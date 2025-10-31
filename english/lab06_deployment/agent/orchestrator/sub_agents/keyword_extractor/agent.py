import json
import logging
from dataclasses import dataclass
from string import Template
from typing import List, Literal

from pydantic import BaseModel, Field
from strands import Agent, tool
from strands_tools import file_read

# Configure the root strands logger
logging.getLogger("strands").setLevel(logging.INFO)

# Add a handler to see the logs
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s", handlers=[logging.StreamHandler()]
)


SYSTEM_PROMPT = """
당신은 키워드 기반 리뷰 분석 전문가입니다.

<핵심작업>
- 리뷰 텍스트에서 한국어 특성과 문맥을 고려해 키워드와 관련된 문장을 정확하게 추출해주세요
- 등록된 키워드와의 정밀한 매칭을 수행해주세요
</핵심작업>

<작업프로세스>
1. 등록된 키워드 조회: file_read 도구를 사용하여 "registered_keywords.txt" 파일을 읽고 등록된 키워드 목록을 획득해주세요
2. 리뷰 텍스트 분석: 등록된 키워드를 참고하여 리뷰에서 관련 키워드와 구문을 식별해주세요
3. 매칭 수행:
   - 완전 일치를 우선해주세요
   - 부분 일치 및 유사어를 고려해주세요
   - 의미론적 유사어를 고려해주세요
</작업프로세스>

<출력형식>
결과에 다음값을 포함해주세요. :
{
  "matched_keywords": [
        {
            "keyword": "매칭된 키워드",
            "match_type": "exact|partial|semantic",
            "original_phrase": "리뷰에서 발견된 원본 구문 (리뷰 텍스트에서 그대로 추출한 문장 또는 구문)"
        }
    ]
}

주의: original_phrase는 반드시 리뷰 원문에 포함된 정확한 텍스트여야 합니다.
</출력형식>

<주의사항>
- 한국어 특성 (조사, 어미 변화)을 고려하여 매칭해주세요
- 부정문에서 사용된 키워드도 포함하되 구분하여 처리해주세요
- 중복 키워드는 제거하고 최적의 매칭만 유지해주세요
</주의사항>
"""

KEYWORD_EXTRACTOR_PROMPT_TEMPLATE = Template(
    """
아래 리뷰에서 등록된 키워드와 매칭되는 내용을 찾아주세요.
<리뷰>
    $review_text
</리뷰>
"""
)


class KeywordHighlight(BaseModel):
    """키워드별 매칭되는 문장리스트 데이터셋"""

    keyword: str = Field(description="기준 키워드")
    match_type: Literal["exact", "partial", "semantic"]
    original_phrase: str = Field(description="리뷰에서 발견된 원본 구문")


class KeywordAnalysisResult(BaseModel):
    """키워드 분석 결과를 담는 클래스"""

    matched_keywords: List[KeywordHighlight]


@tool
def search_keywords(review_text: str) -> dict:
    """
    리뷰에서 키워드에 매칭되는 문장을 검색하는 함수

    Args:
        review_text (str): 리뷰 텍스트

    Returns:
        dict: 키워드 분석 결과
    """

    logging.info(f"search_keywords called with review_text: {review_text}")

    # 키워드 매칭 Agent
    keyword_agent = Agent(
        model="us.anthropic.claude-3-sonnet-20240229-v1:0",
        tools=[file_read],
        callback_handler=None,
        system_prompt=SYSTEM_PROMPT,
    )

    # Agent 실행
    prompt = KEYWORD_EXTRACTOR_PROMPT_TEMPLATE.substitute(review_text=review_text)
    agent_response = keyword_agent(prompt)
    str_response = str(agent_response)

    # Structured output 으로 출력
    result = keyword_agent.structured_output(
        KeywordAnalysisResult, "키워드 분석 결과를 구조화된 형태로 추출하시오"
    )

    return {
        "success": True,
        "analysis_result": (
            result.model_dump() if hasattr(result, "model_dump") else result.__dict__
        ),
        "raw_response": str_response,
    }
