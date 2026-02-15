"""
Generate QA traces from a CSV file.
Reads questions from CSV, runs them through the agent, and writes responses back.
"""

import asyncio
import csv
import uuid
from agent_v5 import chat, load_knowledge_base
import langsmith as ls


async def run_question(question: str, row_metadata: dict) -> dict:
    """Run a single question through the agent with LangSmith tracing."""
    thread_id = str(uuid.uuid4())

    with ls.trace(
        name='Emma',
        inputs={'question': question},
        metadata={
            'thread_id': thread_id,
            'user_type': row_metadata.get('User_type', ''),
            'information_type': row_metadata.get('Information_type', ''),
            'question_type': row_metadata.get('Question_type', ''),
        }
    ) as run:
        result = await chat(question)
        response = result["output"]
        messages = result["messages"]
        run.outputs = {'output': response, 'messages': messages}

        # Detect which tools were used from the messages
        tools_used = set()
        for msg in messages:
            if msg.get('role') == 'assistant' and msg.get('tool_calls'):
                for tc in msg['tool_calls']:
                    tools_used.add(tc['function']['name'])

        return {
            'response': response,
            'tools_used': ','.join(sorted(tools_used)) if tools_used else 'none'
        }


async def main(csv_path: str = 'generated_questions_results.csv'):
    print("Loading knowledge base...")
    await load_knowledge_base()
    print()

    # Read the CSV
    print(f"Reading questions from {csv_path}...")
    rows = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    total = len(rows)
    print(f"Found {total} questions to process")
    print("=" * 70)

    # Process each question
    for i, row in enumerate(rows):
        question = row['question']
        print(f"\n[{i+1}/{total}] {question[:70]}{'...' if len(question) > 70 else ''}")

        try:
            result = await run_question(question, row)
            row['agent_response'] = result['response']
            row['tool_used'] = result['tools_used']
            print(f"  -> {result['response'][:70]}{'...' if len(result['response']) > 70 else ''}")
            print(f"  Tools: {result['tools_used']}")
        except Exception as e:
            print(f"  ERROR: {e}")
            row['agent_response'] = f"ERROR: {e}"
            row['tool_used'] = 'error'

    # Write back to CSV
    print()
    print("=" * 70)
    print(f"Writing results back to {csv_path}...")

    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"COMPLETE: Processed {total} questions")


if __name__ == "__main__":
    import sys
    csv_file = sys.argv[1] if len(sys.argv) > 1 else 'generated_questions_results.csv'
    asyncio.run(main(csv_file))
