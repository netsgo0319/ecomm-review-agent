import json
import logging
import os
from typing import Any, Dict, List

from strands import Agent, tool
from strands_tools import retrieve

# Configure the root strands logger
logging.getLogger("strands").setLevel(logging.INFO)

# Add a handler to see the logs
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s", handlers=[logging.StreamHandler()]
)

# export KNOWLEDGE_BASE_ID=your_kb_id
# export AWS_REGION=us-west-2
os.environ["KNOWLEDGE_BASE_ID"] = "your_kb_id"
os.environ["AWS_REGION"] = "us-west-2"

RESPONSE_SYSTEM_PROMPT = """
    You are an AI assistant that automatically responds to customer reviews for e-commerce sellers.

    To generate appropriate seller responses to customer reviews, please follow this exact sequence:

    <Work Sequence>
    1. First, always use the retrieve tool to search for relevant information in the knowledge base
    2. Analyze the customer review to understand their concerns or emotions
    3. Prepare accurate responses utilizing the retrieved information
    4. Apply the seller's tone and style as defined in SELLER_ANSWER_PROMPT
    5. Generate natural and helpful responses as if the seller is directly responding
    </Work Sequence>

    <Response Guidelines>
    - All factual information is based on the retrieved knowledge base content
    - Match the seller's communication style (seller in their 40s to customers in their 30s)
    - Provide specific and actionable answers rather than vague responses
    - Maintain a professional yet warm tone
    - Do not publicly mention personal or sensitive information
    - For complex issues, appropriately direct to customer service
    - Do not include backticks or code block formatting (```json, ```python, etc.) in responses. Show as plain text.

    </Response Guidelines>

    <Response by Review Type>
    Positive Review: Thank you message + Promise of continued service
    Negative Review: Sincere apology + Specific solution + Related policy guidance
    Inquiry Review: Provide accurate information + Additional inquiry channel guidance
    Shipping Related: Reference shipping guide information
    Refund/Exchange: Reference refund guide policy
    </Response by Review Type>

    <Required Rules>
    - Always use the retrieve tool first before answering
    - Must follow the tone guide in SELLER_ANSWER_PROMPT
    - Write in natural language as if the seller is directly responding
    - Never fabricate information not found in the knowledge base
    - Responses should be concise but complete
    </Required Rules>

    Remember: You represent the seller, so respond authentically as a seller using the knowledge base as the source of truth.
"""

SELLER_ANSWER_PROMPT = """
I am a seller in my 40s, and our products are mainly used by people in their 30s, so please keep this in mind when responding.
Please provide clean and calm information-based answers to customers to avoid any misunderstanding.
However, the tone should be polite.
"""


def generate_auto_response(review: str) -> Dict[str, Any]:
    """
    Main function to generate automatic response to a review

    Args:
        review (str): Review text to analyze

    Returns:
        Dict[str, Any]: Automatic response result
    """

    # Create new Agent for each request
    auto_response_agent = Agent(
        model="us.anthropic.claude-sonnet-4-6",
        tools=[retrieve],
        system_prompt=RESPONSE_SYSTEM_PROMPT
        + f"""
        SELLER_ANSWER_PROMPT: {SELLER_ANSWER_PROMPT}
        """,
    )

    # Generate automatic response to the review
    response = auto_response_agent(review)

    # Extract tool_result
    tool_results = filter_tool_result(auto_response_agent)

    # Return result - includes tool_results
    result = {"response": str(response), "tool_results": tool_results}
    return result


def filter_tool_result(agent: Agent) -> List:
    """
    Function to extract only tool_result from Agent execution result

    Args:
        agent (Agent): Agent instance

    Returns:
        Dict[str, Any]: Dictionary containing only tool_result
    """
    tool_results = []
    for m in agent.messages:
        for content in m["content"]:
            if "toolResult" in content:
                tool_results.append(m["content"][0]["toolResult"])
    return tool_results
