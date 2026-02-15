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
│   ├── chapter-2/                        # Chapter 2: Evaluation fundamentals
│   │   ├── eval_database_usage.py        # Custom evaluator for SQL quality
│   │   ├── eval_conciseness_pairwise.py  # Pairwise conciseness evaluator
│   │   ├── run_experiment.py             # LangSmith experiment runner
│   │   └── run_pairwise_experiment.py    # Pairwise experiment runner
│   │
│   ├── chapter-3/                 # Chapter 3: Synthetic data & advanced eval
│   │   ├── question_generator.py  # Synthetic question generation
│   │   ├── run_questions.py       # Batch question runner
│   │   ├── agent_v5_runner.py     # Agent v5 experiment runner
│   │   ├── enumerate_categories.py
│   │   ├── eval_database_usage.py # Updated evaluator
│   │   └── run_experiment.py      # Experiment runner
│   │
│   ├── generate_qa_traces.py        # QA trace generation
│   ├── pyproject.toml
│   └── .env.example
│
└── ts/
    └── eval_conciseness_pairwise.ts  # Pairwise conciseness evaluator (TypeScript)
```
