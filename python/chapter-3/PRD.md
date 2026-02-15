# OfficeFlow Customer Support Agent - PRD

## Purpose
Emma is an agent that helps customers with inquiries about office supplies inventory,
company policies, and general questions about OfficeFlow services.

## Core Capabilities
1. Query inventory database for product availability, pricing, and specifications
2. Search knowledge base for company policies, shipping info, and general FAQs
3. Provide accurate, helpful responses in a professional tone

## Test Scenarios

### Inventory Queries
- "Do you have any standing desks in stock?"
- "What's the price of the ErgoChair Pro?"
- "Show me all wireless keyboards under $50"

### Company Policy Questions
- "What's your return policy?"
- "How long does shipping take?"
- "Do you offer bulk discounts?"

### Mixed Queries (requires both tools)
- "I need 20 notebooks for my team, do you have them in stock and what's your bulk pricing policy?"
- "What ergonomic chairs do you have available and what's your warranty policy?"

### Edge Cases
- Questions about products not in inventory
- Vague queries requiring clarification
- Questions outside of scope (e.g., "What's the weather?")

## Success Criteria
- Correctly identifies when to use SQL tool vs semantic search
- Provides accurate information from the right data source
- Handles multi-step queries that require both tools
- Gracefully handles out-of-scope questions
- Responds in under 10 seconds for typical queries