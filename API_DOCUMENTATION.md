# Timetable Generator - API Documentation

## Table of Contents

1. [API Overview](#api-overview)
2. [Authentication](#authentication)
3. [Base URL & Headers](#base-url--headers)
4. [Endpoints](#endpoints)
5. [Request/Response Examples](#requestresponse-examples)
6. [Error Handling](#error-handling)
7. [Rate Limiting](#rate-limiting)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## API Overview

The Timetable Generator API is a **RESTful web service** that enables programmatic access to scheduling functionality.

### What You Can Do

- ✅ **Generate Schedules**: Submit constraints and receive an optimized schedule
- ✅ **Retrieve Schedules**: Get previously generated schedules
- ✅ **Browse History**: View all scheduling runs
- ✅ **Access Configurations**: Get saved configurations for reuse

### API Type
- **Protocol**: HTTP/HTTPS (REST)
- **Data Format**: JSON
- **Response Format**: JSON
- **Versioning**: URL-based (v1 implied)

---

## Authentication

**Current Status**: Not required (unauthenticated access allowed)

### Future Enhancements
- API Key authentication
- JWT token-based authentication
- OAuth2 support
- Rate limiting per user

**For now**: No authentication needed. Just make requests to the API.

### Security Considerations

Even without authentication, the API includes:
- ✅ CORS protection (cross-origin restrictions)
- ✅ Input validation (Pydantic models)
- ✅ Rate limiting support (can be enabled)
- ✅ SQL injection prevention

---

## Base URL & Headers

### Development Environment

```
Base URL: http://localhost:8000
```

### Production Environment

```
Base URL: https://api.yourdomain.com
```

### Required Headers

```http
Content-Type: application/json
Accept: application/json
```

### Optional Headers

```http
X-Request-ID: unique-identifier  # For tracing (optional)
Accept-Language: en-US           # For localization (future)
```

### Example Request Header

```http
POST /api/generate/ HTTP/1.1
Host: localhost:8000
Content-Type: application/json
Accept: application/json
Content-Length: 512
```

---

## Endpoints

### 1. Generate Schedule

**Create a new timetable schedule**

#### Request

```http
POST /api/generate/
Content-Type: application/json

{
  "start_time": "HH:MM",
  "end_time": "HH:MM",
  "duration": integer,
  "subjects": [...],
  "rooms": [...],
  "faculty": [...],
  "sections": [...]
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_time` | string | ✅ | Working hours start (HH:MM format, 24-hour) |
| `end_time` | string | ✅ | Working hours end (HH:MM format, 24-hour) |
| `duration` | integer | ✅ | Slot duration in minutes (typically 50) |
| `subjects` | array | ✅ | List of subject objects (min 1) |
| `rooms` | array | ✅ | List of room block objects (min 1) |
| `faculty` | array | ✅ | List of faculty objects (min 1) |
| `sections` | array | ✅ | List of section names (min 1) |

**Subject Object:**
```json
{
  "name": "string",       // Unique subject name
  "credits": "integer",   // Course load (3, 4, 5)
  "is_lab": "boolean"     // True if lab, false if lecture
}
```

**Room Object:**
```json
{
  "block": "string",      // Building identifier (e.g., "A", "B")
  "start": "integer",     // Room number range start (e.g., 101)
  "end": "integer"        // Room number range end (e.g., 110)
}
```

**Faculty Object:**
```json
{
  "name": "string",           // Faculty member name
  "subjects": ["string"]      // List of subject names they teach
}
```

#### Response (Success)

**Status**: 200 OK

```json
{
  "schedule": [
    {
      "id": "unique-id",
      "section": "CS-1A",
      "day": "Monday",
      "start_time": "09:00",
      "end_time": "10:30",
      "subject": "Mathematics",
      "teacher": "Dr. Smith",
      "room": "101",
      "credits": 3,
      "total_credits": 3,
      "duration": 2
    },
    ...
  ],
  "time_slots": [
    "09:00",
    "09:50",
    "10:40",
    ...
  ]
}
```

**Response Field Descriptions:**

| Field | Type | Description |
|-------|------|-------------|
| `schedule` | array | Array of class assignments |
| `schedule[].id` | string | Unique identifier for this assignment |
| `schedule[].section` | string | Student section name |
| `schedule[].day` | string | Day of week (Monday-Friday) |
| `schedule[].start_time` | string | Class start time (HH:MM) |
| `schedule[].end_time` | string | Class end time (HH:MM) |
| `schedule[].subject` | string | Subject name |
| `schedule[].teacher` | string | Faculty name |
| `schedule[].room` | string | Room number |
| `schedule[].credits` | integer | Credit load |
| `schedule[].total_credits` | integer | Total credits (may differ from input) |
| `schedule[].duration` | integer | Number of time slots occupied |
| `time_slots` | array | Array of all available time slots |

#### Response (Error)

**Status**: 400 Bad Request

```json
{
  "detail": "Solver failed to find a valid schedule."
}
```

**Other Possible Errors:**

```json
{
  "detail": "Invalid input data: subjects must not be empty"
}
```

#### Example cURL

```bash
curl -X POST http://localhost:8000/api/generate/ \
  -H "Content-Type: application/json" \
  -d '{
    "start_time": "09:00",
    "end_time": "17:00",
    "duration": 50,
    "subjects": [
      {
        "name": "Mathematics",
        "credits": 3,
        "is_lab": false
      },
      {
        "name": "Physics Lab",
        "credits": 4,
        "is_lab": true
      }
    ],
    "rooms": [
      {
        "block": "A",
        "start": 101,
        "end": 110
      },
      {
        "block": "B",
        "start": 201,
        "end": 210
      }
    ],
    "faculty": [
      {
        "name": "Dr. Smith",
        "subjects": ["Mathematics", "Physics Lab"]
      },
      {
        "name": "Dr. Johnson",
        "subjects": ["Physics Lab"]
      }
    ],
    "sections": ["CS-1A", "CS-1B", "CS-1C"]
  }'
```

#### Example Python (requests library)

```python
import requests
import json

url = "http://localhost:8000/api/generate/"

payload = {
    "start_time": "09:00",
    "end_time": "17:00",
    "duration": 50,
    "subjects": [
        {
            "name": "Mathematics",
            "credits": 3,
            "is_lab": False
        }
    ],
    "rooms": [
        {
            "block": "A",
            "start": 101,
            "end": 110
        }
    ],
    "faculty": [
        {
            "name": "Dr. Smith",
            "subjects": ["Mathematics"]
        }
    ],
    "sections": ["CS-1A", "CS-1B"]
}

headers = {
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)
schedule = response.json()

if response.status_code == 200:
    print(f"Generated {len(schedule['schedule'])} classes")
    for slot in schedule['schedule']:
        print(f"{slot['section']} - {slot['day']} {slot['start_time']}: {slot['subject']}")
else:
    print(f"Error: {schedule['detail']}")
```

#### Example JavaScript (fetch API)

```javascript
const generateSchedule = async (payload) => {
  const response = await fetch('http://localhost:8000/api/generate/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }

  return await response.json();
};

// Usage
const schedule = await generateSchedule({
  start_time: "09:00",
  end_time: "17:00",
  duration: 50,
  subjects: [{ name: "Math", credits: 3, is_lab: false }],
  rooms: [{ block: "A", start: 101, end: 110 }],
  faculty: [{ name: "Dr. Smith", subjects: ["Math"] }],
  sections: ["CS-1A"]
});

console.log(schedule);
```

---

### 2. Get Latest Schedule

**Retrieve the most recently generated schedule**

#### Request

```http
GET /api/latest/
```

**Parameters**: None

#### Response (Success)

**Status**: 200 OK

```json
{
  "schedule": [
    {
      "id": "CS-1A-Math-001",
      "section": "CS-1A",
      "day": "Monday",
      "start_time": "09:00",
      "end_time": "10:30",
      "subject": "Mathematics",
      "teacher": "Dr. Smith",
      "room": "101",
      "credits": 3,
      "total_credits": 3,
      "duration": 2
    },
    ...
  ],
  "time_slots": ["09:00", "09:50", "10:40", ...]
}
```

#### Response (No Schedule Found)

**Status**: 200 OK

```json
{
  "schedule": [],
  "time_slots": []
}
```

#### Example cURL

```bash
curl http://localhost:8000/api/latest/
```

#### Example Python

```python
import requests

response = requests.get("http://localhost:8000/api/latest/")
data = response.json()

if data['schedule']:
    print(f"Found {len(data['schedule'])} classes")
else:
    print("No schedule generated yet")
```

---

### 3. Get History

**Retrieve all previously generated schedules**

#### Request

```http
GET /api/history/
```

**Parameters**: None

#### Response (Success)

**Status**: 200 OK

```json
[
  {
    "id": 1,
    "total_classes": 45,
    "config_id": 1,
    "created_at": "2026-03-25T10:30:00Z"
  },
  {
    "id": 2,
    "total_classes": 52,
    "config_id": 2,
    "created_at": "2026-03-24T14:15:00Z"
  },
  ...
]
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Unique run identifier |
| `total_classes` | integer | Number of classes in this schedule |
| `config_id` | integer | Configuration used for generation |
| `created_at` | string | ISO 8601 timestamp |

#### Example cURL

```bash
curl http://localhost:8000/api/history/
```

#### Example Python

```python
import requests

response = requests.get("http://localhost:8000/api/history/")
runs = response.json()

for run in runs:
    print(f"Run {run['id']}: {run['total_classes']} classes ({run['created_at']})")
```

---

### 4. Get Specific Run

**Retrieve a specific historical schedule by run ID**

#### Request

```http
GET /api/history/{run_id}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `run_id` | integer | ✅ | ID returned from /api/history/ |

#### Response (Success)

**Status**: 200 OK

```json
{
  "schedule": [
    {
      "id": "CS-1A-Math-001",
      "section": "CS-1A",
      "day": "Monday",
      "start_time": "09:00",
      "end_time": "10:30",
      "subject": "Mathematics",
      "teacher": "Dr. Smith",
      "room": "101",
      "credits": 3,
      "total_credits": 3,
      "duration": 2
    },
    ...
  ],
  "time_slots": ["09:00", "09:50", ...]
}
```

#### Response (Error - Run Not Found)

**Status**: 200 OK (empty schedule)

```json
{
  "schedule": [],
  "time_slots": []
}
```

#### Example cURL

```bash
curl http://localhost:8000/api/history/1
```

#### Example Python

```python
import requests

run_id = 1
response = requests.get(f"http://localhost:8000/api/history/{run_id}")
data = response.json()

print(f"Schedule for run {run_id}:")
for slot in data['schedule']:
    print(f"  {slot['section']} - {slot['day']} {slot['start_time']}: {slot['subject']}")
```

---

## Request/Response Examples

### Complete Workflow Example

#### 1. Generate a New Schedule

```bash
curl -X POST http://localhost:8000/api/generate/ \
  -H "Content-Type: application/json" \
  -d '{
    "start_time": "09:00",
    "end_time": "17:00",
    "duration": 50,
    "subjects": [
      {"name": "Mathematics", "credits": 3, "is_lab": false},
      {"name": "Physics", "credits": 3, "is_lab": false},
      {"name": "Chemistry Lab", "credits": 4, "is_lab": true}
    ],
    "rooms": [
      {"block": "A", "start": 101, "end": 110},
      {"block": "B", "start": 201, "end": 210}
    ],
    "faculty": [
      {
        "name": "Dr. Alice Smith",
        "subjects": ["Mathematics", "Physics"]
      },
      {
        "name": "Dr. Bob Johnson",
        "subjects": ["Physics", "Chemistry Lab"]
      },
      {
        "name": "Dr. Carol White",
        "subjects": ["Chemistry Lab"]
      }
    ],
    "sections": ["CS-3A", "CS-3B", "CS-3C"]
  }'
```

**Response:**
```json
{
  "schedule": [
    {
      "id": "CS-3A-Math-001",
      "section": "CS-3A",
      "day": "Monday",
      "start_time": "09:00",
      "end_time": "10:30",
      "subject": "Mathematics",
      "teacher": "Dr. Alice Smith",
      "room": "102",
      "credits": 3,
      "duration": 2
    },
    {
      "id": "CS-3A-Physics-001",
      "section": "CS-3A",
      "day": "Tuesday",
      "start_time": "09:00",
      "end_time": "10:30",
      "subject": "Physics",
      "teacher": "Dr. Bob Johnson",
      "room": "105",
      "credits": 3,
      "duration": 2
    },
    ...
  ],
  "time_slots": [
    "09:00", "09:50", "10:40", "11:30", "13:00", "13:50", "14:40", "15:30"
  ]
}
```

#### 2. Retrieve Latest Schedule

```bash
curl http://localhost:8000/api/latest/
```

**Response:** (Same format as above)

#### 3. Check History

```bash
curl http://localhost:8000/api/history/
```

**Response:**
```json
[
  {
    "id": 5,
    "total_classes": 87,
    "config_id": 5,
    "created_at": "2026-03-25T10:30:45.123456Z"
  },
  {
    "id": 4,
    "total_classes": 84,
    "config_id": 4,
    "created_at": "2026-03-25T09:15:30.456789Z"
  },
  ...
]
```

#### 4. Retrieve Specific Run

```bash
curl http://localhost:8000/api/history/5
```

**Response:** (Full schedule for run 5)

---

## Error Handling

### HTTP Status Codes

| Status | Meaning | Example Scenario |
|--------|---------|-----------------|
| **200** | Success | Schedule generated successfully |
| **400** | Bad Request | Invalid input format, solver failed |
| **404** | Not Found | Requested run_id doesn't exist |
| **500** | Server Error | Database error, unexpected exception |
| **503** | Service Unavailable | Server/Supabase down |

### Error Response Format

All errors return JSON:

```json
{
  "detail": "Human-readable error description"
}
```

### Common Error Messages

#### 1. Invalid Input

```json
{
  "detail": "Invalid input data: start_time must be HH:MM format"
}
```

**Causes:**
- Time format incorrect (should be "HH:MM")
- Numeric fields as strings
- Missing required fields

**Solution:** Check payload structure against API documentation

#### 2. Solver Failed

```json
{
  "detail": "Solver failed to find a valid schedule."
}
```

**Causes:**
- More classes than available slots
- Constraints mathematically impossible
- Faculty shortage for required subjects

**Solution:** 
- Add more time slots (extend hours or add days)
- Add more faculty or rooms
- Reduce number of subjects/sections

#### 3. Database Error

```json
{
  "detail": "Database connection failed"
}
```

**Causes:**
- Supabase not reachable
- Invalid credentials
- Rate limit exceeded

**Solution:**
- Check internet connection
- Verify SUPABASE_URL and SUPABASE_KEY
- Wait and retry

#### 4. Server Error

```json
{
  "detail": "Internal server error"
}
```

**Causes:**
- Unexpected exception
- Code bug
- Resource exhaustion

**Solution:**
- Check server logs
- Retry the request
- Report issue on GitHub

---

## Rate Limiting

### Current Status
**Not implemented** - No rate limits currently

### Future Implementation

When rate limiting is added:

```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1648120000

{
  "detail": "Rate limit exceeded. Try again in 60 seconds"
}
```

**Typical Limits (when implemented):**
- 100 requests per hour per IP
- 5 concurrent /api/generate/ requests
- 10 MB max request size

---

## Best Practices

### 1. Input Validation

Always validate your data before sending:

```python
def validate_payload(payload):
    # Check required fields
    assert 'start_time' in payload, "start_time required"
    assert 'sections' in payload, "sections required"
    
    # Check format
    import re
    time_pattern = r'^\d{2}:\d{2}$'
    assert re.match(time_pattern, payload['start_time']), "Invalid time format"
    
    # Check ranges
    assert payload['duration'] > 0, "duration must be positive"
    assert len(payload['sections']) > 0, "at least one section required"
    
    return True
```

### 2. Error Handling

Implement robust error handling:

```python
import requests
from requests.exceptions import RequestException, Timeout

def generate_schedule(payload, timeout=30):
    try:
        response = requests.post(
            'http://localhost:8000/api/generate/',
            json=payload,
            timeout=timeout
        )
        response.raise_for_status()  # Raise for 4xx/5xx
        return response.json()
    
    except Timeout:
        raise Exception("Request timed out - solver taking too long")
    except requests.ConnectionError:
        raise Exception("Cannot connect to API server")
    except requests.HTTPError as e:
        error_data = e.response.json()
        raise Exception(f"API Error: {error_data.get('detail', str(e))}")
    except Exception as e:
        raise Exception(f"Unexpected error: {str(e)}")
```

### 3. Retrying Failed Requests

Implement backoff strategy:

```python
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_retry_session(retries=3, backoff_factor=0.3):
    session = requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=(500, 502, 504)
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

session = create_retry_session()
response = session.post('http://localhost:8000/api/generate/', json=payload)
```

### 4. Pagination (for large datasets)

When retrieving history with many runs:

```python
def get_history_paginated(page_size=50):
    """Get history in chunks"""
    page = 0
    while True:
        response = requests.get(
            f'http://localhost:8000/api/history/?page={page}&limit={page_size}'
        )
        data = response.json()
        
        if not data:
            break
        
        yield from data
        page += 1
```

### 5. Caching Results

Cache API responses to reduce load:

```python
from functools import lru_cache
import time

@lru_cache(maxsize=128)
def get_latest_schedule(cache_key=None):
    """Cache latest schedule for 5 minutes"""
    response = requests.get('http://localhost:8000/api/latest/')
    return response.json()

# Clear cache periodically
# In production, use redis or memcached instead
```

### 6. Logging

Log all API interactions:

```python
import logging

logger = logging.getLogger('timetable_api')

def log_api_call(method, endpoint, status_code, duration):
    logger.info(
        f"{method} {endpoint} -> {status_code} ({duration:.2f}s)"
    )

# Usage
start = time.time()
response = requests.post(url, json=payload)
duration = time.time() - start
log_api_call('POST', '/api/generate/', response.status_code, duration)
```

---

## Troubleshooting

### Issue: Connection Refused

```
Error: Connection refused
Traceback: Cannot connect to http://localhost:8000
```

**Causes:**
- Backend not running
- Wrong port (8000)
- Firewall blocking

**Solution:**
```bash
# Check if backend is running
curl http://localhost:8000/docs

# If not, start backend
cd backend && uvicorn main:app --reload

# Check port
netstat -ano | findstr :8000
```

### Issue: Invalid JSON Response

```
json.JSONDecodeError: Expecting value: line 1 column 1
Response text: <html><body>Internal Server Error</body></html>
```

**Causes:**
- Server returned HTML error page (500 error)
- Malformed response

**Solution:**
```python
response = requests.get(url)
if response.headers.get('content-type') != 'application/json':
    print(f"Invalid content-type: {response.headers.get('content-type')}")
    print(f"Response: {response.text[:500]}")
else:
    data = response.json()
```

### Issue: 415 Unsupported Media Type

```
Error 415: Unsupported Media Type
```

**Causes:**
- Missing Content-Type header
- Wrong Content-Type value

**Solution:**
```bash
# Always include this header
curl -H "Content-Type: application/json" ...

# Verify:
curl -v ...  # Shows all headers
```

### Issue: Solver Timeout

```
{
  "detail": "Solver exceeded timeout limit"
}
```

**Causes:**
- Large/complex scheduling problem
- Default timeout too short

**Solution:**
```python
# Increase timeout
response = requests.post(
    url,
    json=payload,
    timeout=60  # 60 seconds instead of 30
)
```

---

## Interactive API Documentation

### Swagger UI

When backend is running, visit:

```
http://localhost:8000/docs
```

**Features:**
- ✅ Try endpoints directly from browser
- ✅ See request/response examples
- ✅ Validate payloads
- ✅ View all parameters

### ReDoc

Alternative documentation format:

```
http://localhost:8000/redoc
```

---

## OpenAPI Specification

Get raw OpenAPI spec:

```bash
curl http://localhost:8000/openapi.json
```

Use with:
- Postman: Import JSON
- Insomnia: Import JSON
- Code generation tools (generate client libraries)

---

## Changelog

### Version 1.0 (Current)
- ✅ POST /api/generate/ - Create schedule
- ✅ GET /api/latest/ - Retrieve latest
- ✅ GET /api/history/ - List all runs
- ✅ GET /api/history/{run_id} - Get specific run

### Version 1.1 (Planned)
- 🚀 Authentication (JWT tokens)
- 🚀 Rate limiting
- 🚀 Filtering & sorting
- 🚀 WebSocket for real-time updates

---

**Last Updated**: March 2026
**API Version**: 1.0
**Status**: Stable
