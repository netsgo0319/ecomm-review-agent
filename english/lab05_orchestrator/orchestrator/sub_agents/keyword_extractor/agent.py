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
You are a keyword-based review analysis expert.

<Core Tasks>
- Accurately extract sentences related to keywords from review text, considering language characteristics and context
- Perform precise matching with registered keywords
</Core Tasks>

<Work Process>
1. Retrieve registered keywords: Use the file_read tool to read the "lab02_review_keyword_extractor/registered_keywords.txt" file and obtain the list of registered keywords
2. Analyze review text: Identify related keywords and phrases in the review by referring to the registered keywords
3. Perform matching:
   - Prioritize exact matches
   - Consider partial matches and similar words
   - Consider semantic similarities
</Work Process>

<Output Format>
Include the following values in the result:
{
  "matched_keywords": [
        {
            "keyword": "matched keyword",
            "match_type": "exact|partial|semantic",
            "original_phrase": "original phrase found in review (sentence or phrase extracted directly from the review text)"
        }
    ]
}

Note: original_phrase must be the exact text included in the original review.
</Output Format>

<Important Notes>
- Match considering language characteristics (particles, ending variations)
- Include keywords used in negative sentences, but distinguish and process them
- Remove duplicate keywords and keep only the best matches
</Important Notes>
"""

KEYWORD_EXTRACTOR_PROMPT_TEMPLATE = Template(
    """
Please find content that matches the registered keywords in the review below.
<Review>
    $review_text
</Review>
"""
)


class KeywordHighlight(BaseModel):
    """Dataset of matching sentences for each keyword"""

    keyword: str = Field(description="Reference keyword")
    match_type: Literal["exact", "partial", "semantic"]
    original_phrase: str = Field(description="Original phrase found in review")


class KeywordAnalysisResult(BaseModel):
    """Class containing keyword analysis results"""

    matched_keywords: List[KeywordHighlight]

@tool
def search_keywords(review_text: str) -> dict:
    # Keyword matching Agent
    keyword_agent = Agent(
        model="us.anthropic.claude-sonnet-4-6",
        tools=[file_read],
        system_prompt=SYSTEM_PROMPT,
    )

    # Execute Agent
    prompt = KEYWORD_EXTRACTOR_PROMPT_TEMPLATE.substitute(review_text=review_text)
    agent_response = keyword_agent(prompt)
    str_response = str(agent_response)

    # Output as structured output
    result = keyword_agent.structured_output(
        KeywordAnalysisResult, "Extract keyword analysis results in structured form"
    )

    return {
        "success": True,
        "analysis_result": (
            result.model_dump() if hasattr(result, "model_dump") else result.__dict__
        ),
        "raw_response": str_response,
    }
