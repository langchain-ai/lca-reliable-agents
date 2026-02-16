import asyncio
import sqlite3
import json
import os
import uuid
from dotenv import load_dotenv
from openai import AsyncOpenAI
from langsmith import traceable, Client
from langsmith.wrappers import wrap_openai
import langsmith as ls

load_dotenv()

# Initialize clients
client = wrap_openai(AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY")))
langsmith_client = Client()

# Configuration
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "lca-ls-project")
thread_id = str(uuid.uuid4())

system_prompt = """You are Emma, a customer support specialist for OfficeFlow Supply Co., a paper and office supplies distribution company serving small-to-medium businesses across North America.

ABOUT YOUR ROLE:
You're part of the Customer Experience team and have been with OfficeFlow for 3 years. You're known for being helpful, efficient, and genuinely caring about solving customer problems. Your manager emphasizes that every interaction is an opportunity to build trust and loyalty.

WHAT YOU CAN HELP WITH:
✓ Product Information - Answer questions about our catalog of office supplies, paper products, writing instruments, organizational tools, and desk accessories
✓ Inventory & Availability - Check current stock levels and help customers find what they need
✓ Product Recommendations - Suggest products based on customer needs, usage patterns, and budget
✓ General Inquiries - Handle questions about our company, product lines, and services

WHAT YOU CANNOT DIRECTLY HANDLE:
✗ Order Placement - While you can provide product info, actual ordering is done through our web portal or by contacting our sales team at sales@officeflow.com
✗ Order Status & Tracking - Direct customers to check their account portal or contact fulfillment@officeflow.com
✗ Returns & Refunds - These require approval from our Returns Department at returns@officeflow.com
✗ Account Changes - Billing, payment methods, and account settings must go through accounts@officeflow.com
✗ Technical Support - For website issues, direct to support@officeflow.com

YOUR COMMUNICATION STYLE:
- Warm and professional, never robotic or overly formal
- Use natural language - "I'd be happy to help" instead of "I will assist you"
- Show empathy when customers are frustrated
- Be specific and accurate with information
- If you don't know something, be honest and direct them to the right resource
- Use the customer's name if they provide it
- Keep responses concise but thorough

IMPORTANT - CHECK DATABASE FIRST:
When customers ask about products or inventory, ALWAYS check the database FIRST before asking clarifying questions. Give them useful information about what you find, rather than asking for more details upfront. For example, if a customer asks "do you have any paper?" - check what paper products are in stock and tell them what's available, don't ask "what type of paper are you looking for?"

INTERACTION GUIDELINES:
1. Always greet customers warmly and acknowledge their question
2. Ask clarifying questions only if truly necessary AFTER checking available information
3. Provide complete, accurate information about products and availability
4. If recommending products, explain why they're a good fit
5. End conversations by checking if they need anything else
6. When you can't help directly, provide the specific contact or resource they need
7. Never make up information - if you're unsure, say so and offer to connect them with someone who knows

EXAMPLE INTERACTIONS:

Customer: "Do you have copy paper?"
You: "Yes, we do! We carry several types of copy paper. Are you looking for standard 8.5x11 inch letter size, or do you need a specific weight or finish? I can check what we have in stock."

Customer: "I need to return an order"
You: "I understand you need to process a return. While I can't handle returns directly, our Returns Department will be happy to help you. You can reach them at returns@officeflow.com or call 1-800-OFFICE-1 ext. 3. They typically respond within 4 business hours. Do you need any other information I can help with?"

Customer: "What's the best pen for signing documents?"
You: "For document signing, I'd recommend a pen with archival-quality ink that won't fade over time. Let me check what we have available that would work well for that purpose."

Remember: You represent OfficeFlow's commitment to excellent customer service. Be helpful, honest, and human in every interaction."""

@traceable(name="query_database")
def query_database(query: str, db_path: str) -> str:
    """Execute SQL query against the inventory database."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        return str(results)
    except Exception as e:
        return f"Error: {str(e)}"

# OpenAI function calling schema
QUERY_DATABASE_TOOL = {
    "type": "function",
    "function": {
        "name": "query_database",
        "description": "SQL query to get information about our inventory for customers like products, quantities and prices.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": """SQL query to execute against the inventory database.

YOU DO NOT KNOW THE SCHEMA. ALWAYS discover it first:
1. Query 'SELECT name FROM sqlite_master WHERE type="table"' to see available tables
2. Use 'PRAGMA table_info(table_name)' to inspect columns for each table
3. Only after understanding the schema, construct your search queries"""
                }
            },
            "required": ["query"]
        }
    }
}

def get_thread_history(thread_id: str, project_name: str):
    """Gets conversation history from LangSmith traces."""
    # Filter runs by the specific thread and project
    filter_string = f'and(in(metadata_key, ["session_id","conversation_id","thread_id"]), eq(metadata_value, "{thread_id}"))'
    # Only grab the LLM runs
    runs = [r for r in langsmith_client.list_runs(project_name=project_name, filter=filter_string, run_type="llm")]

    # If no history exists, return empty list (new conversation)
    if not runs:
        return []

    # Sort by start time to get the most recent interaction
    runs = sorted(runs, key=lambda run: run.start_time, reverse=True)

    # Reconstruct the conversation state from the latest run
    latest_run = runs[0]
    messages = latest_run.inputs.get('messages', [])

    # Add the assistant's response from outputs
    if latest_run.outputs and 'choices' in latest_run.outputs:
        assistant_message = latest_run.outputs['choices'][0]['message']
        return messages + [assistant_message]

    return messages

@traceable(name="Emma")
async def chat(question: str) -> str:
    """Process a user question and return assistant response."""
    db_path = '../inventory/inventory.db'
    tools = [QUERY_DATABASE_TOOL]

    # Fetch conversation history from LangSmith traces
    run_tree = ls.get_current_run_tree()
    current_thread_id = run_tree.metadata.get("thread_id", thread_id)
    history_messages = get_thread_history(current_thread_id, LANGSMITH_PROJECT)

    # Build messages with history
    messages = [
        {"role": "system", "content": system_prompt}
    ] + history_messages + [
        {"role": "user", "content": question}
    ]

    # First API call with tools
    response = await client.chat.completions.create(
        model="gpt-5-nano",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )

    response_message = response.choices[0].message

    # Handle tool calls if the model wants to use them
    while response_message.tool_calls:
        # Add assistant's tool call to messages
        messages.append({
            "role": "assistant",
            "content": response_message.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in response_message.tool_calls
            ]
        })

        # Execute the tool call(s)
        for tool_call in response_message.tool_calls:
            function_args = json.loads(tool_call.function.arguments)

            # Handle query_database tool call
            if tool_call.function.name == "query_database":
                result = query_database(
                    query=function_args.get("query"),
                    db_path=db_path
                )
            else:
                result = f"Error: Unknown tool {tool_call.function.name}"

            # Add tool result to messages
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_call.function.name,
                "content": result
            })

        # Make next API call with tool results
        response = await client.chat.completions.create(
            model="gpt-5-nano",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        response_message = response.choices[0].message

    # Add final response to messages
    final_content = response_message.content
    messages.append({
        "role": "assistant",
        "content": final_content
    })

    return {"messages": messages, "output": final_content}

async def main():
    print("Office Supplies Support Chat")
    print("=" * 50)
    print(f"Thread ID: {thread_id}")
    print("Type 'quit' or 'exit' to end the conversation\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Thank you for chatting! Goodbye!")
            break

        if not user_input:
            continue

        result = await chat(user_input)
        response = result["output"]
        print(f"\nAgent: {response}\n")

if __name__ == "__main__":
    asyncio.run(main())
