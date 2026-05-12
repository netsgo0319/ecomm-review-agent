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
You are an orchestrator that manages review analysis workflows.
Based on the review data input by the user, please moderate and analyze the review, then generate an automatic response by following the agents and sequence below.

<Analysis Agents>
Review analysis agents to utilize (execute in order):
1. Review moderation (includes image-product relevance check, rating-comment consistency check, profanity/explicit content check)
2. Keyword-matching sentence analysis
3. Sentiment analysis
4. Auto-response generation (according to analyzed sentiment)
</Analysis Agents>

<Work Sequence>
1. After review moderation, if it fails the profanity/explicit content check, do not proceed with subsequent steps and terminate. When terminating, respond with the reason for disqualification. (Other review moderation items like image check or rating-comment consistency check can proceed to next steps even if they fail)
2. If the review passes moderation normally, proceed with sentiment analysis and keyword extraction in order to analyze the review.
3. Finally, generate an auto-response
</Work Sequence>

"""


class KeywordHighlight(BaseModel):
    keyword: str = Field(description="Reference keyword")
    match_type: str = Field(description="Matching type: exact, partial, semantic")
    original_phrase: str = Field(description="Original phrase found in review")


class ReviewAnalysis(BaseModel):
    """Complete review analysis."""

    moderation_result: Dict[str, Any] = Field(description="Review moderation result")
    keyword_highlighted_list: List[KeywordHighlight] = Field(
        description="Sentences matching keywords from keyword analysis"
    )
    sentiment: str = Field(description="Sentiment analysis result")
    auto_response: str = Field(description="Auto-response generation result")


def comprehensive_analyzer(
    product_data: Dict[str, Any],
    review_data: Dict[str, Any],
    image: Optional[PILImage] = None,
) -> Dict[str, Any]:
    """
    Main function to generate comprehensive analysis for a review

    Args:
        product_data Dict[str, Any]: Product data
        review_data Dict[str, Any]: Review data to analyze
        image (Optional[PILImage]): Uploaded image (PIL Image object)

    Returns:
        Dict[str, Any]: Comprehensive analysis result
    """

    image_path = None
    if image:
        image_path = save_image(image)

    # Create new Agent for each request
    orchestrator_agent = Agent(
        model="us.anthropic.claude-sonnet-4-6",
        tools=[
            moderate_review,
            search_keywords,
            analyze_sentiment,
            generate_auto_response,
        ],
        system_prompt=ORCHESTRATOR_PROMPT,
    )

    # Respond with comprehensive review analysis result
    orchestrator_agent(
        f"""
    <product_data>{product_data}</product_data>
    <review_data>{review_data}</review_data>
    <image_path>{image_path if image_path else 'None'}</image_path>
    """
    )

    result = orchestrator_agent.structured_output(
        ReviewAnalysis, "Extract analysis results for review data in structured form"
    )

    # Convert Pydantic model to dict
    if hasattr(result, "model_dump"):
        result_dict = result.model_dump()
    elif hasattr(result, "dict"):
        result_dict = result.dict()
    else:
        result_dict = result
    print("*"*10)
    print(result_dict)
    print("*"*10)
    return result_dict


def save_image(
    image: PILImage, images_folder: str = "lab05_orchestrator/images"
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
