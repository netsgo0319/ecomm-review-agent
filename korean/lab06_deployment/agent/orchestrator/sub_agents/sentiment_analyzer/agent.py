import json
import logging

from strands import Agent, tool

# Configure the root strands logger
logging.getLogger("strands").setLevel(logging.INFO)

# Add a handler to see the logs
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s", handlers=[logging.StreamHandler()]
)

SYSTEM_PROMPT = """
    당신은 리뷰 감정 분석 전문가입니다.
    리뷰 텍스트를 분석하여 감정을 분류하고 점수를 매겨주세요.

    <감정분류>
    - positive: 긍정적 감정 (만족, 기쁨, 추천 등)
    - negative: 부정적 감정 (불만, 실망, 비추천 등)
    - neutral: 중립적 감정 (객관적 서술, 단순 정보 등)
    </감정분류>

    <점수범위>
    감정 점수: -1.0 (매우 부정) ~ 1.0 (매우 긍정)
    </점수범위>

    <주의사항>
    - 반어법, 비꼬는 표현('정말 좋네요' + 부정적 맥락)을 주의깊게 감지해주세요
    - 복합 감정이 있는 경우 전체적인 주된 감정을 파악해주세요
    - 한국어 완곡 표현을 고려해주세요: '나쁘지 않다'는 긍정적, '그럭저럭'은 보통 만족
    - 도메인별 전문용어의 맥락을 파악해주세요 (예: 게임의 '어려움'은 긍정적일 수 있음)
    - 비교 표현('~보다 나아요')의 상대적 의미를 고려해주세요
    - 텍스트가 너무 짧거나 모호한 경우 confidence를 낮게 설정해주세요
    </주의사항>

    <출력형식>
    결과를 JSON 형식으로 반환해주세요. 답변에 백틱이나 코드 블록 포맷(```json, ```python 등)을 붙이지 마세요. :
    {
    "sentiment": "positive|negative|neutral",
    "score": 0.8,
    "confidence": 0.9,
    "reason": "분석 근거"
    }
    </출력형식>
"""
# 감정 분석 Agent 생성


@tool
def analyze_sentiment(review_content: str) -> dict:
    """
    리뷰 텍스트의 감정을 분석하는 메인 함수 (Strands Agent 사용)

    Args:
        review_content (str): 분석할 리뷰 텍스트

    Returns:
        dict: 감정 분석 결과
    """
    sentiment_agent = Agent(
        model="us.anthropic.claude-3-5-haiku-20241022-v1:0",
        system_prompt=SYSTEM_PROMPT,
        callback_handler=None,
    )

    # Strands Agent 호출
    result = sentiment_agent(review_content)
    str_result = str(result)

    return {
        "success": True,
        "sentiment_result": json.loads(str_result),
        "raw_response": str_result,
    }
