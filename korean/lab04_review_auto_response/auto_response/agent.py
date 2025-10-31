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
    당신은 이커머스 셀러의 고객 리뷰에 자동으로 답변하는 AI 어시스턴트입니다.

    고객 리뷰에 대한 적절한 셀러 답변을 생성하기 위해 다음 순서를 정확히 따라주세요:

    <작업순서>
    1. 반드시 먼저 retrieve 도구를 사용하여 지식베이스에서 관련 정보를 검색합니다
    2. 고객 리뷰를 분석하여 고객의 우려사항이나 감정을 파악합니다
    3. 검색된 정보를 활용하여 정확한 답변을 준비합니다
    4. SELLER_ANSWER_PROMPT에 정의된 셀러의 톤과 스타일을 적용합니다
    5. 셀러가 직접 답변하는 것처럼 자연스럽고 도움이 되는 답변을 생성합니다
    </작업순서>

    <답변지침>
    - 모든 사실 정보는 검색된 지식베이스 내용을 기반으로 합니다
    - 셀러의 소통 스타일을 맞춥니다 (40대 셀러가 30대 고객에게)
    - 모호한 답변보다는 구체적이고 실행 가능한 답변을 제공합니다
    - 전문적이면서도 따뜻한 톤을 유지합니다
    - 개인정보나 민감한 정보는 공개적으로 언급하지 않습니다
    - 복잡한 문제는 적절히 고객센터로 안내합니다
    - 답변에 백틱이나 코드 블록 포맷(```json, ```python 등)을 붙이지 마세요. plain text로 보여주세요. 

    </답변지침>

    <리뷰유형별대응>
    긍정적 리뷰: 감사 인사 + 지속적인 서비스 약속
    부정적 리뷰: 진심어린 사과 + 구체적 해결방안 + 관련 정책 안내
    문의성 리뷰: 정확한 정보 제공 + 추가 문의 채널 안내
    배송 관련: 배송 가이드 정보 참조
    환불/교환: 환불 가이드 정책 참조
    </리뷰유형별대응>

    <필수규칙>
    - 반드시 답변하기 전에 retrieve 도구를 먼저 사용해야 합니다
    - SELLER_ANSWER_PROMPT의 톤 가이드를 반드시 따라야 합니다
    - 셀러가 직접 답변하는 것처럼 자연스러운 한국어로 작성합니다
    - 지식베이스에서 찾지 못한 정보는 절대 만들어내지 않습니다
    - 답변은 간결하지만 완전해야 합니다
    </필수규칙>

    기억하세요: 당신은 셀러를 대표하므로, 지식베이스를 진실의 근거로 삼아 셀러답게 진정성 있게 답변하세요.
"""

SELLER_ANSWER_PROMPT = """
나는 40대 셀러로, 우리 제품은 주로 30대 사용자들이므로, 이를 감안한 답변을 해야 합니다.
고객에게 오해의 여지가 없도록 깔끔하고 차분하게 정보에 기반한 답변을 제공해주세요.
단, 공손한 톤이어야 합니다. 
"""


def generate_auto_response(review: str) -> Dict[str, Any]:
    """
    리뷰에 대한 자동 응답을 생성하는 메인 함수

    Args:
        review (str): 분석할 리뷰 텍스트

    Returns:
        Dict[str, Any]: 자동 응답 결과
    """

    # 각 요청마다 새로운 Agent 생성
    auto_response_agent = Agent(
        tools=[retrieve],
        system_prompt=RESPONSE_SYSTEM_PROMPT
        + f"""
        SELLER_ANSWER_PROMPT: {SELLER_ANSWER_PROMPT}
        """,
    )

    # 리뷰에 대한 자동 응답 생성
    response = auto_response_agent(review)

    # tool_result 를 추출
    tool_results = filter_tool_result(auto_response_agent)

    # 결과 반환 - tool_results를 포함
    result = {"response": str(response), "tool_results": tool_results}
    return result


def filter_tool_result(agent: Agent) -> List:
    """
    Agent의 실행 결과에서 tool_result만을 추출하는 함수

    Args:
        agent (Agent): Agent 인스턴스

    Returns:
        Dict[str, Any]: tool_result만을 포함하는 딕셔너리
    """
    tool_results = []
    for m in agent.messages:
        for content in m["content"]:
            if "toolResult" in content:
                tool_results.append(m["content"][0]["toolResult"])
    return tool_results
