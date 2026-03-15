import json
import logging
from typing import Optional, List
import os
from fastmcp import FastMCP
from fastapi import FastAPI
import uvicorn

# Initialize FastMCP Server with lowercase 'sales-pro' slug
# The name here is used for logging and internal identification
mcp = FastMCP("sales-pro")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sales-pro-gen")

# --- Tools Definition ---

@mcp.tool()
def healthz() -> str:
    """
    Check the health of the MCP server tools.
    """
    return "OK"

@mcp.tool()
def research_prospect(name: str, company: Optional[str] = None) -> str:
    """
    Simulates a search for a prospect's LinkedIn data.
    """
    logger.info(f"Researching prospect: {name} at {company or 'Unknown Company'}")
    company_name = company if company else "Tech Innovations Inc."
    role = "Senior Engineering Lead" if "tech" in company_name.lower() else "VP of Sales"
    
    mock_profile = {
        "name": name,
        "company": company_name,
        "current_role": role,
        "years_of_experience": 8,
        "key_skills": ["Leadership", "Strategic Planning", "System Architecture" if role != "VP of Sales" else "B2B Sales"],
        "recent_activity": f"Recently posted about scaleable solutions at {company_name}.",
        "contact_probability": "High",
        "email_format": f"{name.split(' ')[0].lower()}.{name.split(' ')[-1].lower()}@{company_name.lower().replace(' ', '')}.com"
    }

    return (
        f"Prospect Profile Summary: {mock_profile['name']}\n"
        f"--------------------------------------------------\n"
        f"Current Role: {mock_profile['current_role']} at {mock_profile['company']}\n"
        f"Experience: ~{mock_profile['years_of_experience']} years\n"
        f"Key Skills: {', '.join(mock_profile['key_skills'])}\n"
        f"Recent Activity: {mock_profile['recent_activity']}\n"
        f"--------------------------------------------------\n"
        f"Lead Gen Assessment:\n"
        f"- Contact Probability: {mock_profile['contact_probability']}\n"
        f"- Estimated Email: {mock_profile['email_format']}\n"
    )

@mcp.tool()
def sales_pro(company_name: str) -> str:
    """
    Researches a company's strategic focus and recent AI developments.
    """
    logger.info(f"Researching company: {company_name}")
    if "google" in company_name.lower():
        return (
            "Google AI Strategic Focus (2026 Roadmap Summary):\n"
            "--------------------------------------------------\n"
            "1. Agentic AI: Maturation of autonomous agents capable of planning and executing multi-step tasks.\n"
            "2. Infrastructure: Gigawatt-scale data centers and custom TPU expansion for Gemini training.\n"
            "3. Gemini Evolution: Continued reasoning enhancements and full replacement of Google Assistant.\n"
            "4. Robotics: Embodied AI and humanoid foundation models from DeepMind.\n"
            "5. Search Transformation: Shift from link-based retrieval to a synthesized answer engine.\n"
            "--------------------------------------------------\n"
            "Market Position: Leading in pervasive integration and agentic capabilities across Workspace and Android."
        )
    return f"Researching {company_name}... Found: HQ in SF, 500 employees, recently focused on scaling AI infrastructure."

# --- FastAPI Integration & Deployment ---

app = FastAPI()

@app.get("/")
async def root():
    """
    Root diagnostic route for browser verification.
    """
    return {"status": "online", "mcp": "ready"}

@app.get("/health")
async def health():
    """
    Automated health check route for Render and xpay.sh.
    """
    return {"status": "ready"}

# Mount FastMCP at the root path (/)
mcp.mount(app, path="/")

if __name__ == "__main__":
    # Render uses port 10000 by default
    port = int(os.getenv("PORT", 10000))
    logger.info(f"Starting 'sales-pro' MCP Server on port {port} at root path (/)")
    uvicorn.run(app, host="0.0.0.0", port=port)
