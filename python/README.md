# OfficeFlow Agent Versions - Teaching Guide

This directory contains a progression of AI agent implementations for **Emma**, a customer support agent for OfficeFlow Supply Co. Each version builds on the previous one, introducing specific improvements and demonstrating best practices for AI agent development with LangSmith observability.

## Quick Reference

| Version | Key Feature | Problem Addressed |
|---------|-------------|-------------------|
| **v0** | Baseline | None - starting point |
| **v1** | LangSmith Tracing | Can't debug agent behavior |
| **v2** | Enhanced Tool Instructions | Agent doesn't discover schema properly |
| **v3** | Stock Policy | Reveals sensitive inventory data |
| **v4** | No-Chunking RAG | Information split across chunks |

---

## Version Details

### **agent_v0.py** - Baseline Agent
**Problem:** No observability means you can't debug agent behavior or understand why it makes certain decisions.

### **agent_v1.py** - LangSmith Observability
**Improvement from v0:** Adds LangSmith tracing with `wrap_openai()` and `@traceable` decorators to make all agent decisions visible and debuggable.

**Problem:** Agent assumes it knows the database schema and writes SQL queries without discovering table structures first, leading to failed queries and incorrect assumptions about column names.

### **agent_v2.py** - Enhanced Database Tool
**Improvement from v1:** Enhanced tool description with step-by-step schema discovery instructions and SQL best practices (bilateral wildcards, case-insensitive search with `LOWER()`).

**Problem:** Agent reveals exact inventory quantities to customers ("We have 7 units"), exposing sensitive competitive data.

### **agent_v3.py** - Stock Information Policy
**Improvement from v2:** Adds system prompt policy that converts exact stock quantities into urgency signals ("in stock, but running low") to protect business intelligence while still informing customers.

**Problem:** Knowledge base retrieval returns incomplete information because critical details are split across chunk boundaries (e.g., "RMA required" in one chunk, "RMA = Return Merchandise Authorization" in another).

### **agent_v4.py** - Fixed RAG Chunking
**Improvement from v3:** Eliminates chunking entirely by embedding whole documents, ensuring complete context is always retrieved since policy documents are small enough (2-5KB) to embed atomically.