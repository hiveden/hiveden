from hiveden.api.dtos import DNSConfigResponse

def test_model():
    resp = DNSConfigResponse(enabled=True, domain="test.local", container_id="123")
    print(resp.model_dump_json(indent=2))
    
    resp2 = DNSConfigResponse(enabled=False)
    print(resp2.model_dump_json(indent=2))

if __name__ == "__main__":
    test_model()
