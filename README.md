# 🚀 PermitFlow Pro MCP Server
**The Autonomous Compliance & Sales Intelligence Agent.**

The PermitFlow Pro MCP (Model Context Protocol) server provides powerful tools for Claude to perform both real-time sales prospecting and complex HVAC compliance auditing. Built on FastMCP and FastAPI, it supports an agentic workflow that bridges company intelligence with regulatory logic.

---

## 🛠 Features

### Sales Intelligence
- **Deep Prospecting:** Instantly research individuals, roles, and skills.
- **Company Intelligence:** Fetch real-time firmographics and 2026 AI strategic roadmaps.

### HVAC Compliance & Audit
- **Global Compliance Engine:** Checks HVAC compliance standards for USA (EPA), EU (F-Gas), UK, and International.
- **Agentic Auditor Workflow:** Uses dual agents (Vision-to-Spec Auditor and Filer) to extract equipment metrics and verify JA18 Logic Locks.
- **Paywall & Rate Limiting:** Built-in usage limits (free vs. paid tier) protected by Supabase authentication.

---


## 💡 Available Tools

Through MCP, Claude natively integrates the following agent tools:
- `healthz`: Diagnostics to check MCP server health.
- `research_prospect`: Analyzes a prospect's role, experience, and contact probability.
- `sales_pro`: Analyzes a company's strategic focus and recent developments.
- `compliance_check`: Evaluates HVAC refrigerant compliance based on region and charge weight.
- `process_hvac_compliance_pro`: Executes a multi-agent workflow analyzing equipment imagery for compliance checks.

## 🔒 REST Endpoints & Authentication

The FastAPI server provides additional REST endpoints:
- `GET /` & `GET /health`: Diagnostic healthcheck endpoints.
- `POST /calculate`: A protected endpoint that runs the core compliance engine. It requires a valid Supabase JWT and enforces usage limits using an atomic Supabase RPC log.

---

## 🏗 Repository Structure

- **`.claude-plugin/`**: Official marketplace metadata and `plugin.json` structure.
- **`agents/`**: Contains specific agent implementations (`VisionSpecialist`, `ComplianceFilingAgent`).
- **`mcp_server.py`**: Main application file defining FastMCP tools and FastAPI routes.
- **`auth.py`**: Supabase authentication and user session security.
- **`demo.html` / `index.html`**: Front-end playgrounds to test the API visually.

---

## 👨‍💻 Author

**Bristo** – Serial AI Founder | Building the future of AI-driven compliance and sales.
