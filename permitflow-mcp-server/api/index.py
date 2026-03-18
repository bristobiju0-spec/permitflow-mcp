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
    
    # User Accounts
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
    
    # Add email if not exists (for migrations)
    try:
        cursor.execute("ALTER TABLE user_account ADD COLUMN email TEXT UNIQUE")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE user_account ADD COLUMN is_pro INTEGER DEFAULT 0")
    except:
        pass
        
    conn.commit()
    conn.close()

# Initialize on startup (Vercel may re-run this)
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
    credits_used = user_data['credits_used']
    signup_dt = datetime.fromisoformat(user_data['signup_date'])
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
        cursor.execute("""
            INSERT INTO scan_logs 
            (user_email, timestamp, model, seer2, type, verification_id, status, violation, is_compliant, gps)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('user_email'),
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
                       (data.get('user_email'),))
        
        conn.commit()
        return {"success": True, "id": cursor.lastrowid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/logs")
async def get_logs(email: str = None):
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
