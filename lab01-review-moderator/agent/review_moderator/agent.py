from strands import Agent
from .tools import check_profanity, check_image_product_match, check_rating_consistency
import json
from typing import Dict, Any, List, Optional

# 리뷰 검수 에이전트 시스템 프롬프트 (외부화)
REVIEW_MODERATION_PROMPT = """
당신은 전문적인 리뷰 검수 에이전트입니다.

주요 역할:
1. 리뷰 내용의 선정적/욕설 표현 검사
2. 업로드된 이미지와 제품의 관련성 검증 (이미지가 있는 경우에만)
3. 별점과 리뷰 내용의 일치성 분석

검수 원칙:
- 객관적이고 공정한 기준 적용
- 명확한 근거와 함께 판단 결과 제시
- 사용자 경험을 고려한 건설적 피드백 제공
- 이미지가 없는 리뷰는 이미지 검수를 건너뛰고 나머지 2개 항목만 검사
- 이미지가 있는데 검증할 수 없거나 제품과 관련이 없으면 반드시 FAIL로 처리

검수 결과는 반드시 다음 JSON 형태로 제공하세요:
{
    "profanity_check": {"status": "PASS/FAIL", "reason": "이유", "confidence": 0.0-1.0},
    "image_match": {"status": "PASS/FAIL/SKIP", "reason": "이유", "confidence": 0.0-1.0},
    "rating_consistency": {"status": "PASS/FAIL", "reason": "이유", "confidence": 0.0-1.0},
    "overall_status": "PASS/FAIL",
    "failed_checks": ["실패한 검수 항목들"],
    "checks_performed": ["실행된 검수 항목들"],
    "summary": "전체 검수 결과 요약"
}
"""

def moderate_review(
    review_content: str,
    rating: int,
    product_data: Dict[str, Any],
    media_files: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """
    리뷰를 종합적으로 검수하는 메인 함수 (하이브리드 접근법)
    
    Args:
        review_content (str): 리뷰 내용
        rating (int): 별점 (1-5)
        product_data (Dict[str, Any]): 제품 정보
        media_files (Optional[List[Dict]]): 업로드된 미디어 파일들
        
    Returns:
        Dict[str, Any]: 검수 결과
    """
    
    try:
        # 1. 이미지 검수는 직접 호출 (Base64 데이터 보존)
        if media_files and len(media_files) > 0:
            image_result = check_image_product_match(media_files, product_data)
        else:
            image_result = {"status": "SKIP", "reason": "업로드된 이미지가 없습니다.", "confidence": 1.0}
        
        # 2. 텍스트 검수는 Agent 사용 (토큰 절약)
        agent = Agent(
            tools=[check_profanity, check_rating_consistency],
            system_prompt=REVIEW_MODERATION_PROMPT
        )
        
        simplified_prompt = f"""
        다음 리뷰를 검수해주세요:
        
        - 내용: "{review_content}"
        - 별점: {rating}점
        - 제품: {product_data.get('name', 'Unknown')}
        
        1. check_profanity 도구로 선정적/욕설 표현을 검사하세요.
        2. check_rating_consistency 도구로 별점과 내용의 일치성을 분석하세요.
        
        JSON 형태로 결과를 제공하세요.
        """
        
        agent_result = agent(simplified_prompt)
        
        # 3. AgentResult 파싱
        try:
            result_text = str(agent_result)
            
            if "```json" in result_text:
                json_start = result_text.find("```json") + 7
                json_end = result_text.find("```", json_start)
                json_text = result_text[json_start:json_end].strip()
            elif "{" in result_text and "}" in result_text:
                json_start = result_text.find("{")
                json_end = result_text.rfind("}") + 1
                json_text = result_text[json_start:json_end]
            else:
                raise ValueError("JSON을 찾을 수 없습니다")
            
            parsed_data = json.loads(json_text)
            
        except Exception as parse_error:
            # 파싱 실패 시 기본값
            parsed_data = {
                "profanity_check": {"status": "FAIL", "reason": "결과 파싱 실패", "confidence": 0.0},
                "rating_consistency": {"status": "FAIL", "reason": "결과 파싱 실패", "confidence": 0.0}
            }
        
        # 4. 결과 통합
        final_result = {
            "profanity_check": parsed_data.get("profanity_check", {"status": "FAIL", "reason": "검수 실패", "confidence": 0.0}),
            "image_match": image_result,  # 직접 호출 결과
            "rating_consistency": parsed_data.get("rating_consistency", {"status": "FAIL", "reason": "검수 실패", "confidence": 0.0})
        }
        
        # 5. 전체 상태 판정
        failed_checks = []
        checks_performed = ["profanity_check", "rating_consistency"]
        
        if final_result["profanity_check"]["status"] == "FAIL":
            failed_checks.append("profanity_check")
        if final_result["rating_consistency"]["status"] == "FAIL":
            failed_checks.append("rating_consistency")
        
        if image_result["status"] == "FAIL":
            failed_checks.append("image_match")
            checks_performed.append("image_match")
        elif image_result["status"] == "PASS":
            checks_performed.append("image_match")
        
        overall_status = "FAIL" if failed_checks else "PASS"
        
        final_result.update({
            "overall_status": overall_status,
            "failed_checks": failed_checks,
            "checks_performed": checks_performed,
            "summary": f"검수 완료: {len(checks_performed)}개 항목 중 {len(failed_checks)}개 실패"
        })
        
        return {
            "success": True,
            "moderation_result": final_result,  # 파싱된 딕셔너리
            "raw_response": str(agent_result)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "moderation_result": {
                "profanity_check": {"status": "FAIL", "reason": "시스템 오류", "confidence": 0.0},
                "image_match": {"status": "SKIP", "reason": "시스템 오류", "confidence": 0.0},
                "rating_consistency": {"status": "FAIL", "reason": "시스템 오류", "confidence": 0.0},
                "overall_status": "FAIL",
                "failed_checks": ["system_error"],
                "checks_performed": [],
                "summary": f"시스템 오류로 인해 검수를 완료할 수 없습니다: {str(e)}"
            }
        }

def generate_error_messages(moderation_result: Dict[str, Any]) -> List[str]:
    """
    검수 실패 시 사용자에게 표시할 에러 메시지를 생성합니다.
    
    Args:
        moderation_result (Dict[str, Any]): 검수 결과
        
    Returns:
        List[str]: 에러 메시지 목록
    """
    messages = []
    failed_checks = moderation_result.get("failed_checks", [])
    
    if "profanity_check" in failed_checks:
        reason = moderation_result.get("profanity_check", {}).get("reason", "부적절한 언어가 포함되어 있습니다.")
        messages.append(f"언어 검수 실패: {reason}")
    
    if "image_match" in failed_checks:
        reason = moderation_result.get("image_match", {}).get("reason", "업로드된 이미지가 제품과 관련이 없습니다.")
        messages.append(f"이미지 검수 실패: {reason}")
    
    if "rating_consistency" in failed_checks:
        reason = moderation_result.get("rating_consistency", {}).get("reason", "별점과 리뷰 내용이 일치하지 않습니다.")
        messages.append(f"별점 일치성 검수 실패: {reason}")
    
    if "system_error" in failed_checks:
        messages.append("시스템 오류로 인해 검수를 완료할 수 없습니다. 잠시 후 다시 시도해주세요.")
    
    return messages
