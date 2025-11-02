import uuid
import asyncio
from typing import Optional, List, Dict, Any
import json
import sys
from agent_squad.orchestrator import AgentSquad, AgentSquadConfig
from agent_squad.agents import (
    BedrockLLMAgent,
    BedrockLLMAgentOptions,
    AgentResponse,
    AgentCallbacks,
)
from agent_squad.types import ConversationMessage, ParticipantRole

AWS_SESSION_TOKEN = "IQoJb3JpZ2luX2VjEGoaCXVzLWVhc3QtMSJHMEUCIF8rt3lsD0WnB3aZsOcaUaqwGkHgpaxr2ld2xeuS2JhiAiEAtd8hI7qWJUGWP/JuqwRhOp7qYH3GX0xK3BexGsy3TNEqmQIIMhAAGgw5OTIzODI2MTgzMjciDIKUuy3we3+Av+ZQHCr2ATLtyE8frvQSeyWmRKPirUgdjpd0VA/O7qL5Qyo1oTg0oFdPwRQzFDBhv/hHuKRqFIBFyYpP3zSsd/9l7xM7+0idmzvdcS5emUfL9DSNiWWQA/nNq9+hEECZHUAfbzCwU0Ci8+zOYIFyksBLmCF0cKj7qFTQVK5hyzzYkU46moBGFDKJi3pZXp66gSQttIlvYa4JzTAqhS+uNV1gtO75GZ2jJD23XjjPHruunpnNTwFshiZE4dha9Q+yqdlxCD7oi28GbFueCZqcIpRg7JJkss5j1NNWVKUfef0VgERVZHs1knpQArt0oC5fAme1b/xDponKb593ETD6/pjIBjqdAaMa1lhGJHl9bC5GyXM6nUckvnjZthTtYyVU97AedQZ2MJdAKuY7+n67XVm5s5c/TYWJxo86WQB+2+CSP3Agn2UG55abV2Ld+YjK93vt63TdtuJMQ7hcvISmtt6w8OCYexBaNe+TbkSWT2p1pLn76zOZOBk1HdjqvNQLmKXH9j1j9kfsD76m+boVWv3QCoN198YBPnR+VK5Jh7C+RbQ="

orchestrator = AgentSquad(
    options=AgentSquadConfig(
        LOG_AGENT_CHAT=True,
        LOG_CLASSIFIER_CHAT=True,
        LOG_CLASSIFIER_RAW_OUTPUT=True,
        LOG_CLASSIFIER_OUTPUT=True,
        LOG_EXECUTION_TIMES=True,
        MAX_RETRIES=3,
        USE_DEFAULT_AGENT_IF_NONE_IDENTIFIED=True,
        MAX_MESSAGE_PAIRS_PER_AGENT=10,
    )
)


class BedrockLLMAgentCallbacks(AgentCallbacks):
    async def on_llm_new_token(self, token: str) -> None:
        # handle response streaming here
        print(token, end="", flush=True)

"""
tech_agent = BedrockLLMAgent(
    BedrockLLMAgentOptions(
        name="Tech Agent",
        streaming=True,
        description="Specializes in technology areas including software development, hardware, AI, \
  cybersecurity, blockchain, cloud computing, emerging tech innovations, and pricing/costs \
  related to technology products and services.",
        callbacks=BedrockLLMAgentCallbacks()
        )
    )
    

orchestrator.add_agent(tech_agent)

health_agent = BedrockLLMAgent(
    BedrockLLMAgentOptions(
        name="Health Agent",
        description="Focuses on health and medical topics such as general wellness, nutrition, diseases, treatments, mental health, fitness, healthcare systems, and medical terminology or concepts.",
        callbacks=BedrockLLMAgentCallbacks(),
    )
)
orchestrator.add_agent(health_agent)
"""

async def handle_request(
    _orchestrator: AgentSquad, _user_input: str, _user_id: str, _session_id: str
):
    response: AgentResponse = await _orchestrator.route_request(
        _user_input, _user_id, _session_id
    )
    # Print metadata
    print("\nMetadata:")
    print(f"Selected Agent: {response.metadata.agent_name}")
    if response.streaming:
        print("Response:", response.output.content[0]["text"])
    else:
        print("Response:", response.output.content[0]["text"])


if __name__ == "__main__":
    USER_ID = "user123"
    SESSION_ID = str(uuid.uuid4())
    print("Welcome to the interactive Multi-Agent system. Type 'quit' to exit.")
    while True:
        # Get user input
        user_input = input("\nYou: ").strip()
        if user_input.lower() == "quit":
            print("Exiting the program. Goodbye!")
            sys.exit()
        # Run the async function
        asyncio.run(handle_request(orchestrator, user_input, USER_ID, SESSION_ID))
