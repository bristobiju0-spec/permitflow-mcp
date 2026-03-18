import sys
import os

# Add the current directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp_server import get_hvac_efficiency_standards, check_ca_compliance

def test_tools():
    print("Testing Regulatory Truth Server Tools...")
    
    # Test 1: get_hvac_efficiency_standards
    print("\nTest 1: get_hvac_efficiency_standards('air conditioner')")
    standards = get_hvac_efficiency_standards("air conditioner")
    print(standards)
    
    # Test 2: check_ca_compliance (Compliant)
    print("\nTest 2: check_ca_compliance (Compliant AC)")
    compliant = check_ca_compliance("air conditioner", seer2=16.0)
    print(compliant)
    
    # Test 3: check_ca_compliance (Non-Compliant)
    print("\nTest 3: check_ca_compliance (Non-Compliant AC)")
    non_compliant = check_ca_compliance("air conditioner", seer2=14.0)
    print(non_compliant)

    if standards.get("year") == "2026" and compliant.get("is_compliant") is True and non_compliant.get("is_compliant") is False:
        print("\nVerification Successful!")
    else:
        print("\nVerification Failed.")

if __name__ == "__main__":
    test_tools()
