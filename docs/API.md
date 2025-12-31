# 🔌 REST API Documentation

**Base URL:** `http://localhost:5000`

## 📊 Data Endpoints

### `GET /api/devices`
```json
[
  {
    "device_id": "uuid",
    "device_hash": "sha256",
    "os": "Windows",
    "browser": "Chrome",
    "risk_score": 85.2,
    "risk_level": "high",
    "is_vpn": true
  }
]

Params: page=1, per_page=20

GET /api/accounts

[
  {
    "account_id": "uuid",
    "account_hash": "sha256",
    "kyc_level": "verified",
    "risk_score": 23.4,
    "device_count": 3
  }
]

GET /api/graph-data

D3.js network data

{
  "nodes": [...],
  "links": [...]
}

Params: limit=100

⚡ Action Endpoints

POST /api/calculate-risk

// Request
{
  "device_id": "uuid-here"
}

// Response
{
  "risk_score": 78.5,
  "risk_level": "high",
  "factors": {...}
}

🧪 Test Commands

curl http://localhost:5000/api/devices | jq '.'
curl http://localhost:5000/api/graph-data?limit=50 | jq '{nodes: length(.nodes)}'
curl http://localhost:5000/health
