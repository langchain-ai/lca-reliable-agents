"""
Generate 100 QA pairs as LangSmith traces.
Creates 30-50 threads with 1-4 QA pairs each.
Users have one of 3 sentiments: satisfied, unsatisfied, neutral
"""

import asyncio
import uuid
import random
from agent_v5 import chat, load_knowledge_base
import langsmith as ls

# Questions organized by sentiment

SATISFIED_QUESTIONS = [
    # Happy product inquiries
    "Hi! I love your service. Do you have copy paper in stock?",
    "You guys are great! Looking for some pens today.",
    "Thanks for the quick delivery last time! Need more notebooks.",
    "Your staplers are the best - do you have any left?",
    "I've been a customer for years, always happy! Need file folders.",
    "Fantastic service as always. What highlighters do you carry?",
    "Love shopping here! Do you have sticky notes?",
    "Your prices are so reasonable. How much for binders?",
    "Best office supply company around! Any pencils in stock?",
    "Always a pleasure! Looking for tape dispensers.",
    "You've never let me down. Do you have scissors?",
    "Great experience every time. What markers do you sell?",
    "I recommended you to all my colleagues! Need erasers.",
    "Your customer service is amazing. How much is copy paper?",
    "So happy with my last order! Do you have paper clips?",

    # Happy policy questions
    "Love your return policy! Just confirming - 30 days right?",
    "Your shipping is always so fast! What's the free shipping minimum?",
    "Great that you ship to Canada! How long does that take?",
    "I appreciate the business account option. How do I sign up?",
    "Your phone support is wonderful. What are your hours?",
    "Thanks for making ordering so easy! Do you accept POs?",

    # Happy follow-ups
    "Perfect, exactly what I needed!",
    "That's wonderful, thank you so much!",
    "You're the best, I'll place an order right away!",
    "Excellent, this is why I keep coming back!",
    "Amazing, thanks for all your help today!",
]

UNSATISFIED_QUESTIONS = [
    # Frustrated product inquiries
    "I've been waiting forever. Do you have copy paper or not?",
    "This is ridiculous. Are staplers even in stock?",
    "Your website is useless. Just tell me if you have pens.",
    "I'm so frustrated. The notebooks I ordered were wrong.",
    "This is the third time I'm asking - do you have file folders?",
    "Unbelievable. How hard is it to stock highlighters?",
    "I've been on hold for 20 minutes. Do you have binders?",
    "Your prices keep going up. How much are sticky notes now?",
    "I'm very disappointed. My last order was all wrong.",
    "This is unacceptable. I need tape dispensers TODAY.",
    "Why is this so difficult? Do you have scissors or not?",
    "I'm losing my patience here. What markers do you have?",
    "I've had nothing but problems. Are erasers available?",
    "Your service has really gone downhill. How much for paper?",
    "I'm about to switch suppliers. Do you have paper clips?",

    # Frustrated policy questions
    "Your return policy is confusing! Can I return this or not?",
    "Why is shipping so expensive? What's the minimum for free?",
    "I've been waiting 2 weeks for my order! Where is it?",
    "Nobody ever answers the phone. What are your actual hours?",
    "I was charged twice! Who do I contact about this?",
    "Your website crashed during checkout. How do I order now?",
    "The item arrived damaged. What's your defective item policy?",
    "I can't believe there's a minimum order. That's ridiculous!",

    # Frustrated follow-ups
    "That doesn't help me at all.",
    "Are you serious? That's your answer?",
    "I need to speak to a manager.",
    "This is completely unacceptable.",
    "I want a refund immediately.",
    "I'm filing a complaint about this.",
]

NEUTRAL_QUESTIONS = [
    # Neutral product inquiries
    "Do you have copy paper?",
    "What's the price on staplers?",
    "Are pens in stock?",
    "I need notebooks. What do you have?",
    "Looking for file folders.",
    "Do you carry highlighters?",
    "What binders are available?",
    "How much for sticky notes?",
    "Do you have tape dispensers?",
    "I need paper clips.",
    "What scissors do you sell?",
    "Any markers available?",
    "Do you have erasers in stock?",
    "What's the cost of copy paper?",
    "I'm looking for pencils.",
    "Do you have blue ballpoint pens?",
    "What spiral notebooks do you carry?",
    "I need manila file folders.",

    # Neutral policy questions
    "What's your return policy?",
    "How much is shipping?",
    "Is there free shipping?",
    "Do you ship to Canada?",
    "What payment methods do you accept?",
    "Is there a minimum order amount?",
    "What are your business hours?",
    "Where are you located?",
    "Do you offer business accounts?",
    "How long does shipping take?",
    "Can I pick up my order?",
    "What's your phone number?",

    # Neutral follow-ups
    "Okay, thanks.",
    "Got it.",
    "And the price?",
    "What about shipping?",
    "Any other options?",
    "Is that all you have?",
]


def generate_thread_questions(sentiment: str):
    """Generate 1-4 questions for a single thread with consistent sentiment."""
    num_questions = random.choices([1, 2, 3, 4], weights=[20, 40, 30, 10])[0]

    if sentiment == 'satisfied':
        pool = SATISFIED_QUESTIONS
    elif sentiment == 'unsatisfied':
        pool = UNSATISFIED_QUESTIONS
    else:
        pool = NEUTRAL_QUESTIONS

    # Pick unique questions from the pool
    questions = random.sample(pool, min(num_questions, len(pool)))
    return questions


async def run_thread(questions: list[str], thread_id: str, sentiment: str):
    """Run a series of questions in a single thread."""
    results = []

    for i, question in enumerate(questions):
        print(f"    Q{i+1}: {question[:70]}{'...' if len(question) > 70 else ''}")

        # Use trace with explicit inputs, and set outputs after
        with ls.trace(
            name='Emma',
            inputs={'question': question},
            metadata={'thread_id': thread_id, 'user_sentiment': sentiment}
        ) as run:
            result = await chat(question)
            response = result["output"]
            messages = result["messages"]
            run.outputs = {'output': response, 'messages': messages}
            results.append({
                'question': question,
                'response': response,
                'sentiment': sentiment
            })

        print(f"    A{i+1}: {response[:70]}{'...' if len(response) > 70 else ''}")

    return results


async def main():
    print("Loading knowledge base...")
    await load_knowledge_base()
    print()

    # Generate threads until we have ~100 QA pairs
    total_qa_pairs = 0
    thread_count = 0
    all_results = []

    # Track sentiment distribution
    sentiment_counts = {'satisfied': 0, 'unsatisfied': 0, 'neutral': 0}

    print("Generating QA traces with varied user sentiments...")
    print("=" * 70)

    while total_qa_pairs < 100:
        thread_id = str(uuid.uuid4())

        # Roughly equal distribution of sentiments
        sentiment = random.choice(['satisfied', 'unsatisfied', 'neutral'])
        questions = generate_thread_questions(sentiment)

        # Don't exceed ~100 total
        if total_qa_pairs + len(questions) > 105:
            questions = questions[:100 - total_qa_pairs]

        if not questions:
            break

        thread_count += 1
        sentiment_counts[sentiment] += len(questions)

        emoji = {'satisfied': '😊', 'unsatisfied': '😠', 'neutral': '😐'}[sentiment]
        print(f"\nThread {thread_count} [{sentiment.upper()} {emoji}] ({thread_id[:8]}...) - {len(questions)} questions:")

        results = await run_thread(questions, thread_id, sentiment)
        all_results.append({
            'thread_id': thread_id,
            'sentiment': sentiment,
            'qa_pairs': results
        })

        total_qa_pairs += len(questions)
        print(f"  Running total: {total_qa_pairs} QA pairs")

    print()
    print("=" * 70)
    print(f"COMPLETE: {total_qa_pairs} QA pairs across {thread_count} threads")
    print(f"Sentiment distribution:")
    for s, count in sentiment_counts.items():
        print(f"  {s}: {count} questions")
    print("=" * 70)

    # Save summary to JSON
    import json
    with open('qa_traces_summary.json', 'w') as f:
        json.dump({
            'total_qa_pairs': total_qa_pairs,
            'total_threads': thread_count,
            'sentiment_distribution': sentiment_counts,
            'threads': all_results
        }, f, indent=2)
    print(f"\nSummary saved to qa_traces_summary.json")


if __name__ == "__main__":
    asyncio.run(main())
