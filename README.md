# LCA LangSmith Professional

Course materials for LangSmith Professional, with Python and TypeScript implementations.

## Project Structure

Both `python/` and `ts/` directories mirror each other with equivalent implementations.

```
├── python/
│   ├── officeflow-agent/              # OfficeFlow customer support agent (Emma)
│   │   ├── agent_v0.py                # Baseline agent (no tracing)
│   │   ├── agent_v1.py                # + LangSmith tracing
│   │   ├── agent_v2.py                # + Enhanced tool instructions
│   │   ├── agent_v3.py                # + Stock information policy
│   │   ├── agent_v4.py                # + No-chunking RAG
│   │   ├── agent_v5.py                # + Conciseness improvements
│   │   ├── inventory/                 # SQLite product database
│   │   └── knowledge_base/            # Company policy documents + embeddings
│   │
│   ├── module-1/
│   │   └── lesson-2/                  # Tracing with LangSmith
│   │       └── third_party_agent.py   # Weather agent with tool calling
│   │
│   ├── module-2/                      # Evaluation fundamentals
│   │   ├── lesson-3/                  # Running experiments
│   │   │   └── run_experiment.py
│   │   ├── lesson-4/                  # Code-based evaluation
│   │   │   ├── eval_schema_check.py   # Schema-before-query evaluator
│   │   │   └── run_eval.py
│   │   ├── lesson-5/                  # LLM-as-judge
│   │   │   └── run_experiment.py
│   │   └── lesson-6/                  # Pairwise evaluation
│   │       ├── run_agents.py
│   │       ├── eval_conciseness_pairwise.py
│   │       └── run_pairwise_experiment.py
│   │
│   ├── module-3/                      # Production & scaling
│   │   └── lesson-2/                  # Trace upload
│   │       ├── generate_traces.py
│   │       └── upload_traces.py
│   │
│   ├── pyproject.toml
│   └── .env.example
│
└── ts/
    ├── officeflow-agent/              # OfficeFlow customer support agent (Emma)
    │   ├── agent_v0.ts                # Baseline agent (no tracing)
    │   ├── agent_v1.ts                # + LangSmith tracing
    │   ├── agent_v2.ts                # + Enhanced tool instructions
    │   ├── agent_v3.ts                # + Stock information policy
    │   ├── agent_v4.ts                # + No-chunking RAG
    │   ├── agent_v5.ts                # + Conciseness improvements
    │   ├── inventory/                 # SQLite product database
    │   └── knowledge_base/            # Company policy documents + embeddings
    │
    ├── module-1/
    │   └── lesson-2/                  # Tracing with LangSmith
    │       └── third_party_agent.ts   # Weather agent with tool calling
    │
    ├── module-2/                      # Evaluation fundamentals
    │   ├── lesson-3/                  # Running experiments
    │   │   └── run_experiment.ts
    │   ├── lesson-4/                  # Code-based evaluation
    │   │   ├── eval_schema_check.ts   # Schema-before-query evaluator
    │   │   └── run_eval.ts
    │   ├── lesson-5/                  # LLM-as-judge
    │   │   └── run_experiment.ts
    │   └── lesson-6/                  # Pairwise evaluation
    │       ├── run_agents.ts
    │       ├── eval_conciseness_pairwise.ts
    │       └── run_pairwise_experiment.ts
    │
    ├── module-3/                      # Production & scaling
    │   └── lesson-2/                  # Trace upload
    │       ├── generate_traces.ts
    │       └── upload_traces.ts
    │
    ├── package.json
    └── example.env
```
