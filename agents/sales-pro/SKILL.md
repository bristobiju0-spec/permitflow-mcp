---
name: Bristo Sales Prospector
description: An autonomous agent for deep-researching B2B leads. Finds HQ, employee counts, and funding data.
---

# Bristo Sales Prospector Skill

This skill allows the agent to use the Sales-Prospector-Pro MCP Server to gather deep prospect research and company strategic insights.

## How to Use

1. **Setup**: `pip install -r requirements.txt`
2. **Launch**: `python mcp_server.py`
3. **Connect**: Connect via Claude using the provided MCP URL.

## Available Tools

- `research_prospect`: Research a specific person at a company.
    - `name` (string): Full name.
    - `company` (string, optional): Company name.
- `sales_pro`: Research a company's strategic AI focus (2026 Roadmap).
    - `company_name` (string): Target company.

This agent provides premium, formatted summaries designed for sales outreach preparation.
