from hiveden.api.dtos import DNSConfigResponse, DNSUpdateRequest

def test_dns_models():
    # Test Response Model
    resp = DNSConfigResponse(enabled=True, domain="test.local", container_id="123", api_key="secret-key")
    data = resp.model_dump()
    assert data['api_key'] == "secret-key"
    assert data['enabled'] is True
    
    # Test Update Request Model
    req = DNSUpdateRequest(api_key="new-key")
    assert req.api_key == "new-key"
    
    print("DNS Models verified successfully.")

if __name__ == "__main__":
    test_dns_models()
