# LCA LangSmith Professional

Course materials for LangSmith Professional, with Python and TypeScript implementations.

## Project Structure

```
├── python/
│   ├── officeflow_agent/          # OfficeFlow customer support agent (Emma)
│   │   ├── agent_v0.py            # Baseline agent
│   │   ├── agent_v1.py            # + LangSmith tracing
│   │   ├── agent_v2.py            # + Enhanced tool instructions
│   │   ├── agent_v3.py            # + Stock information policy
│   │   ├── agent_v4.py            # + No-chunking RAG
│   │   ├── agent_v5.py            # + Conciseness improvements
│   │   ├── inventory/             # SQLite product databases
│   │   └── knowledge_base/        # Company policy documents
│   │
│   ├── chapter-2/                              # Chapter 2: Evaluation fundamentals
│   │   ├── lesson-3/                           # SQL database evaluation
│   │   │   ├── eval_database_usage.py          # Custom evaluator for SQL quality
│   │   │   └── run_experiment.py               # LangSmith experiment runner
│   │   ├── lesson-4/                           # Experiment runner
│   │   │   └── run_experiment.py               # LangSmith experiment runner
│   │   └── lesson-5/                           # Pairwise evaluation
│   │       ├── eval_conciseness_pairwise.py    # Pairwise conciseness evaluator
│   │       └── run_pairwise_experiment.py      # Pairwise experiment runner
│   │
│   ├── chapter-3/                          # Chapter 3: Synthetic data & advanced eval
│   │   ├── lesson-2/                       # Synthetic question generation pipeline
│   │   │   ├── enumerate_categories.py     # Generate category combinations CSV
│   │   │   ├── question_generator.py       # LLM-based question generation
│   │   │   ├── run_questions.py            # Batch question runner
│   │   │   ├── PRD.md                      # Product requirements doc
│   │   │   ├── question_generator_prompt.md
│   │   │   ├── test_categories.md
│   │   │   └── sample_of_inventory_with_prices.csv
│   │   └── lesson-3/                       # Evaluation pipeline
│   │       ├── eval_database_usage.py      # Custom evaluator for SQL quality
│   │       └── run_experiment.py           # LangSmith experiment runner
│   │
│   ├── pyproject.toml
│   └── .env.example
│
└── ts/
    └── eval_conciseness_pairwise.ts  # Pairwise conciseness evaluator (TypeScript)
```
