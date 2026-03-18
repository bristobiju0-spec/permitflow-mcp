import time
import sys
import os

# Add the server directory to path
sys.path.append("/home/bristo/sales-agent-pro/permitflow-mcp-server")

from mcp_server import check_ca_compliance

def test_rate_limit_and_logs():
    print("--- Testing Rate Limit & Audit Logs ---")
    
    # 1. First call (should pass)
    print("\nCall 1: Initial Compliance Check (expect PASS)")
    res1 = check_ca_compliance("air conditioner", seer2=16.0)
    print(f"Result: {res1.get('status')} (Compliant: {res1.get('is_compliant')})")
    
    # 2. Second call immediately (should hit cooldown)
    print("\nCall 2: Rapid-fire Check (expect COOLDOWN)")
    res2 = check_ca_compliance("air conditioner", seer2=16.0)
    print(f"Result: {res2.get('status')} (Seconds Remaining: {res2.get('seconds_remaining')})")
    
    # 3. Wait and check logs
    print("\nChecking Audit Logs (audit_log.db)...")
    import sqlite3
    conn = sqlite3.connect("/home/bristo/sales-agent-pro/permitflow-mcp-server/audit_log.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scan_logs ORDER BY id DESC LIMIT 5")
    logs = cursor.fetchall()
    print("Last 5 Logs:")
    for log in logs:
        print(log)
    conn.close()

    if res1.get('status') == 'APPROVED' and res2.get('status') == 'cooldown':
        print("\nBackend Verification SUCCESSFUL!")
    else:
        print("\nBackend Verification FAILED.")

if __name__ == "__main__":
    test_rate_limit_and_logs()
