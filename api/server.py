import os
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Vercel Runtime Setup
app = FastAPI()

# Configure CORS for Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastmcp import FastMCP

# Initialize FastMCP Server
mcp = FastMCP("regulatory-truth")

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
    
    return res

# --- Audit Persistence (SQLite fallback / Supabase Concept) ---
DATABASE = "/tmp/audit_log.db" if os.environ.get("VERCEL") else "audit_log.db"

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Audit Logs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scan_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            timestamp TEXT,
            model TEXT,
            seer2 REAL,
            type TEXT,
            verification_id TEXT,
            status TEXT,
            violation TEXT,
            is_compliant INTEGER,
            gps TEXT
        )
    """)
    
    # User Accounts (Consolidated)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_account (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            supabase_id TEXT,
            signup_date TEXT,
            credits_used INTEGER DEFAULT 0,
            is_pro INTEGER DEFAULT 0
        )
    """)
        
    conn.commit()
    conn.close()

# Initialize on startup
if not os.path.exists(DATABASE) or os.environ.get("VERCEL"):
    init_db()

@app.get("/")
async def root():
    return {"status": "PermitFlow Pro Engine Online", "runtime": "Vercel Serverless"}

@app.get("/user")
async def get_user_account(email: str = "guest@permitflow.pro"):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM user_account WHERE email = ?", (email,))
    row = cursor.fetchone()
    
    if not row:
        # Auto-signup vibe
        signup_date = datetime.now().isoformat()
        cursor.execute("INSERT INTO user_account (email, signup_date, credits_used) VALUES (?, ?, ?)", 
                       (email, signup_date, 0))
        conn.commit()
        cursor.execute("SELECT * FROM user_account WHERE email = ?", (email,))
        row = cursor.fetchone()

    user_data = dict(row)
    conn.close()
    
    # Beta Logic
    credits_used = int(user_data['credits_used'])
    signup_dt = datetime.fromisoformat(str(user_data['signup_date']))
    days_since_signup = (datetime.now() - signup_dt).days
    
    is_subscription_required = credits_used >= 10 or days_since_signup > 30
    if user_data['is_pro']: is_subscription_required = False

    return {
        "email": user_data['email'],
        "credits_used": credits_used,
        "credits_remaining": max(0, 10 - credits_used),
        "days_since_signup": days_since_signup,
        "is_subscription_required": is_subscription_required,
        "is_pro": bool(user_data['is_pro'])
    }

@app.post("/logs")
async def log_scan(request: Request):
    data = await request.json()
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    try:
        user_email = data.get('user_email', 'guest@permitflow.pro')
        
        # Verify or Create User
        cursor.execute("SELECT id FROM user_account WHERE email = ?", (user_email,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO user_account (email, signup_date) VALUES (?, ?)", 
                           (user_email, datetime.now().isoformat()))

        cursor.execute("""
            INSERT INTO scan_logs 
            (user_email, timestamp, model, seer2, type, verification_id, status, violation, is_compliant, gps)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_email,
            data.get('timestamp', datetime.now().isoformat()),
            data.get('model'),
            data.get('seer2'),
            data.get('type'),
            data.get('verification_id'),
            data.get('status'),
            data.get('violation'),
            1 if data.get('is_compliant') else 0,
            data.get('gps')
        ))
        
        # Increment credits if not pro
        cursor.execute("UPDATE user_account SET credits_used = credits_used + 1 WHERE email = ? AND is_pro = 0", 
                       (user_email,))
        
        conn.commit()
        return {"success": True, "id": cursor.lastrowid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/logs")
async def get_logs(email: Optional[str] = None):
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if email:
        cursor.execute("SELECT * FROM scan_logs WHERE user_email = ? ORDER BY timestamp DESC", (email,))
    else:
        cursor.execute("SELECT * FROM scan_logs ORDER BY timestamp DESC LIMIT 50")
        
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# Mount MCP
mcp.mount(app)
