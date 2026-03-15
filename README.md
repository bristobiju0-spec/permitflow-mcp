# 🚀 Bristo Sales Prospector
**The Autonomous Lead Research Agent for Claude.**

Bristo Sales Prospector is an MCP (Model Context Protocol) server that empowers Claude to perform deep, real-time research on B2B prospects and companies. It eliminates manual "tab-hunting" by pulling firmographics, funding data, and strategic priorities directly into your chat.

---

## 🛠 Features
- **Deep Prospecting:** Get instant summaries on individuals (roles, skills, focus).
- **Company Intelligence:** Fetch real-time data on HQ locations, employee counts, and 2026 strategic AI roadmaps.
- **Autonomous Research:** Claude can decide *when* to use this tool based on your sales-related questions.
- **Cloud Hosted:** High availability via Render.

---

## 🚀 Quick Install (Claude Code / Desktop)
Run this command in your terminal to add the agent to your Claude environment:

```bash
claude mcp add sales-pro --transport http https://sales-agent-pro.onrender.com/
```

## 💡 How to Use

Once installed, you don't need special commands. Just ask Claude naturally:

> "Research NVIDIA and tell me if they are a good lead for an AI infrastructure company."

> "I'm meeting with the CEO of Tesla tomorrow. Give me a 1-page research summary."

> "Find the employee count and recent funding for Anthropic."

## 🏗 Repository Structure

- **`.claude-plugin/`**: Official marketplace metadata and `plugin.json`.
- **`agents/`**: Contains `SKILL.md` which defines the agent's behavior and personality.
- **`mcp_server.py`**: The core Python engine (FastMCP/FastAPI) hosted on Render.
- **`demo.html`**: A local playground to test the server connection.

## 🔒 Privacy & Security

- **Data Usage**: This agent only accesses public company information.
- **No Storage**: We do not store your lead lists or chat history.
- **Transport**: All communication is handled via secure SSE (Server-Sent Events).

## 💰 Pricing

**Free Beta**: This agent is currently in free beta. No tokens or paywalls are required to use the research tools during this period.

---

## 👨💻 Author

**Bristo** – Building the future of AI-driven sales.
