import json
from uuid import uuid4

import boto3
from botocore.config import Config

agentcore_config = Config(
    connect_timeout=120,  # 120 seconds for connection timeout
    read_timeout=300      # 300 seconds for read timeout
)

def invoke_agentcore_runtime(product_data: dict, review_data: dict):
    client = boto3.client("bedrock-agentcore", region_name="us-west-2", config=agentcore_config)
    payload = json.dumps({"product_data": product_data, "review_data": review_data})

    agent_runtime_arn = "<your-agent-runtime-arn>"
    session_id = str(uuid4())

    response = client.invoke_agent_runtime(
        agentRuntimeArn=agent_runtime_arn,
        runtimeSessionId=session_id,  # Must be 33+ chars
        payload=payload,
    )

    response_body = response["response"].read()
    response_data = json.loads(response_body)
    return response_data


if __name__ == "__main__":
    review_data = {
        "review_id": 5,
        "content": "이어폰 만만세",
        "rating": 3,
        "author": "정수연",
        "timestamp": "2024-01-11 16:22",
    }
    product_data = {"name": "프리미엄 무선 이어폰", "category": "전자기기"}
    response_data = invoke_agentcore_runtime(product_data, review_data)
    print("Agent Response:", response_data)
