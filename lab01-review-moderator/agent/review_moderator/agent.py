from strands import Agent, tool
from .tools import (
    check_profanity, check_image_product_match, check_rating_consistency,
    set_image_context, check_image_with_context
)
import json
import re
from typing import Dict, Any, List, Optional

# 통합 리뷰 검수 Agent 시스템 프롬프트
UNIFIED_MODERATOR_PROMPT = """
당신은 이컴머스 리뷰 검수 전문가입니다.

주요 역할:
1. 리뷰 텍스트의 선정적/욕설 표현 검사
2. 별점과 리뷰 내용의 일치성 분석
3. 업로드된 이미지와 제품의 관련성 검증 (있는 경우)

한국어 전문 가이드라인:
- 긍정 표현: '만만세', '최고', '대박', '감동', '완벽' = 4-5점 기대
- 보통 표현: '괜찮다', '나쁘지않음', '평범' = 3점 정도
- 부정 표현: '실망', '아쉬움', '별로' = 1-2점 기대
- 아이러니/비꼬기: '최고다(사실은 별로)' 같은 상반된 표현 주의

이미지 검수 기준:
- 이미지가 제품과 직접적 관련이 있는가?
- 카테고리와 일치하는가? (예: 전자기기 제품에 꽃 사진 = 부적절)
- 제품의 특징이나 사용 모습을 보여주는가?

오류 방지:
- 단순 키워드보다 전체 맥락 고려
- 확신이 없을 때는 confidence를 낮게 설정
- 모호한 경우 SKIP 사용 고려

사용 가능한 도구:
- check_profanity: 욕설/선정성 검사
- check_rating_consistency: 별점 일치성 검사
- check_image_with_context: 이미지 검수 (이미지가 있는 경우만)

모든 검수를 수행한 후, 반드시 다음 JSON 스키마로 응답해주세요:

```json
{
    "profanity_check": {
        "status": "PASS|FAIL|SKIP",
        "reason": "구체적인 판단 근거 (필수)",
        "confidence": 0.0-1.0
    },
    "rating_consistency": {
        "status": "PASS|FAIL|SKIP",
        "reason": "구체적인 판단 근거 (필수)",
        "confidence": 0.0-1.0
    },
    "image_match": {
        "status": "PASS|FAIL|SKIP",
        "reason": "구체적인 판단 근거 (필수)",
        "confidence": 0.0-1.0
    },
    "analysis_summary": "전문가 종합 분석 요약"
}
```
"""

@tool
def moderate_review(
    review_content: str,
    rating: int,
    product_data: Dict[str, Any],
    media_files: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """
    리뷰를 종합적으로 검수하는 메인 함수

    Args:
        review_content (str): 리뷰 내용
        rating (int): 별점 (1-5)
        product_data (Dict[str, Any]): 제품 정보
        media_files (Optional[List[Dict]]): 업로드된 미디어 파일들

    Returns:
        Dict[str, Any]: 검수 결과
    """

    try:
        # 이미지가 있는 경우 컨텍스트 설정
        if media_files and len(media_files) > 0:
            set_image_context(media_files, product_data)
            available_tools = [check_profanity, check_rating_consistency, check_image_with_context]
        else:
            available_tools = [check_profanity, check_rating_consistency]

        # 통합 검수 Agent 생성
        unified_moderator = Agent(
            tools=available_tools,
            system_prompt=UNIFIED_MODERATOR_PROMPT
        )

        # 통합 검수 프롬프트 생성
        unified_prompt = f"""
        다음 리뷰를 종합적으로 검수해주세요:

        리뷰 내용: "{review_content}"
        별점: {rating}점 (1-5점 척도)
        제품: {product_data.get('name', 'Unknown')} ({product_data.get('category', '알수없음')})
        이미지: {len(media_files) if media_files else 0}개

        필수 검수 항목:
        1. check_profanity 도구로 선정적/욕설 표현 검사
        2. check_rating_consistency 도구로 별점 일치성 검사
        {"3. check_image_with_context 도구로 이미지 검사" if media_files and len(media_files) > 0 else "3. 이미지 없음 - image_match: SKIP 처리"}

        전문가 기준:
        - 한국어 감정 표현의 미묘한 차이 인식
        - 전체 맥락을 고려한 종합적 판단
        - 모든 검수 완료 후 JSON 형태로 결과 제시
        """

        # 통합 Agent 실행
        unified_response = unified_moderator(unified_prompt)

        # JSON 응답에서 결과 추출
        unified_result = parse_unified_agent_response(unified_response)

        # 결과 형태 변환
        moderation_result = format_moderation_result(unified_result)

        return {
            "success": True,
            "moderation_result": moderation_result,
            "raw_response": str(unified_response),
            "specialist_details": {
                "unified_moderator": unified_response
            }
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

def parse_unified_agent_response(agent_response) -> Dict[str, Any]:
    """
    통합 Agent 응답에서 JSON을 추출합니다.

    Args:
        agent_response: 통합 Agent의 응답

    Returns:
        Dict[str, Any]: 파싱된 전체 결과
    """
    try:
        response_text = str(agent_response)

        # JSON 블록 추출 시도
        json_patterns = [
            r'```json\s*({.*?})\s*```',
            r'```\s*({.*?})\s*```',
            r'({\s*"[^"]+"\s*:[^}]+})',
            r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})'
        ]

        for pattern in json_patterns:
            matches = re.findall(pattern, response_text, re.DOTALL)
            for match in matches:
                try:
                    data = json.loads(match)

                    # 필수 필드 확인
                    if all(key in data for key in ['profanity_check', 'rating_consistency', 'image_match']):
                        return data

                except json.JSONDecodeError:
                    continue

        # JSON 추출 실패 시 기본값 반환
        return {
            "profanity_check": {"status": "PASS", "reason": "JSON 파싱 실패 - 기본 통과", "confidence": 0.7},
            "rating_consistency": {"status": "PASS", "reason": "JSON 파싱 실패 - 기본 통과", "confidence": 0.7},
            "image_match": {"status": "SKIP", "reason": "JSON 파싱 실패 - 기본 SKIP", "confidence": 0.7},
            "analysis_summary": "JSON 파싱 오류로 인한 기본 처리"
        }

    except Exception as e:
        # 예외 시 기본값 반환
        return {
            "profanity_check": {"status": "PASS", "reason": f"기본 통과 처리: {str(e)}", "confidence": 0.7},
            "rating_consistency": {"status": "PASS", "reason": f"기본 통과 처리: {str(e)}", "confidence": 0.7},
            "image_match": {"status": "SKIP", "reason": f"기본 SKIP 처리: {str(e)}", "confidence": 0.7},
            "analysis_summary": f"예외 발생: {str(e)}"
        }

def format_moderation_result(unified_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    통합 Agent 결과를 기존 형태로 변환합니다.

    Args:
        unified_result (Dict[str, Any]): 통합 Agent 결과

    Returns:
        Dict[str, Any]: 기존 형태의 검수 결과
    """
    # 실패한 검수 항목 수집
    failed_checks = []
    checks_performed = []

    # 욕설 검사 결과
    profanity_check = unified_result.get("profanity_check", {"status": "PASS", "reason": "검수 완료", "confidence": 0.8})
    if profanity_check["status"] != "SKIP":
        checks_performed.append("profanity_check")
        if profanity_check["status"] == "FAIL":
            failed_checks.append("profanity_check")

    # 별점 일치성 검사 결과
    rating_consistency = unified_result.get("rating_consistency", {"status": "PASS", "reason": "검수 완룼", "confidence": 0.8})
    if rating_consistency["status"] != "SKIP":
        checks_performed.append("rating_consistency")
        if rating_consistency["status"] == "FAIL":
            failed_checks.append("rating_consistency")

    # 이미지 검사 결과
    image_match = unified_result.get("image_match", {"status": "SKIP", "reason": "이미지 없음", "confidence": 1.0})
    if image_match["status"] != "SKIP":
        checks_performed.append("image_match")
        if image_match["status"] == "FAIL":
            failed_checks.append("image_match")

    # 전체 판정
    overall_status = "FAIL" if failed_checks else "PASS"

    # 요약 메시지 생성
    if failed_checks:
        summary = f"통합 전문가 검수 완료: {len(failed_checks)}개 항목 실패 ({', '.join(failed_checks)})"
    else:
        summary = f"통합 전문가 검수 완료: 모든 항목 통과"

    return {
        "profanity_check": profanity_check,
        "image_match": image_match,
        "rating_consistency": rating_consistency,
        "overall_status": overall_status,
        "failed_checks": failed_checks,
        "checks_performed": checks_performed,
        "summary": summary
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
