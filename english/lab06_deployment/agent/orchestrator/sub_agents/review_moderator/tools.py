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
    Please moderate whether the review content contains inappropriate expressions:

    Moderation Criteria:
    1. Profanity, obscenity, aggressive language
    2. Sexual, explicit expressions
    3. Hate speech, discriminatory expressions
    4. Threatening, violent expressions
    5. Spam, promotional content

    Please judge considering subtle nuances and context.

    Please provide your response only in the following JSON format. Do not include backticks or code block formatting (```json, ```python, etc.):
    {
        "is_appropriate": true/false,
        "confidence": 0.0-1.0,
        "detected_issues": ["List of detected issues"],
        "severity": "low/medium/high",
        "reason": "Rationale for judgment"
    }
    """

IMAGE_MATCH_PROMPT = """
    Please analyze whether the image is related to the product:

    Please judge based on the following criteria:
    1. Does the image show the product or related products?
    2. Does the image match the product category?
    3. Is the image appropriate for a product review?

    Please provide your response only in the following JSON format. Do not include backticks or code block formatting (```json, ```python, etc.):
    {
        "is_related": true/false,
        "confidence": 0.0-1.0,
        "reason": "Rationale for judgment",
        "detected_objects": ["List of main objects detected in the image"]
    }
    """

RATING_CONSISTENCY_PROMPT = """
    Please analyze whether the review's rating and content are consistent:

    Please judge based on the following criteria:
    1. Overall sentiment of the review content (positive/negative/neutral)
    2. Consistency between rating and sentiment
    3. Consider irony, sarcasm, and mixed emotions
    4. Understand context and nuances

    Judgment criteria:
    - Rating 4-5 points: Expect positive content
    - Rating 1-2 points: Expect negative content
    - Rating 3 points: Expect neutral content

    Please provide your response only in the following JSON format. Do not include backticks or code block formatting (```json, ```python, etc.):
    {
        "content_sentiment": "positive/negative/neutral",
        "sentiment_confidence": 0.0-1.0,
        "is_consistent": true/false,
        "reason": "Rationale for judgment",
        "detected_emotions": ["List of detected emotions or expressions"]
    }
"""


@tool
def check_profanity(content: str) -> Any:
    """
    Moderate the review content for profanity/inappropriate expressions.

    Args:
        content (str): Review content to check

    Returns:
        Any: Check result
    """
    profanity_agent = Agent(
        model="us.anthropic.claude-sonnet-4-6",
        system_prompt=PROFANITY_PROMPT,
    )
    return profanity_agent(
        f"Please moderate the following review content for profanity/inappropriate expressions. <review_content>{content}</review_content>"
    )


@tool
def check_image_product_match(image_path: str, product_data: Dict) -> Any:
    """
    Verify the relevance between the uploaded image and the actual product.

    Args:
        image_path (str): Uploaded image file path
        product_data (Dict): Product information

    Returns:
        Any: Match check result
    """
    try:
        if not image_path or not os.path.exists(image_path):
            return {
                "status": "SKIP",
                "reason": "No uploaded image.",
                "confidence": 1.0,
            }
        image_match_agent = Agent(
            model="us.anthropic.claude-haiku-4-5-20251001-v1:0",
            system_prompt=IMAGE_MATCH_PROMPT,
            tools=[image_reader],
        )

        return image_match_agent(
            f"Please check the relevance between the following image and product information. <image_path>{image_path}</image_path> <product_data>{product_data}</product_data>"
        )
    except Exception as e:
        return {"status": "ERROR", "reason": str(e), "confidence": 1.0}


@tool
def check_rating_consistency(rating: int, content: str) -> Any:
    """
    Analyze the consistency between rating and review content.

    Args:
        rating (int): Rating (1-5)
        content (str): Review content

    Returns:
        Dict[str, Any]: Consistency check result
    """
    rating_consistency_agent = Agent(
        model="us.anthropic.claude-haiku-4-5-20251001-v1:0",
        system_prompt=RATING_CONSISTENCY_PROMPT,
    )
    return rating_consistency_agent(
        f"Please analyze the consistency between the following rating and review content. <rating>{rating}</rating> <review_content>{content}</review_content>"
    )
