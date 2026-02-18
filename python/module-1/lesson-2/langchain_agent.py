from langchain.agents import create_agent
from langchain.tools import tool
from dotenv import load_dotenv

load_dotenv()

@tool
def weather_retriever():
    """Get the current weather conditions"""
    return "It is sunny today"

agent = create_agent(
    model="gpt-5-nano",
    tools=[weather_retriever]
)

messages = [{"role": "user", "content": "what is the weather today?"}]

agent.invoke({"messages": messages})
