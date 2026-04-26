import json
import logging

from strands import Agent, tool

# Strands logger configuration
logging.getLogger("strands").setLevel(logging.INFO)

# Log output format configuration
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s", handlers=[logging.StreamHandler()]
)

SYSTEM_PROMPT = """
    You are a review sentiment analysis expert.
    Please analyze the review text to classify sentiment and assign a score.

    <Sentiment Classification>
    - positive: Positive sentiment (satisfaction, joy, recommendation, etc.)
    - negative: Negative sentiment (dissatisfaction, disappointment, not recommended, etc.)
    - neutral: Neutral sentiment (objective description, simple information, etc.)
    </Sentiment Classification>

    <Score Range>
    Sentiment score: -1.0 (very negative) ~ 1.0 (very positive)
    </Score Range>

    <Important Notes>
    - Carefully detect irony and sarcastic expressions (e.g., 'Really great!' with negative context)
    - When there are mixed emotions, identify the overall dominant sentiment
    - Consider euphemistic expressions: 'not bad' is positive, 'so-so' is usually satisfactory
    - Understand the context of domain-specific terminology (e.g., 'difficult' in games can be positive)
    - Consider the relative meaning of comparative expressions (e.g., 'better than~')
    - Set confidence low if the text is too short or ambiguous
    </Important Notes>

    <Output Format>
    Please return the result in JSON format. Do not include backticks or code block formatting (```json, ```python, etc.):
    {
    "sentiment": "positive|negative|neutral",
    "score": 0.8,
    "confidence": 0.9,
    "reason": "Analysis rationale"
    }
    </Output Format>
"""
# Create sentiment analysis Agent

@tool
def analyze_sentiment(review_content: str) -> dict:
    """
    Main function to analyze sentiment of review text (using Strands Agent)

    Args:
        review_content (str): Review text to analyze

    Returns:
        dict: Sentiment analysis result
    """
    sentiment_agent = Agent(
        model="us.anthropic.claude-sonnet-4-6",
        system_prompt=SYSTEM_PROMPT,
    )

    # Call Strands Agent
    result = sentiment_agent(review_content)
    str_result = str(result)

    return {
        "success": True,
        "sentiment_result": json.loads(str_result),
        "raw_response": str_result,
    }
