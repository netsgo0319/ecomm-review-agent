import logging
import os
from datetime import datetime
from string import Template
from typing import Any, Dict, List, Literal, Optional

from PIL.Image import Image as PILImage
from pydantic import BaseModel, Field
from strands import Agent

from .tools import check_image_product_match, check_profanity, check_rating_consistency

# Configure the root strands logger
logging.getLogger("strands").setLevel(logging.INFO)

# Add a handler to see the logs
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s", handlers=[logging.StreamHandler()]
)


# 통합 리뷰 검수 Agent 시스템 프롬프트
UNIFIED_MODERATOR_PROMPT = """
    당신은 이커머스 플랫폼의 리뷰 검수 전문가입니다.

    <주요역할>
    다음의 세가지 카테고리의 검수를 진행하세요.
    - 리뷰 텍스트의 선정적/욕설 표현을 검사해주세요 -> check_profanity
    - 별점과 리뷰 내용의 일치성을 분석해주세요 -> check_rating_consistency
    - 업로드된 이미지와 제품의 관련성을 검증해주세요 (이미지가 있는 경우에만.) -> check_image_product_match
    </주요역할>

    <주의사항>
    - 한국어 감정 표현의 미묘한 차이 인식
    - 전체 맥락을 고려한 종합적 판단
    </주의사항>

    <출력형식>
    모든 검수를 수행한 후, 반드시 다음 JSON 스키마로 응답해주세요. 다른 설명이나 백틱(```json) 등은 절대 포함하지 마세요.:

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
        "overall_status": "PASS|FAIL",
        "failed_checks": ["실패한 검수 항목 리스트"]
    }

    </출력형식>
"""

USER_PROMPT_TEMPLATE = Template(
    """
    다음 리뷰를 종합적으로 검수해주세요:

    리뷰 내용: $review_content
    별점: $rating 점 (1-5점 척도)
    제품: $product
    카테고리: $category
    이미지: $has_image ($image_path)
    """
)


class CheckResult(BaseModel):
    """개별 검사 결과"""

    status: Literal["PASS", "FAIL", "SKIP"] = Field(description="검사 상태")
    reason: str = Field(description="구체적인 판단 근거 (필수)")
    confidence: float = Field(ge=0.0, le=1.0, description="신뢰도 (0.0-1.0)")


class ReviewModerationResult(BaseModel):
    """리뷰 모더레이션 분석 결과"""

    profanity_check: CheckResult = Field(description="욕설/비속어 검사 결과")
    rating_consistency: CheckResult = Field(description="평점-내용 일치성 검사 결과")
    image_match: CheckResult = Field(description="이미지-내용 일치성 검사 결과")
    overall_status: Literal["PASS", "FAIL"] = Field(description="전체 검수 통과 여부")
    failed_checks: List[str] = Field(description="실패한 검사 항목 리스트")


def moderate_review(
    review_content: str,
    rating: int,
    product_data: Dict[str, Any],
    image: Optional[PILImage] = None,
) -> Dict[str, Any]:
    """
    리뷰를 종합적으로 검수하는 메인 함수

    Args:
        review_content (str): 리뷰 내용
        rating (int): 별점 (1-5)
        product_data (Dict[str, Any]): name(제품명), category(카테고리) 등 제품 정보
        image (Optional[PILImage]): 업로드된 이미지 (PIL Image 객체)

    Returns:
        Dict[str, Any]: 검수 결과
    """
    image_path = None
    if image:
        image_path = save_image(image)

    # 통합 검수 Agent 생성
    unified_moderator = Agent(
        model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        tools=[check_profanity, check_rating_consistency, check_image_product_match],
        system_prompt=UNIFIED_MODERATOR_PROMPT,
    )

    # user prompt 생성
    user_prompt = USER_PROMPT_TEMPLATE.substitute(
        review_content=review_content,
        rating=rating,
        product=product_data.get("name", "Unknown"),
        category=product_data.get("category", "알수없음"),
        has_image="있음" if image else "없음",
        image_path=image_path if image_path else "없음",
    )

    # 통합 검수 Agent 실행
    unified_response = unified_moderator(user_prompt)

    # Structured Output
    moderated_result = unified_moderator.structured_output(
        ReviewModerationResult, "모델의 종합적인 리뷰 검수 결과를 구조화합니다."
    )

    return {
        "success": True,
        "moderation_result": moderated_result,
        "raw_response": str(unified_response),
    }


def save_image(
    image: PILImage, images_folder: str = "lab03_review_moderator/images"
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
