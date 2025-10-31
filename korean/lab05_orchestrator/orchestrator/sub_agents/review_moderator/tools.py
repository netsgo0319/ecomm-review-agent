import json
import os
import re
import threading
import time
from typing import Any, Dict, List, Optional

import logging
from strands import Agent, tool
from strands_tools import image_reader

# Configure the root strands logger
logging.getLogger("strands").setLevel(logging.INFO)

# Add a handler to see the logs
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s", handlers=[logging.StreamHandler()]
)

PROFANITY_PROMPT = """
    리뷰 내용이 부적절한 표현을 포함하고 있는지 검수해주세요:

    검수 기준:
    1. 욕설, 비속어, 공격적 언어
    2. 성적, 선정적 표현
    3. 혐오 발언, 차별적 표현
    4. 위협적, 폭력적 표현
    5. 스팸성, 광고성 내용

    한국어의 미묘한 뉘앙스와 맥락을 고려하여 판단해주세요.

    응답은 반드시 다음 JSON 형식으로만 제공해주세요. 답변에 백틱이나 코드 블록 포맷(```json, ```python 등)을 붙이지 마세요. :
    ```
    {
        "is_appropriate": true/false,
        "confidence": 0.0-1.0,
        "detected_issues": ["감지된 문제점들"],
        "severity": "low/medium/high",
        "reason": "판단 근거"
    }
    """

IMAGE_MATCH_PROMPT = """
    이미지가 제품과 관련이 있는지 분석해주세요:

    다음 기준으로 판단해주세요:
    1. 이미지에 해당 제품이나 관련 제품이 보이는가?
    2. 이미지가 제품 카테고리와 일치하는가?
    3. 이미지가 제품 리뷰용으로 적절한가?

    응답은 다음 JSON 형식으로만 제공해주세요. 답변에 백틱이나 코드 블록 포맷(```json, ```python 등)을 붙이지 마세요. :
    {
        "is_related": true/false,
        "confidence": 0.0-1.0,
        "reason": "판단 근거",
        "detected_objects": ["이미지에서 감지된 주요 객체들"]
    }
    """

RATING_CONSISTENCY_PROMPT = """
    리뷰의 별점과 내용이 일치하는지 분석해주세요:

    다음 기준들을 참고하여 판단해주세요:
    1. 리뷰 내용의 전반적인 감정 (긍정/부정/중립)
    2. 별점과 감정의 일치성
    3. 반어법, 아이러니, 복합 감정 고려
    4. 한국어 맥락과 뉘앙스 이해

    판단 기준:
    - 별점 4-5점: 긍정적 내용 기대
    - 별점 1-2점: 부정적 내용 기대  
    - 별점 3점: 중립적 내용 기대

    응답은 다음 JSON 형식으로만 제공해주세요. 답변에 백틱이나 코드 블록 포맷(```json, ```python 등)을 붙이지 마세요. :
    {
        "content_sentiment": "positive/negative/neutral",
        "sentiment_confidence": 0.0-1.0,
        "is_consistent": true/false,
        "reason": "판단 근거",
        "detected_emotions": ["감지된 감정이나 표현들"]
    }
"""


@tool
def check_profanity(content: str) -> Any:
    """
    리뷰 내용의 선정적/욕설 표현을 검수합니다.

    Args:
        content (str): 검사할 리뷰 내용

    Returns:
        Any: 검사 결과
    """
    profanity_agent = Agent(
        model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        system_prompt=PROFANITY_PROMPT,
        callback_handler=None,
    )
    return profanity_agent(
        f"다음 리뷰 내용의 선정적/욕설 표현을 검수하세요. <review_content>{content}</review_content>"
    )


@tool
def check_image_product_match(image_path: str, product_data: Dict) -> Any:
    """
    리뷰에 업로드된 이미지와 실제 제품의 관련성을 검증합니다.

    Args:
        media_files (List[Dict]): 업로드된 미디어 파일 정보
        product_data (Dict): 제품 정보

    Returns:
        Any: 매칭 검사 결과
    """
    try:
        if not image_path or not os.path.exists(image_path):
            return {
                "status": "SKIP",
                "reason": "업로드된 이미지가 없습니다.",
                "confidence": 1.0,
            }
        image_match_agent = Agent(
            model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
            system_prompt=IMAGE_MATCH_PROMPT,
            tools=[image_reader],
            callback_handler=None,
        )

        return image_match_agent(
            f"다음 이미지와 제품정보를 기반으로 상호관련 여부를 체크해주세요. <image_path>{image_path}</image_path> <product_data>{product_data}</product_data>"
        )
    except Exception as e:
        return {"status": "ERROR", "reason": str(e), "confidence": 1.0}


@tool
def check_rating_consistency(rating: int, content: str) -> Any:
    """
    별점과 리뷰 내용의 일치성을 분석합니다.

    Args:
        rating (int): 별점 (1-5)
        content (str): 리뷰 내용

    Returns:
        Dict[str, Any]: 일치성 검사 결과
    """
    rating_consistency_agent = Agent(
        model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        callback_handler=None,
        system_prompt=RATING_CONSISTENCY_PROMPT,
    )
    return rating_consistency_agent(
        f"다음 별점과 리뷰 내용의 일치성을 분석해주세요. <rating>{rating}</rating> <review_content>{content}</review_content>"
    )
