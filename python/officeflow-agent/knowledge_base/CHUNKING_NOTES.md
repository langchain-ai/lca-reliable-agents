# Knowledge Base Chunking Issues - Teaching Notes

## About This Knowledge Base

These policy documents are stored as **Markdown (.md) files** - the same format real companies use for documentation (GitHub, Notion, Confluence all support markdown).

In production, OfficeFlow would likely:
- Store these in a knowledge base platform (Zendesk, Confluence, SharePoint)
- Use an API to fetch updates automatically
- Store embeddings in a vector database (Pinecone, Weaviate, Qdrant)
- Have metadata like version, last_updated, author

For this exercise, we've simplified to local markdown files so students can focus on **the chunking problem** - which is exactly the same whether documents come from files or APIs.

## Recommended Chunking Parameters
For this teaching exercise, use these parameters to expose the chunking problems:
- **Chunk size**: 200 characters
- **Chunk overlap**: 20 characters
- **Step size**: 180 characters (200 - 20 = 180)

## Problems Built Into These Files

### 1. **returns_policy.txt** - Context Separation
- **RMA definition split**: The requirement for an RMA is mentioned early, but what "RMA" stands for (Return Merchandise Authorization) appears sentences later
- **30-day window vs exceptions**: The 30-day return window is in one section, but the critical exception (defective items anytime) is in a separate paragraph
- **Contact info separation**: Email/phone separated from response time guarantees
- **Refund conditions split**: Processing time separated from the conditions that affect refunds

**Example student question**: "How do I return a defective item?"
- **Problem**: Retrieval might get the 30-day policy chunk but miss the exception chunk that says defective items can be returned anytime
- **Symptom**: Agent tells customer they're outside the return window when they shouldn't be

### 2. **shipping_policy.txt** - Critical Details Fragmented
- **Free shipping thresholds**: Cost mentioned first, then "there is a threshold" as a teaser, then the actual $100 threshold several sentences later
- **Cutoff times scattered**: Different shipping methods have different cutoff times (2:00 PM vs 12:00 PM) that get split across chunks
- **Restrictions separation**: Shipping method listed in one chunk, restrictions (Monday-Thursday only) in a different chunk
- **Contact info orphaned**: Department contact separated from what issues they handle

**Example student question**: "What does standard shipping cost?"
- **Problem**: Might retrieve "$8.95 flat rate" chunk but miss the "FREE for orders $100+" chunk
- **Symptom**: Agent quotes $8.95 when customer's order would qualify for free shipping

### 3. **ordering_policy.txt** - Prerequisites Split From Actions
- **Payment timing**: Cards accepted, but when they're charged is mentioned later
- **Minimum order split**: "There is a minimum" followed by suspense, then "$50" appears later
- **Business account benefits**: Benefits listed separately from how to apply
- **Cancellation fees**: Fee mentioned but conditions that avoid the fee are in previous chunk

**Example student question**: "What's the minimum order?"
- **Problem**: Might get "there is a minimum" chunk without the "$50" value, or vice versa
- **Symptom**: Vague or incomplete answer

### 4. **locations_contact.txt** - Related Data Scattered
- **Addresses vs phone numbers**: Distribution center address in one chunk, phone number in another
- **Services vs locations**: What services are available separated from where they're available
- **Department contacts**: Department name/email in one chunk, hours and what they handle in different chunks
- **Holiday details**: Holiday names separated from the hours/closures

**Example student question**: "What's the phone number for the Chicago location?"
- **Problem**: Might retrieve address chunk but not the phone chunk, or vice versa
- **Symptom**: Incomplete location information

### 5. **company_info.txt** - Facts Split From Context
- **Founded date vs history**: "Founded in 1998" separate from "over 25 years" context
- **Award year vs award name**: "2023" in one chunk, "Green Business Award" details in another
- **Numbers vs meaning**: "150+ employees" split from what they do
- **Values vs explanations**: Value name separated from what it means

**Example student question**: "How many employees does OfficeFlow have?"
- **Problem**: Might retrieve "over 150 employees" but miss context about departments
- **Symptom**: Correct but potentially incomplete answer

## Debugging Exercise Flow

### Phase 1: Observe the Problem
Students run queries and notice:
- Incomplete answers despite relevant info in knowledge base
- Agent gives partial information that requires follow-up questions
- Sometimes contradictory information (e.g., gives cost but misses "free over X")

### Phase 2: Fetch Traces with LangSmith
Using `langsmith-fetch`, students should:
```bash
langsmith-fetch traces ./investigation --limit 20 --filter "your_filter"
```

### Phase 3: Analyze Retrieved Chunks
Students examine the trace and see:
- Which chunks were retrieved (top-k results)
- Relevance scores for each chunk
- What information was in the chunks vs. what was missing
- Pattern: related info exists but didn't get retrieved together

### Phase 4: Hypothesis Testing
Students should discover:
- Chunks are exactly 200 characters (too small for complex info)
- 20-char overlap isn't enough to keep related info together
- Semantic similarity doesn't help when context is fragmented
- Some queries retrieve chunk 1 and chunk 3, missing chunk 2 that bridges them

### Phase 5: Solutions
Students learn to fix it:
1. **Increase chunk size** to 500-800 characters (keeps related info together)
2. **Increase overlap** to 50-100 characters (maintains continuity)
3. **Add better chunking strategy**: Use sentence boundaries or semantic breaks instead of character count
4. **Increase top-k** temporarily to see if info exists but isn't being retrieved
5. **Re-structure documents** with clear sections that align with likely chunk boundaries

## Key Teaching Points

1. **Chunk size matters**: Too small = fragmented context, too large = noise and cost
2. **Overlap is critical**: Prevents information from being orphaned at boundaries
3. **Document structure matters**: RAG-friendly writing keeps related info close
4. **Retrieval is only as good as chunks**: Embeddings can't fix structural problems
5. **Debugging workflow**: Observe → Fetch traces → Analyze chunks → Hypothesis → Test fix

## Expected "Aha!" Moments

- **"The info is RIGHT THERE!"**: Seeing the full document has the answer but chunking split it
- **"The overlap is too small"**: 20 chars only captures partial sentences, not semantic units
- **"200 chars is nothing"**: Realizing a single sentence can be 150+ characters
- **"We need sentence-aware chunking"**: Character count alone is too naive
- **"Different docs need different strategies"**: Contact lists vs. policy explanations need different approaches

## Realistic Chunking Parameters

After students identify the problems, guide them to realistic parameters:
- **Chunk size**: 600-1000 characters (2-4 paragraphs)
- **Overlap**: 100-150 characters (1-2 sentences)
- **Chunking strategy**: Sentence-aware or semantic section boundaries
- **Top-k**: 3-5 chunks (vs. the too-low 2 currently used)
