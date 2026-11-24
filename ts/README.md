# Building Reliable Agents - TypeScript

## Introduction

Welcome to LangChain Academy's **Building Reliable Agents** course!

---

## 🚀 Setup

### Prerequisites

- The Chrome browser is recommended
- Node.js >= 18 ([download here](https://nodejs.org/)) [More info](#nodejs-version-management)
- npm (included with Node.js)

### Installation

Download the course repository
```bash
# Clone the repo (shallow — latest code only)
git clone --depth 1 https://github.com/langchain-ai/lca-reliable-agents.git
cd lca-reliable-agents/ts
```

Install dependencies
```bash
npm install
```

Make a copy of example.env
```bash
# Create .env file
cp example.env .env
```

Edit the .env file to include the keys below. [More info](#model-providers)
```bash
# Direct OpenAI chat and knowledge-base embeddings
OPENAI_API_KEY='your_openai_api_key_here'

# Optional chat routing through LangSmith Gateway
LANGSMITH_GATEWAY=false
# LANGSMITH_GATEWAY_API_KEY='your_gateway_api_key_here'

# LangSmith tracing, experiments, feedback, and trace uploads
LANGSMITH_API_KEY='your_langsmith_api_key_here'
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=lca-reliable-agents
# LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com
```

Create a [LangSmith](https://smith.langchain.com/) account and API Key.
For the default direct-provider setup, get an OpenAI API key [here](https://openai.com/index/openai-api/).

### Optional: LangSmith Gateway for chat

The course uses the raw OpenAI SDK, which does not read `LANGSMITH_GATEWAY` itself. Our `model_config.ts` helper routes all course chat calls, including the local pairwise judge, through the OpenAI-compatible provider path when you opt in. The installed SDK already supports explicit API keys and base URLs; no package upgrade is needed.

First ask your workspace administrator to [configure Gateway and the OpenAI provider secret](https://docs.langchain.com/langsmith/llm-gateway-admin-setup), and confirm access to the course's GPT-5 models. Then edit `.env`:

```dotenv
LANGSMITH_GATEWAY=true
LANGSMITH_API_KEY=your_langsmith_api_key_here
```

Replace the placeholder with your real key. To use a separate inference credential, set `LANGSMITH_GATEWAY_API_KEY`; a nonempty override takes precedence over `LANGSMITH_API_KEY`. An empty override falls back to `LANGSMITH_API_KEY`. Missing, blank, and template keys are rejected for the selected chat route.

- `true`, `1`, or `yes` (case-insensitive) selects `https://gateway.smith.langchain.com/openai/v1`
- `false`, `0`, `no`, unset, or empty keeps direct OpenAI chat as the default
- A custom root URL, such as `https://eu.gateway.smith.langchain.com`, gets `/openai/v1` appended; do not include that provider path yourself

You can export the same values in your shell instead of creating `.env`. Existing shell values take precedence; restart the script after changes. Do not replace `OPENAI_API_KEY` with a LangSmith key or globally redirect `OPENAI_BASE_URL` to Gateway.

**Course limits:** OfficeFlow knowledge-base searches and embedding generation still call OpenAI directly and require `OPENAI_API_KEY`, even in Gateway mode. The basic Module 1 chat examples and local pairwise judge do not need a local OpenAI key in Gateway mode. Tools remain local SQLite and file operations; Gateway only changes chat transport. The course keeps its model names and does not automatically switch providers.

Tracing is independent: `LANGSMITH_TRACING=false` disables application tracing, not Gateway routing or Gateway-side tracing. A separate Gateway key does not authenticate LangSmith experiments, feedback, trace uploads, or application tracing; those need `LANGSMITH_API_KEY` and the correct `LANGSMITH_ENDPOINT`. Configure credentials for any evaluator running in the LangSmith UI on the server; a local `.env` does not configure hosted evaluators.

### Setup Verification

The checker validates the selected chat credential and, when enabled, tracing. Embeddings and LangSmith experiments/uploads have the separate requirements above. After setup, run:

```bash
npx tsx env_utils.ts
```

[If the script flags issues, see this section below.](#setup-verification-issues)

### Running Scripts

```bash
# Example: run the agent interactively
npx tsx officeflow-agent/agent_v5.ts

# Example: run an experiment
npx tsx module-2/lesson-3/run_experiment.ts
```

### If you are using coding agents in the course

You can provide your agent access to the LangSmith Documents. The instructions are [here](https://docs.langchain.com/use-these-docs).


## 🎓 Lessons

### OfficeFlow Agent

The course builds an iterative customer support agent (versions v0–v5) for OfficeFlow Supply Co., with tools for database queries and knowledge base search.

### Module 1: Observation

- **Lesson 1 — Observability.** Why traditional debugging falls short for AI agents and how observability tools fill the gap.
- **Lesson 2 — Tracing with LangSmith.** Instrument your agent so every LLM call, tool invocation, and decision is captured in a trace.
- **Lesson 3 — Analyzing your Agent.** Use traces to run through PRD scenarios, spot failures, and iteratively debug your agent across multiple versions.

### Module 2: Evaluation

- **Lesson 1 — Evaluating Agents.** Why you need automated evals to monitor agent quality over time and detect regression as you develop.
- **Lesson 2 — Creating Datasets.** Build collections of test inputs and reference outputs for repeatable evaluation.
- **Lesson 3 — Running Experiments.** Connect a target, a dataset, and evaluators to run your first experiment in LangSmith.
- **Lesson 4 — Eval 1 - Code-based Eval.** Write deterministic evaluators that work like unit tests — checking tool usage, output shape, and keyword matching.
- **Lesson 5 — Eval 2 - LLM-as-Judge.** Use an LLM to evaluate subjective criteria that are hard to test with code alone.
- **Lesson 6 — Eval 3 - Pairwise Evaluations.** Compare two agent versions side by side to measure which performs better.

### Module 3: Moving Towards Production

- **Lesson 1 — Moving Towards Production.** Transition from internal testing to real users, and learn the techniques needed to observe and evaluate at scale.
- **Lesson 2 — Insights Agent.** Automatically analyze traces at scale to detect usage patterns and failure modes across hundreds of traces.
- **Lesson 3 — Online Evals.** Automatically score every production trace as it comes in, giving you continuous signal on agent quality.

## 📖 Related Resources

### Optional: LangSmith Gateway for chat

The course uses the raw OpenAI SDK, which does not read `LANGSMITH_GATEWAY` itself. Our `model_config.ts` helper routes all course chat calls, including the local pairwise judge, through the OpenAI-compatible provider path when you opt in. The installed SDK already supports explicit API keys and base URLs; no package upgrade is needed.

First ask your workspace administrator to [configure Gateway and the OpenAI provider secret](https://docs.langchain.com/langsmith/llm-gateway-admin-setup), and confirm access to the course's GPT-5 models. Then edit `.env`:

```dotenv
LANGSMITH_GATEWAY=true
LANGSMITH_API_KEY=your_langsmith_api_key_here
```

Replace the placeholder with your real key. To use a separate inference credential, set `LANGSMITH_GATEWAY_API_KEY`; a nonempty override takes precedence over `LANGSMITH_API_KEY`. An empty override falls back to `LANGSMITH_API_KEY`. Missing, blank, and template keys are rejected for the selected chat route.

- `true`, `1`, or `yes` (case-insensitive) selects `https://gateway.smith.langchain.com/openai/v1`
- `false`, `0`, `no`, unset, or empty keeps direct OpenAI chat as the default
- A custom root URL, such as `https://eu.gateway.smith.langchain.com`, gets `/openai/v1` appended; do not include that provider path yourself

You can export the same values in your shell instead of creating `.env`. Existing shell values take precedence; restart the script after changes. Do not replace `OPENAI_API_KEY` with a LangSmith key or globally redirect `OPENAI_BASE_URL` to Gateway.

**Course limits:** OfficeFlow knowledge-base searches and embedding generation still call OpenAI directly and require `OPENAI_API_KEY`, even in Gateway mode. The basic Module 1 chat examples and local pairwise judge do not need a local OpenAI key in Gateway mode. Tools remain local SQLite and file operations; Gateway only changes chat transport. The course keeps its model names and does not automatically switch providers.

Tracing is independent: `LANGSMITH_TRACING=false` disables application tracing, not Gateway routing or Gateway-side tracing. A separate Gateway key does not authenticate LangSmith experiments, feedback, trace uploads, or application tracing; those need `LANGSMITH_API_KEY` and the correct `LANGSMITH_ENDPOINT`. Configure credentials for any evaluator running in the LangSmith UI on the server; a local `.env` does not configure hosted evaluators.

### Setup Verification Issues
**What the verification checks:**
- ✅ Node.js executable location and version (must be >=18)
- ✅ npm and tsx are available
- ✅ Required packages are installed with correct versions
- ✅ Environment variables (API keys) are properly configured

**Configuration Issues and Solutions:**

<details>
<summary>Module not found when running scripts</summary>

If you see an error like `Cannot find module`, you likely haven't installed dependencies yet.

**Solution:**
```bash
npm install
```

</details>

<details>
<summary>Environment Variable Conflicts</summary>

If you see a warning about "ENVIRONMENT VARIABLE CONFLICTS DETECTED", you have API keys set in your system environment that differ from your .env file. Since `dotenv.config()` doesn't override existing variables by default, your system values will be used.

**Solutions:**
1. Unset the conflicting system environment variables (commands provided in warning)
2. Update your .env file to match your system environment

</details>

<details>
<summary>LangSmith Tracing Errors</summary>

If you see "LANGSMITH_TRACING is enabled but LANGSMITH_API_KEY still has the example/placeholder value", you need to set a valid LangSmith API key in your .env file.

</details>

<details>
<summary>Wrong Node.js Version</summary>

If you see a warning about Node.js version not satisfying requirements, you need Node.js >= 18.

**Solution:**
- Install Node.js from [nodejs.org](https://nodejs.org/) or use a version manager like [nvm](#nodejs-version-management)

</details>



### Node.js Version Management

Managing your Node.js version is often best done with a version manager. This allows you to select a Node.js version for the course independent of the system version.

<details open>
<summary>Using nvm (recommended)</summary>

[nvm](https://github.com/nvm-sh/nvm) lets you install and switch between multiple Node.js versions.

```bash
nvm install 22
nvm use 22
npm install
```
</details>

<details>
<summary>Using the official installer</summary>

Download and install Node.js from [nodejs.org](https://nodejs.org/). The LTS version is recommended.

</details>

### Model Providers

For direct chat or embeddings, if you don't have an OpenAI API key, you can sign up [here](https://openai.com/index/openai-api/). The course primarily uses gpt-5-nano which is very inexpensive.

This course has been created using particular models and model providers.  You can use other providers, but you will need to update the API keys in the .env file and make some necessary code changes. LangChain supports many chat model providers [here](https://docs.langchain.com/oss/js/integrations/providers/all_providers).

### Getting Started with LangSmith

- Create a [LangSmith](https://smith.langchain.com/) account
- Create a LangSmith API key

<img width="600" alt="LangSmith Dashboard" src="https://github.com/user-attachments/assets/e39b8364-c3e3-4c75-a287-d9d4685caad5" />

<img width="600" alt="LangSmith API Keys" src="https://github.com/user-attachments/assets/2e916b2d-e3b0-4c59-a178-c5818604b8fe" />

- Update the .env file you created with your new LangSmith API Key.
- Check that `LANGSMITH_TRACING=true` is set in your .env file.

For more information on LangSmith, see our docs [here](https://docs.langchain.com/langsmith/home).

**Note:** If you enable LangSmith tracing by setting `LANGSMITH_TRACING=true` in your .env file, make sure you have a valid `LANGSMITH_API_KEY` set. The environment verification script (`env_utils.ts`) will warn you if tracing is enabled without a valid key.

### Environment Variables

This course uses the [dotenv](https://www.npmjs.com/package/dotenv) module to read key-value pairs from the .env file and set them in the environment in your scripts. They do not need to be set globally in your system environment.

**Note:** If you have API keys already set in your system environment, they may conflict with the ones in your .env file. The `env_utils.ts` verification script will detect and warn you about such conflicts. By default, `dotenv.config()` does not override existing environment variables.

