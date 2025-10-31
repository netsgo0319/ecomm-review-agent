import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from PIL.Image import Image as PILImage
from pydantic import BaseModel, Field
from strands import Agent

from .sub_agents.auto_responser.agent import generate_auto_response
from .sub_agents.keyword_extractor.agent import search_keywords
from .sub_agents.review_moderator.agent import moderate_review
from .sub_agents.sentiment_analyzer.agent import analyze_sentiment

# Configure the root strands logger
logging.getLogger("strands").setLevel(logging.INFO)

# Add a handler to see the logs
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s", handlers=[logging.StreamHandler()]
)

ORCHESTRATOR_PROMPT = """
당신은 리뷰 분석 워크플로우를 관리하는 오케스트레이터입니다.
사용자가 입력하는 리뷰 데이터를 기반으로 다음 agent와 순서를 참고하여 리뷰를 검수하고 분석한 후 자동답글을 생성해주세요.

<분석용에이전트들>
활용해야 하는 리뷰 분석 Agent (순서대로 실행):
1. 리뷰 검수 (이미지와 제품 정보 연관 검사, 별점과 코멘트의 일관성 검사, 욕설/선정성 검사를 포함함)
2. 키워드에 맞는 문장 분석
3. 감정 분석
4. 자동 응답 생성 (분석된 감정에 맞게)
</분석용에이전트들>

<작업순서>
1. 리뷰 검수 후 욕설/선정성 검수에서 탈락할 경우 이후 단계를 진행하지 않고 종료해주세요. 종료 시 부적격 사유를 응답해주세요. (이미지 검수나 별점코멘트 일관성 검수 등 다른 리뷰 검수 항목은 실패하더라도 다음 단계 진행 가능) 
2. 리뷰 검수에서 정상적으로 통과할 경우, 감정 분석과 키워드 추출을 순서대로 진행하고 리뷰를 분석해주세요.
3. 마지막으로 자동응답을 생성해주세요
</작업순서>

"""


class KeywordHighlight(BaseModel):
    keyword: str = Field(description="기준 키워드")
    match_type: str = Field(description="매칭 타입: exact, partial, semantic")
    original_phrase: str = Field(description="리뷰에서 발견된 원본 구문")


class ReviewAnalysis(BaseModel):
    """Complete review analysis."""

    moderation_result: Dict[str, Any] = Field(description="리뷰 검수 결과")
    keyword_highlighted_list: List[KeywordHighlight] = Field(
        description="키워드 분석에서 키워드에 맞는 문장들"
    )
    sentiment: str = Field(description="감정 분석 결과")
    auto_response: str = Field(description="자동 응답 생성 결과")


def comprehensive_analyzer(
    product_data: Dict[str, Any],
    review_data: Dict[str, Any],
    image: Optional[PILImage] = None,
) -> Dict[str, Any]:
    """
    리뷰에 대한 자동 응답을 생성하는 메인 함수

    Args:
        review_data Dict[str, Any]: 분석할 리뷰 데이터
        image (Optional[PILImage]): 업로드된 이미지 (PIL Image 객체)

    Returns:
        Dict[str, Any]: 종합 분석 결과
    """

    image_path = None
    if image:
        image_path = save_image(image)

    # 각 요청마다 새로운 Agent 생성
    orchestrator_agent = Agent(
        model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        tools=[
            moderate_review,
            search_keywords,
            analyze_sentiment,
            generate_auto_response,
        ],
        system_prompt=ORCHESTRATOR_PROMPT,
    )

    # 리뷰 종합 분석 결과 응답
    orchestrator_agent(
        f"""
    <product_data>{product_data}</product_data>
    <review_data>{review_data}</review_data>
    <image_path>{image_path if image_path else '없음'}</image_path>
    """
    )

    result = orchestrator_agent.structured_output(
        ReviewAnalysis, "리뷰데이터에 대한 분석 결과를 구조화된 형태로 추출하시오"
    )

    # Pydantic 모델을 dict로 변환
    if hasattr(result, "model_dump"):
        result_dict = result.model_dump()
    elif hasattr(result, "dict"):
        result_dict = result.dict()
    else:
        result_dict = result

    return result_dict


def save_image(
    image: PILImage, images_folder: str = "lab05_orchestrator/images"
) -> str:
    """
    이미지를 images 폴더에 저장하고 경로를 반환합니다.

    Args:
        image (PILImage): 저장할 PIL Image 객체
        images_folder (str): 저장할 폴더 경로 (기본값: "images")

    Returns:
        str: 저장된 이미지의 경로
    """
    os.makedirs(images_folder, exist_ok=True)

    image_format = image.format if image.format else "PNG"
    extension = image_format.lower()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"review_image_{timestamp}.{extension}"
    filepath = os.path.join(images_folder, filename)

    image.save(filepath, format=image_format)

    return filepath
