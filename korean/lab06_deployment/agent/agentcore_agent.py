from agent.orchestrator.agent import comprehensive_analyzer
from bedrock_agentcore import BedrockAgentCoreApp

app = BedrockAgentCoreApp()


@app.entrypoint
def invoke_agent(payload):
    review_data = payload.get("review_data")
    product_data = payload.get("product_data")
    response = comprehensive_analyzer(
        product_data=product_data, review_data=review_data
    )
    return {"result": response}


if __name__ == "__main__":
    app.run()
