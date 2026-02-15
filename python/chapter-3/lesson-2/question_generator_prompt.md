# `question_generator.py` — Specification

## Purpose
Read a category combinations CSV, a PRD, and a product inventory sample, then use an LLM to generate realistic customer questions. For each row in the CSV, generate `repeat_count` questions that reflect the category options in that row. This script only produces questions — no example responses.

## Inputs (CLI)
| Argument | Required | Description |
|---|---|---|
| `--prd` | Yes | Path to the PRD markdown file (e.g., `PRD.md`) |
| `--combos` | Yes | Path to the category combinations CSV (output of `enumerate_categories.py`) |
| `--inventory` | No | Path to product inventory CSV (default: `sample_of_inventory_with_prices.csv`) |
| `-o` | No | Output CSV path (default: `generated_questions.csv`) |

## Process

1. **Read the PRD** — load the full text to give the LLM context about the agent.
2. **Read the product inventory CSV** — loaded into the prompt so product questions reference real items from the catalog.
3. **Read the combinations CSV** — each row has category columns (e.g., `User_type`, `Information_type`, `Question_type`) plus a `repeat_count` column.
4. **For each row**, generate `repeat_count` questions:
   - Pass the PRD, the inventory sample, and the row's category values to the LLM.
   - The LLM generates one realistic customer question per call.
   - Track previously generated questions and instruct the LLM not to repeat them.
5. **Determine `tool_used`** — this is purely rule-based, not LLM-determined:
   - If `Information_type` is `"product"`, set `tool_used` to `"query_database"`.
   - Otherwise, leave `tool_used` empty.

## Output
A CSV file with the following columns:

| Column | Description |
|---|---|
| `question` | The generated customer question |
| `User_type` | From the input row |
| `Information_type` | From the input row |
| `Question_type` | From the input row |
| `tool_used` | `"query_database"` if Information_type is "product", otherwise empty |

## Example

Given input row `standard,product,clear,2`, generate 2 questions:

| question | User_type | Information_type | Question_type | tool_used |
|---|---|---|---|---|
| "Hi, do you carry blue ballpoint pens?" | standard | product | clear | query_database |
| "What's the price on your A4 copy paper?" | standard | product | clear | query_database |

Given input row `frustrated,policy,vague,1`, generate 1 question:

| question | User_type | Information_type | Question_type | tool_used |
|---|---|---|---|---|
| "I've been going back and forth trying to figure out your return process — can someone just explain how it works?" | frustrated | policy | vague | |

## Tone guidance
- **"frustrated" users should be mildly frustrated** — a bit annoyed but still reasonable. Think "had a bad day" not "losing their mind." They might express mild impatience or disappointment but remain civil and coherent. Avoid all-caps, excessive punctuation, or melodramatic language.

## Constraints
- One LLM call per question (keep it simple)
- No example responses generated — only questions
- A product inventory sample CSV is loaded and included in the LLM prompt so product questions reference real items from the catalog
- `tool_used` is determined by code, not by the LLM
- Track all previously generated questions and include them in the prompt to avoid duplicates
