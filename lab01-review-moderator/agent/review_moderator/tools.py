from strands import tool
import re
import json
import threading
import time
from typing import Dict, List, Any, Optional

# 스레드 안전한 컨텍스트 관리
class ImageContextManager:
    def __init__(self):
        self._contexts = {}
        self._lock = threading.Lock()
        self._cleanup_interval = 300  # 5분 후 자동 정리

    def set_context(self, session_id: str, media_files: List[Dict], product_data: Dict) -> None:
        """세션별 이미지 컨텍스트 설정"""
        with self._lock:
            self._contexts[session_id] = {
                'media_files': media_files,
                'product_data': product_data,
                'timestamp': time.time()
            }
            # 오래된 컨텍스트 정리
            self._cleanup_old_contexts()

    def get_context(self, session_id: str) -> Dict:
        """세션별 이미지 컨텍스트 조회"""
        with self._lock:
            return self._contexts.get(session_id, {})

    def clear_context(self, session_id: str) -> None:
        """특정 세션 컨텍스트 삭제"""
        with self._lock:
            self._contexts.pop(session_id, None)

    def _cleanup_old_contexts(self) -> None:
        """5분 이상 된 컨텍스트 자동 정리"""
        current_time = time.time()
        expired_sessions = [
            session_id for session_id, context in self._contexts.items()
            if current_time - context['timestamp'] > self._cleanup_interval
        ]
        for session_id in expired_sessions:
            del self._contexts[session_id]

# 전역 컨텍스트 매니저 인스턴스
_context_manager = ImageContextManager()

@tool
def check_profanity(content: str) -> Dict[str, Any]:
    """
    Amazon Bedrock Claude API 사용하여 리뷰 내용의 선정적/욕설 표현을 검수합니다.
    
    Args:
        content (str): 검사할 리뷰 내용
        
    Returns:
        Dict[str, Any]: 검사 결과
    """
    try:
        import boto3
        import json
        
        # Bedrock 클라이언트 초기화 (Claude 3.5 사용)
        bedrock = boto3.client('bedrock-runtime', region_name='us-west-2')
        
        # Claude에게 보낼 프롬프트
        prompt = f"""
다음 리뷰 내용이 부적절한 표현을 포함하고 있는지 검수해주세요:

리뷰 내용: "{content}"

검수 기준:
1. 욕설, 비속어, 공격적 언어
2. 성적, 선정적 표현
3. 혐오 발언, 차별적 표현
4. 위협적, 폭력적 표현
5. 스팸성, 광고성 내용

한국어의 미묘한 뉘앙스와 맥락을 고려하여 판단해주세요.

응답은 다음 JSON 형식으로만 제공해주세요:
{{
  "is_appropriate": true/false,
  "confidence": 0.0-1.0,
  "detected_issues": ["감지된 문제점들"],
  "severity": "low/medium/high",
  "reason": "판단 근거"
}}
"""
        
        # Bedrock API 호출 (Claude 3.5 Sonnet)
        response = bedrock.invoke_model(
            modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
        )
        
        # 응답 파싱
        response_body = json.loads(response['body'].read())
        claude_response = response_body['content'][0]['text']
        
        # JSON 응답 파싱
        try:
            if "```json" in claude_response:
                json_start = claude_response.find("```json") + 7
                json_end = claude_response.find("```", json_start)
                json_text = claude_response[json_start:json_end].strip()
            elif "{" in claude_response and "}" in claude_response:
                json_start = claude_response.find("{")
                json_end = claude_response.rfind("}") + 1
                json_text = claude_response[json_start:json_end]
            else:
                raise ValueError("JSON 형태를 찾을 수 없습니다.")
            
            moderation_result = json.loads(json_text)
            
            # 결과 반환
            if moderation_result.get("is_appropriate", True):
                return {
                    "status": "PASS",
                    "reason": moderation_result.get("reason", "적절한 표현입니다."),
                    "confidence": moderation_result.get("confidence", 0.9),
                    "severity": moderation_result.get("severity", "none")
                }
            else:
                return {
                    "status": "FAIL",
                    "reason": moderation_result.get("reason", "부적절한 표현이 감지되었습니다."),
                    "detected_issues": moderation_result.get("detected_issues", []),
                    "severity": moderation_result.get("severity", "medium"),
                    "confidence": moderation_result.get("confidence", 0.9)
                }
                
        except (json.JSONDecodeError, ValueError) as e:
            return {
                "status": "FAIL",
                "reason": f"Claude 응답 파싱 실패: {str(e)}",
                "confidence": 0.0
            }
            
    except Exception as e:
        return {
            "status": "FAIL",
            "reason": f"API 호출 실패: {str(e)}",
            "confidence": 0.0
        }

@tool
def check_image_product_match(media_files: List[Dict], product_data: Dict) -> Dict[str, Any]:
    """
    Claude Vision API를 사용하여 업로드된 이미지와 제품의 관련성을 검증합니다.
    
    Args:
        media_files (List[Dict]): 업로드된 미디어 파일 정보
        product_data (Dict): 제품 정보
        
    Returns:
        Dict[str, Any]: 매칭 검사 결과
    """
    if not media_files or len(media_files) == 0:
        return {
            "status": "SKIP",
            "reason": "업로드된 이미지가 없습니다.",
            "confidence": 1.0
        }
    
    try:
        import boto3
        import base64
        import os
        from pathlib import Path
        
        # Bedrock 클라이언트 초기화
        bedrock = boto3.client('bedrock-runtime', region_name='us-west-2')
        
        product_name = product_data.get("name", "")
        product_category = product_data.get("category", "")
        
        # 첫 번째 이미지만 검사 (여러 이미지가 있을 경우)
        first_media = media_files[0]
        
        # 이미지 데이터 추출
        image_url = first_media.get("url", "")
        
        if image_url.startswith("data:image/"):
            # Streamlit에서 전달된 base64 데이터 처리
            try:
                # data:image/jpeg;base64,{base64_data} 형식에서 base64 부분만 추출
                image_data = image_url.split(",")[1]
            except IndexError:
                return {
                    "status": "FAIL",
                    "reason": "잘못된 base64 이미지 데이터 형식입니다.",
                    "confidence": 0.0
                }
        elif image_url.startswith("/uploads/media/"):
            # 파일 시스템 경로 처리 (기존 로직 유지)
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent.parent
            image_path = project_root / "backend" / "uploads" / "media" / image_url.split("/")[-1]
            
            if not image_path.exists():
                return {
                    "status": "FAIL",
                    "reason": f"이미지 파일이 존재하지 않습니다: {image_path}",
                    "confidence": 0.0
                }
            
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
        else:
            return {
                "status": "FAIL",
                "reason": f"지원하지 않는 이미지 URL 형식입니다: {image_url}",
                "confidence": 0.0
            }
        
        # Claude Vision API 호출
        prompt = f"""
이 이미지가 다음 제품과 관련이 있는지 분석해주세요:

제품명: {product_name}
카테고리: {product_category}

다음 기준으로 판단해주세요:
1. 이미지에 해당 제품이나 관련 제품이 보이는가?
2. 이미지가 제품 카테고리와 일치하는가?
3. 이미지가 제품 리뷰용으로 적절한가?

응답은 다음 JSON 형식으로만 제공해주세요:
{{
  "is_related": true/false,
  "confidence": 0.0-1.0,
  "reason": "판단 근거",
  "detected_objects": ["이미지에서 감지된 주요 객체들"]
}}
"""
        
        # Bedrock API 호출 (Claude 3.5 Sonnet v2)
        response = bedrock.invoke_model(
            modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": image_data
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            })
        )
        
        # 응답 파싱
        response_body = json.loads(response['body'].read())
        claude_response = response_body['content'][0]['text']
        
        # JSON 응답 파싱
        try:
            if "```json" in claude_response:
                json_start = claude_response.find("```json") + 7
                json_end = claude_response.find("```", json_start)
                json_text = claude_response[json_start:json_end].strip()
            elif "{" in claude_response and "}" in claude_response:
                json_start = claude_response.find("{")
                json_end = claude_response.rfind("}") + 1
                json_text = claude_response[json_start:json_end]
            else:
                raise ValueError("JSON 형태를 찾을 수 없습니다.")
            
            vision_result = json.loads(json_text)
            
            # 결과 반환
            if vision_result.get("is_related", False):
                return {
                    "status": "PASS",
                    "reason": vision_result.get("reason", "이미지가 제품과 관련이 있습니다."),
                    "confidence": vision_result.get("confidence", 0.8),
                    "detected_objects": vision_result.get("detected_objects", []),
                    "image_count": len(media_files),
                    "product_category": product_category
                }
            else:
                return {
                    "status": "FAIL",
                    "reason": vision_result.get("reason", "이미지가 제품과 관련이 없습니다."),
                    "confidence": vision_result.get("confidence", 0.8),
                    "detected_objects": vision_result.get("detected_objects", []),
                    "image_count": len(media_files),
                    "product_category": product_category
                }
                
        except (json.JSONDecodeError, ValueError) as e:
            return {
                "status": "FAIL",
                "reason": f"Claude Vision 응답 파싱 실패: {str(e)}",
                "confidence": 0.0
            }
            
    except Exception as e:
        return {
            "status": "FAIL",
            "reason": f"Vision API 호출 실패: {str(e)}",
            "confidence": 0.0
        }

@tool
def check_rating_consistency(rating: int, content: str) -> Dict[str, Any]:
    """
    Claude LLM을 사용하여 별점과 리뷰 내용의 일치성을 분석합니다.
    
    Args:
        rating (int): 별점 (1-5)
        content (str): 리뷰 내용
        
    Returns:
        Dict[str, Any]: 일치성 검사 결과
    """
    try:
        import boto3
        import json
        
        # Bedrock 클라이언트 초기화
        bedrock = boto3.client('bedrock-runtime', region_name='us-west-2')
        
        # Claude에게 보낼 프롬프트
        prompt = f"""
다음 리뷰의 별점과 내용이 일치하는지 분석해주세요:

별점: {rating}점 (1-5점 척도)
리뷰 내용: "{content}"

다음 기준으로 판단해주세요:
1. 리뷰 내용의 전반적인 감정 (긍정/부정/중립)
2. 별점과 감정의 일치성
3. 반어법, 아이러니, 복합 감정 고려
4. 한국어 맥락과 뉘앙스 이해

판단 기준:
- 별점 4-5점: 긍정적 내용 기대
- 별점 1-2점: 부정적 내용 기대  
- 별점 3점: 중립적 내용 기대

응답은 다음 JSON 형식으로만 제공해주세요:
{{
  "content_sentiment": "positive/negative/neutral",
  "sentiment_confidence": 0.0-1.0,
  "is_consistent": true/false,
  "reason": "판단 근거",
  "detected_emotions": ["감지된 감정이나 표현들"]
}}
"""
        
        # Bedrock API 호출 (Claude 3.5 Sonnet)
        response = bedrock.invoke_model(
            modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
        )
        
        # 응답 파싱
        response_body = json.loads(response['body'].read())
        claude_response = response_body['content'][0]['text']
        
        # JSON 응답 파싱
        try:
            if "```json" in claude_response:
                json_start = claude_response.find("```json") + 7
                json_end = claude_response.find("```", json_start)
                json_text = claude_response[json_start:json_end].strip()
            elif "{" in claude_response and "}" in claude_response:
                json_start = claude_response.find("{")
                json_end = claude_response.rfind("}") + 1
                json_text = claude_response[json_start:json_end]
            else:
                raise ValueError("JSON 형태를 찾을 수 없습니다.")
            
            sentiment_result = json.loads(json_text)
            
            # 결과 반환
            status = "PASS" if sentiment_result.get("is_consistent", True) else "FAIL"
            reason = sentiment_result.get("reason", "별점과 리뷰 내용이 일치합니다.")
            
            return {
                "status": status,
                "reason": reason,
                "rating": rating,
                "content_sentiment": sentiment_result.get("content_sentiment", "neutral"),
                "sentiment_confidence": sentiment_result.get("sentiment_confidence", 0.8),
                "detected_emotions": sentiment_result.get("detected_emotions", []),
                "confidence": sentiment_result.get("sentiment_confidence", 0.8)
            }
            
        except (json.JSONDecodeError, ValueError) as e:
            return {
                "status": "FAIL",
                "reason": f"감정 분석 응답 파싱 실패: {str(e)}",
                "rating": rating,
                "confidence": 0.0
            }
            
    except Exception as e:
        return {
            "status": "FAIL",
            "reason": f"API 호출 실패: {str(e)}",
            "rating": rating,
            "confidence": 0.0
        }

def set_image_context(media_files: List[Dict], product_data: Dict, session_id: str = "default") -> None:
    """
    이미지 컨텍스트를 세션별로 안전하게 저장합니다.

    Args:
        media_files (List[Dict]): 업로드된 미디어 파일 정보
        product_data (Dict): 제품 정보
        session_id (str): 세션 식별자 (기본값: "default")
    """
    _context_manager.set_context(session_id, media_files, product_data)

@tool
def check_image_with_context(session_id: str = "default") -> str:
    """
    컨텍스트에 저장된 이미지를 검수합니다.

    Args:
        session_id (str): 세션 식별자 (기본값: "default")

    Returns:
        str: JSON 형태의 검수 결과
    """
    context = _context_manager.get_context(session_id)

    if not context.get('media_files'):
        return json.dumps({
            "status": "SKIP",
            "reason": "설정된 이미지가 없습니다.",
            "confidence": 1.0
        })

    # 기존 check_image_product_match 로직 재사용
    result = check_image_product_match(
        context['media_files'],
        context['product_data']
    )

    # Agent가 이해할 수 있는 JSON 문자열로 반환
    return json.dumps(result)


