import json
from mcp_server import compliance_check

def test_compliance():
    print("Testing Global Compliance Logic...")
    
    # Test USA (EPA) - Pass
    res = json.loads(compliance_check("USA (EPA)", "R-410A", 10.0))
    print(f"USA 10lbs: {'PASS' if res['is_compliant'] else 'FAIL'}")
    assert res['is_compliant'] == True

    # Test USA (EPA) - Fail (15lb rule)
    res = json.loads(compliance_check("USA (EPA)", "R-410A", 16.0))
    print(f"USA 16lbs: {'PASS' if res['is_compliant'] else 'FAIL'} - {res['note']}")
    assert res['is_compliant'] == False

    # Test Europe (EU F-Gas) - Pass
    # 2kg R-410A = 2 * 2088 / 1000 = 4.17 tonnes CO2e (< 5)
    res = json.loads(compliance_check("Europe (EU F-Gas)", "R-410A", 4.4)) # ~2kg
    print(f"EU 2kg R-410A: {'PASS' if res['is_compliant'] else 'FAIL'}")
    assert res['is_compliant'] == True

    # Test Europe (EU F-Gas) - Fail
    # 5kg R-410A = 5 * 2088 / 1000 = 10.44 tonnes CO2e (> 5)
    res = json.loads(compliance_check("Europe (EU F-Gas)", "R-410A", 11.0)) # ~5kg
    print(f"EU 5kg R-410A: {'PASS' if res['is_compliant'] else 'FAIL'} - {res['note']}")
    assert res['is_compliant'] == False

    print("\nAll compliance tests passed!")

if __name__ == "__main__":
    test_compliance()
