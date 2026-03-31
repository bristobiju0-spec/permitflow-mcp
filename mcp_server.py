import json
import logging
from typing import Optional, List
import os
from fastmcp import FastMCP
from fastapi import FastAPI
import uvicorn
import asyncio
from agents.vision_specialist import VisionSpecialist
from agents.compliance_filing_agent import ComplianceFilingAgent

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

@mcp.tool()
def compliance_check(region: str, refrigerant: str, charge_weight_lbs: float) -> str:
    """
    Checks HVAC compliance based on region, refrigerant type, and charge weight.
    Regions: USA (EPA), Europe (EU F-Gas), UK, International.
    """
    logger.info(f"Compliance check for {region} | {refrigerant} | {charge_weight_lbs} lbs")
    
    refrigerants_gwp = {
        "R-410A": 2088,
        "R-134a": 1430,
        "R-404A": 3922,
        "R-32": 675,
        "R-454B": 466
    }
    
    gwp = refrigerants_gwp.get(refrigerant, 2088)
    is_compliant = True
    note = "Unit meets standard compliance requirements."
    code_section = "General Standard"
    
    if region == "USA (EPA)":
        if charge_weight_lbs >= 15:
            is_compliant = False
            note = "⚠️ EPA MANDATE: Annual leak inspection and mandatory 30-day repair required."
            code_section = "EPA 608 (15lb Rule)"
    elif region in ["Europe (EU F-Gas)", "UK"]:
        # Convert lbs to kg
        kg = charge_weight_lbs * 0.453592
        tonnes_co2e = (kg * gwp) / 1000
        if tonnes_co2e >= 5:
            is_compliant = False
            note = "⚠️ EU F-GAS MANDATE: Mandatory leak check every 12 months required."
            code_section = "F-Gas Regulation (EU 517/2014)" if region == "Europe (EU F-Gas)" else "UK F-Gas Regulation"
            
    return json.dumps({
        "is_compliant": is_compliant,
        "note": note,
        "code_section": code_section,
        "region": region,
        "details": {
            "gwp": gwp,
            "charge_lbs": charge_weight_lbs,
            "charge_kg": charge_weight_lbs * 0.453592 if "kg" not in note else None,
            "co2e_tonnes": (charge_weight_lbs * 0.453592 * gwp / 1000) if region in ["Europe (EU F-Gas)", "UK"] else None
        }
    }, indent=2)

@mcp.tool()
async def process_hvac_compliance_pro(equipment_image_b64: str, roof_image_b64: Optional[str] = None) -> str:
    """
    Refined Agent Manager Workflow:
    1. Runs Vision-to-Spec Auditor (Agent 1) to extract 2026 metrics & check Heat Pump mandate. 
    2. Vision Agent writes site_specs.json.
    3. Runs Compliance & Filing Agent (Agent 2) to check JA18 locks and simulate browser filing.
    4. Agents are designed to run in parallel where dependencies allow.
    """
    logger.info("Starting Refined HVAC Dual-Agent Workflow...")
    
    auditor = VisionSpecialist()
    filer = ComplianceFilingAgent()
    
    # Step 1: Run Auditor (Agent 1)
    # In a real async environment, we could gather multiple extractions
    try:
        audit_result = auditor.auditor_workflow(equipment_image_b64, roof_image_b64)
    except Exception as e:
        logger.error(f"Auditor failed: {str(e)}")
        return f"Agent 1 Error: {str(e)}"

    # Step 2: Run Filer (Agent 2) - Ingests site_specs.json
    try:
        filing_result = filer.filer_workflow()
    except Exception as e:
        logger.error(f"Filer failed: {str(e)}")
        return f"Agent 2 Error: {str(e)}"
    
    # Step 3: Synthesis
    specs = audit_result["site_specs"]
    summary = (
        "🏗️ Refined HVAC Compliance & Filing Summary\n"
        "==========================================\n"
        f"Manufacturer: {specs.get('manufacturer')} | Model: {specs.get('model_number')}\n"
        f"2026 Metrics: SEER2={specs.get('seer2')}, EER2={specs.get('eer2')}, HSPF2={specs.get('hspf2')}\n"
        "------------------------------------------\n"
        "🛡️ Compliance Audit (Agent 1):\n"
        f"- Heat Pump Mandate: {'✅ OK' if audit_result['compliance_audit']['is_compliant'] else '⚠️ WARNING'}\n"
        f"  Note: {audit_result['compliance_audit']['note']}\n"
        f"- SARA Estimate: {audit_result['sara_assessment']['estimated_sara_sqft']} sqft\n"
        "------------------------------------------\n"
        "📂 Filing & Regulatory (Agent 2):\n"
        f"- JA18 Logic Lock: {'✅ VERIFIED' if filing_result['ja18_compliance']['is_locked'] else '❌ MISSING'}\n"
        f"  Note: {filing_result['ja18_compliance']['note']}\n"
        f"- Filing Status: {filing_result['filing_status']['status']} ({filing_result['filing_status']['portal']})\n"
        "------------------------------------------\n"
        "✅ Workflow Complete. site_specs.json generated and forms populated.\n"
        "Review Screenshot: [Ready_to_Submit_Artifact](file:///tmp/filing_screenshot.png)"
    )
    
    return summary

# --- FastAPI Integration & Deployment ---

app = FastAPI()

@app.get("/")
async def root():
    """
    Root diagnostic route for Render and xpay health checks.
    """
    return {"status": "ok"}

@app.get("/health")
async def health():
    """
    Secondary health check route.
    """
    return {"status": "ready"}

# Mount FastMCP without the 'path' argument (it is not supported in this version)
mcp.mount(app)

if __name__ == "__main__":
    # Render requires binding to 0.0.0.0 and using the PORT env var
    port = int(os.getenv("PORT", 10000))
    logger.info(f"Starting 'sales-pro' MCP Server on host 0.0.0.0 port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
