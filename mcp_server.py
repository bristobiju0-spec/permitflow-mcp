import json
import logging
from typing import Optional

from mcp.server.fastmcp import FastMCP

# Initialize FastMCP Server
mcp = FastMCP("Lead Generation Agent")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("lead-gen")

@mcp.tool()
def research_prospect(name: str, company: Optional[str] = None) -> str:
    """
    Simulates a search for a prospect's LinkedIn data.
    
    Args:
        name: Full name of the prospect.
        company: Optional. The company the prospect works for.
        
    Returns:
        A formatted summary of the prospect's mock professional profile.
    """
    logger.info(f"Researching prospect: {name} at {company or 'Unknown Company'}")
    
    # Mock data generation based on inputs
    company_name = company if company else "Tech Innovations Inc."
    role = "Senior Engineering Lead" if "tech" in company_name.lower() else "VP of Sales"
    
    mock_profile = {
        "name": name,
        "company": company_name,
        "current_role": role,
        "years_of_experience": 8,
        "key_skills": ["Leadership", "Strategic Planning", "B2B Sales" if role == "VP of Sales" else "System Architecture"],
        "recent_activity": f"Recently posted about scaleable solutions at {company_name}.",
        "contact_probability": "High",
        "email_format": f"{name.split(' ')[0].lower()}.{name.split(' ')[-1].lower()}@{company_name.lower().replace(' ', '')}.com"
    }

    summary = (
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
    
    return summary

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    if os.environ.get("RENDER"):
        logger.info(f"Starting Lead Generation MCP Server on Render (SSE, port {port})...")
        mcp.run(transport="sse", host="0.0.0.0", port=port)
    else:
        logger.info("Starting Lead Generation MCP Server locally...")
        mcp.run()
