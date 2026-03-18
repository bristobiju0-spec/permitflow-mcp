import logging
import os
from typing import Dict, Any, Optional
from fastmcp import FastMCP
from fastapi import FastAPI
import uvicorn
import sqlite3
import time
from datetime import datetime

# Initialize FastMCP Server
mcp = FastMCP("regulatory-truth")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("regulatory-truth")

# --- Audit Persistence ---
# SUPABASE RLS & EDGE FUNCTION BRIDGE (VIBE OPTIMIZATION)
# To keep the 8GB RAM server lightweight, use Supabase Row Level Security (RLS)
# Example RLS Policy for scan_logs:
#   CREATE POLICY "Users can only see their own scans" 
#   ON public.scan_logs FOR SELECT 
#   USING (auth.uid() = user_id);
#
# PADDLE SYNC:
#   Edge Function 'paddle-webhook' listens for subscription.created
#   Updates public.users.is_pro = true based on passthrough=user_id
#   This replaces a heavy local background worker.

def init_db():
    conn = sqlite3.connect("audit_log.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scan_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            equipment_type TEXT,
            seer2 REAL,
            status TEXT,
            user_email TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_account (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signup_date TEXT,
            credits_used INTEGER DEFAULT 0,
            email TEXT UNIQUE,
            supabase_id TEXT UNIQUE
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def log_scan(equipment_type, seer2, status, user_email="guest@permitflow.pro"):
    conn = sqlite3.connect("audit_log.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO scan_logs (timestamp, equipment_type, seer2, status, user_email) VALUES (?, ?, ?, ?, ?)",
                   (datetime.now().isoformat(), equipment_type, seer2, status, user_email))
    last_row_id = cursor.lastrowid
    
    # Increment credits for this specific user
    cursor.execute("UPDATE user_account SET credits_used = credits_used + 1 WHERE email = ?", (user_email,))
    
    conn.commit()
    conn.close()
    return f"PF-{last_row_id:05d}"

# --- Rate Limit Logic ---
LAST_CALL_TIME = 0
RATE_LIMIT_SECONDS = 10

def check_rate_limit():
    global LAST_CALL_TIME
    current_time = time.time()
    elapsed = current_time - LAST_CALL_TIME
    if elapsed < RATE_LIMIT_SECONDS:
        remaining = int(RATE_LIMIT_SECONDS - elapsed)
        return False, remaining
    LAST_CALL_TIME = current_time
    return True, 0

# --- Regulatory Data (Mocked for 2026 Standards) ---

STANDARDS_2026 = {
    "residential": {
        "air_conditioner": {
            "min_seer2": 15.0,
            "min_eer2": 10.0
        },
        "heat_pump": {
            "min_seer2": 14.3,
            "min_hspf2": 7.5
        }
    }
}

# --- Tools Definition ---

@mcp.tool()
def get_hvac_efficiency_standards(equipment_type: str, usage: str = "residential") -> Dict[str, Any]:
    """
    Returns the latest 2025/2026 CEC efficiency standards for a given equipment type.
    """
    logger.info(f"Fetching standards for {equipment_type} ({usage})")
    
    usage_data = STANDARDS_2026.get(usage.lower(), {})
    standards = usage_data.get(equipment_type.lower().replace(" ", "_"), {})
    
    if not standards:
        return {"error": f"No standards found for '{equipment_type}' in {usage} usage."}
    
    return {
        "year": "2026",
        "standard_source": "CEC Title 24 Part 6",
        "equipment_type": equipment_type,
        "usage": usage,
        "required_metrics": standards
    }

@mcp.tool()
def check_ca_compliance(equipment_type: str, seer2: float, hspf2: Optional[float] = None) -> Dict[str, Any]:
    """
    Checks if a specific piece of equipment complies with the 2026 California Energy Code.
    """
    allowed, remaining = check_rate_limit()
    if not allowed:
        return {
            "status": "cooldown",
            "seconds_remaining": remaining,
            "error": f"Rate limit exceeded. Cooling down for {remaining}s."
        }

    logger.info(f"Checking compliance for {equipment_type}: SEER2={seer2}, HSPF2={hspf2}")
    
    standards_resp = get_hvac_efficiency_standards(equipment_type)
    if "error" in standards_resp:
        return standards_resp
        
    required = standards_resp["required_metrics"]
    is_compliant = True
    reasons = []
    
    # SEER2 check
    if seer2 < required.get("min_seer2", 0):
        is_compliant = False
        reasons.append(f"SEER2 {seer2} is below the required {required['min_seer2']}")
        
    # HSPF2 check (if applicable)
    if hspf2 is not None and "min_hspf2" in required:
        if hspf2 < required["min_hspf2"]:
            is_compliant = False
            reasons.append(f"HSPF2 {hspf2} is below the required {required['min_hspf2']}")
            
    res = {
        "is_compliant": is_compliant,
        "equipment_type": equipment_type,
        "provided_specs": {"seer2": seer2, "hspf2": hspf2},
        "required_specs": required,
        "violations": reasons,
        "status": "APPROVED" if is_compliant else "REJECTED",
        "code_section": "Title 24, Part 6, Section 150.1(c)" if is_compliant else "Non-compliant with CEC 2026"
    }
    
    res["verification_id"] = log_scan(equipment_type, seer2, res["status"])
    return res

# --- FastAPI Integration ---

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok", "server": "Regulatory Truth"}

@app.post("/logs")
async def save_log(data: Dict[str, Any]):
    user_email = data.get("user_email", "guest@permitflow.pro")
    equipment_type = data.get("equipment_type", "Unknown")
    seer2 = data.get("seer2", 0.0)
    status = data.get("status", "REJECTED")
    
    verification_id = log_scan(equipment_type, seer2, status, user_email)
    return {"status": "success", "verification_id": verification_id}

@app.get("/logs")
async def get_logs(email: str = "guest@permitflow.pro", status: Optional[str] = None, search: Optional[str] = None):
    conn = sqlite3.connect("audit_log.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = "SELECT * FROM scan_logs WHERE user_email = ?"
    params = [email]
    
    if status == "APPROVED":
        query += " AND status = 'APPROVED'"
    elif status == "REJECTED":
        query += " AND status = 'REJECTED'"
        
    if search:
        query += " AND equipment_type LIKE ?"
        params.append(f"%{search}%")
        
    query += " ORDER BY id DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

@app.get("/user")
async def get_user(email: str = "guest@permitflow.pro", supabase_id: Optional[str] = None):
    conn = sqlite3.connect("audit_log.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM user_account WHERE email = ?", (email,))
    row = cursor.fetchone()
    
    if not row:
        # Auto-signup logic for Magic Link vibe
        cursor.execute("INSERT INTO user_account (signup_date, credits_used, email, supabase_id) VALUES (?, ?, ?, ?)",
                       (datetime.now().isoformat(), 0, email, supabase_id))
        conn.commit()
        cursor.execute("SELECT * FROM user_account WHERE email = ?", (email,))
        row = cursor.fetchone()
        
    user = dict(row)
    conn.close()
    
    # Beta Logic
    signup_date = datetime.fromisoformat(user["signup_date"])
    days_since_signup = (datetime.now() - signup_date).days
    credits_used = int(user["credits_used"])
    
    is_subscription_required = credits_used >= 10 or days_since_signup > 30
    
    return {
        "email": user["email"],
        "credits_used": credits_used,
        "credits_remaining": max(0, 10 - credits_used),
        "days_remaining": max(0, 30 - days_since_signup),
        "is_subscription_required": is_subscription_required,
        "signup_date": user["signup_date"]
    }

mcp.mount(app)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10001))
    logger.info(f"Starting Regulatory Truth Server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
