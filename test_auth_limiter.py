from fastapi.testclient import TestClient
from mcp_server import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_calculate_unauthorized():
    response = client.post("/calculate", json={"test": "payload"})
    assert response.status_code == 401 # FastAPI HTTPBearer now returns 401 with auto_error=False
    
if __name__ == "__main__":
    test_health()
    test_calculate_unauthorized()
    print("All tests passed!")
