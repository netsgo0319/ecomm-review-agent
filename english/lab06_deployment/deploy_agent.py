from bedrock_agentcore_starter_toolkit import Runtime
from boto3.session import Session

boto_session = Session()
region = boto_session.region_name

agentcore_runtime = Runtime()
agent_name = "review_agent"

response = agentcore_runtime.configure(
    entrypoint="agent/agentcore_agent.py",
    execution_role="<your-runtime-execution-role-arn>",
    auto_create_ecr=True,
    requirements_file="requirements.txt",
    region=region,
    agent_name=agent_name,
)

launch_result = agentcore_runtime.launch(auto_update_on_conflict=True)
print('-'*10)
print("Agent Runtime ARN: " + launch_result.agent_arn)
print('-'*10)