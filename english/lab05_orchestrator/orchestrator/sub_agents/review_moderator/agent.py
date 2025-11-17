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


# Unified review moderation Agent system prompt
UNIFIED_MODERATOR_PROMPT = """
    You are a review moderation expert for an e-commerce platform.

    <Main Roles>
    Conduct moderation in the following three categories:
    - Check for profanity/inappropriate expressions in review text -> check_profanity
    - Analyze consistency between rating and review content -> check_rating_consistency
    - Verify relevance of uploaded image to product (only if image exists) -> check_image_product_match
    </Main Roles>

    <Important Notes>
    - Recognize subtle differences in emotional expressions
    - Make comprehensive judgments considering the overall context
    </Important Notes>

    <Output Format>
    After performing all moderation checks, respond with the following JSON schema. Do not include any other explanations or backticks (```json):

    {
        "profanity_check": {
            "status": "PASS|FAIL|SKIP",
            "reason": "Specific rationale (required)",
            "confidence": 0.0-1.0
        },
        "rating_consistency": {
            "status": "PASS|FAIL|SKIP",
            "reason": "Specific rationale (required)",
            "confidence": 0.0-1.0
        },
        "image_match": {
            "status": "PASS|FAIL|SKIP",
            "reason": "Specific rationale (required)",
            "confidence": 0.0-1.0
        },
        "overall_status": "PASS|FAIL",
        "failed_checks": ["List of failed moderation items"]
    }

    </Output Format>
"""

USER_PROMPT_TEMPLATE = Template(
    """
    Please conduct a comprehensive moderation of the following review:

    Review Content: $review_content
    Rating: $rating points (1-5 scale)
    Product: $product
    Category: $category
    Image: $has_image ($image_path)
    """
)


class CheckResult(BaseModel):
    """Individual check result"""

    status: Literal["PASS", "FAIL", "SKIP"] = Field(description="Check status")
    reason: str = Field(description="Specific rationale (required)")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence (0.0-1.0)")


class ReviewModerationResult(BaseModel):
    """Review moderation analysis result"""

    profanity_check: CheckResult = Field(description="Profanity/obscenity check result")
    rating_consistency: CheckResult = Field(description="Rating-content consistency check result")
    image_match: CheckResult = Field(description="Image-content match check result")
    overall_status: Literal["PASS", "FAIL"] = Field(description="Overall moderation pass status")
    failed_checks: List[str] = Field(description="List of failed check items")


def moderate_review(
    review_content: str,
    rating: int,
    product_data: Dict[str, Any],
    image: Optional[PILImage] = None,
) -> Dict[str, Any]:
    """
    Main function to comprehensively moderate a review

    Args:
        review_content (str): Review content
        rating (int): Rating (1-5)
        product_data (Dict[str, Any]): Product information including name and category
        image (Optional[PILImage]): Uploaded image (PIL Image object)

    Returns:
        Dict[str, Any]: Moderation result
    """
    image_path = None
    if image:
        image_path = save_image(image)

    # Create unified moderation Agent
    unified_moderator = Agent(
        model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        tools=[check_profanity, check_rating_consistency, check_image_product_match],
        system_prompt=UNIFIED_MODERATOR_PROMPT,
    )

    # Generate user prompt
    user_prompt = USER_PROMPT_TEMPLATE.substitute(
        review_content=review_content,
        rating=rating,
        product=product_data.get("name", "Unknown"),
        category=product_data.get("category", "Unknown"),
        has_image="Yes" if image else "No",
        image_path=image_path if image_path else "None",
    )

    # Execute unified moderation Agent
    unified_response = unified_moderator(user_prompt)

    # Structured Output
    moderated_result = unified_moderator.structured_output(
        ReviewModerationResult, "Structure the model's comprehensive review moderation result."
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
    Save image to images folder and return the path.

    Args:
        image (PILImage): PIL Image object to save
        images_folder (str): Folder path to save to (default: "images")

    Returns:
        str: Path of the saved image
    """
    os.makedirs(images_folder, exist_ok=True)

    image_format = image.format if image.format else "PNG"
    extension = image_format.lower()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"review_image_{timestamp}.{extension}"
    filepath = os.path.join(images_folder, filename)

    image.save(filepath, format=image_format)

    return filepath
