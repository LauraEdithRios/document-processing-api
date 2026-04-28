# API Documentation — Document Processing API

Base URL: `http://localhost:8000`  
Interactive docs (Swagger UI): `http://localhost:8000/docs`  
OpenAPI JSON: `http://localhost:8000/openapi.json`

---

## Authentication

No authentication required. All endpoints are publicly accessible.

---

## Common Response Codes

| Code | Meaning |
|---|---|
| `200 OK` | Request succeeded |
| `201 Created` | Resource created successfully |
| `404 Not Found` | Process ID does not exist |
| `422 Unprocessable Entity` | Invalid input (e.g. malformed UUID) |
| `500 Internal Server Error` | Unexpected server error |

---

## Schemas

### ProcessResponse

Returned by most endpoints that operate on a single process.

```json
{
  "process_id":           "string (UUID)",
  "status":               "PENDING | RUNNING | PAUSED | COMPLETED | FAILED | STOPPED",
  "progress": {
    "total_files":        "integer",
    "processed_files":    "integer",
    "percentage":         "integer (0–100)"
  },
  "started_at":           "ISO 8601 datetime | null",
  "completed_at":         "ISO 8601 datetime | null",
  "estimated_completion": "ISO 8601 datetime | null",
  "results":              "ProcessResultResponse | null"
}
```

### ProcessResultResponse

Present in `results` once status is `COMPLETED`.

```json
{
  "total_words":          "integer",
  "total_lines":          "integer",
  "total_characters":     "integer",
  "most_frequent_words":  ["string"],
  "files_processed":      ["string"],
  "summary":              "string | null"
}
```

### ProcessListItemResponse

Returned by `GET /process/list`.

```json
{
  "process_id":   "string (UUID)",
  "status":       "string",
  "progress":     "ProgressResponse",
  "created_at":   "ISO 8601 datetime",
  "started_at":   "ISO 8601 datetime | null",
  "completed_at": "ISO 8601 datetime | null"
}
```

---

## Endpoints

---

### POST /process/start

Start a new document processing job. Creates the process record, schedules the worker in a background thread, and returns immediately.

**Request body:** none

**Response `201 Created`**

```json
{
  "process_id": "7f438c06-a983-4d6f-89b7-2d512cd4f643",
  "status": "PENDING",
  "progress": { "total_files": 0, "processed_files": 0, "percentage": 0 },
  "started_at": null,
  "completed_at": null,
  "estimated_completion": null,
  "results": null
}
```

**Notes**
- The returned status may already be `RUNNING` depending on thread scheduling latency.
- `estimated_completion` is calculated from elapsed time per file once at least one file has been processed.

---

### GET /process/list

Return all processes ordered by creation time descending (newest first).

**Response `200 OK`** — array of `ProcessListItemResponse`

```json
[
  {
    "process_id": "7f438c06-a983-4d6f-89b7-2d512cd4f643",
    "status": "RUNNING",
    "progress": { "total_files": 10, "processed_files": 3, "percentage": 30 },
    "created_at": "2026-04-28T11:30:00Z",
    "started_at": "2026-04-28T11:30:00Z",
    "completed_at": null
  }
]
```

Returns `[]` if no processes exist.

---

### GET /process/status/{process_id}

Get the current status and progress of a specific process.

**Path parameters**

| Parameter | Type | Description |
|---|---|---|
| `process_id` | UUID string | ID of the process |

**Response `200 OK`** — `ProcessResponse`

**Response `404 Not Found`**
```json
{ "detail": "Process not found" }
```

**Response `422 Unprocessable Entity`**
```json
{ "detail": "process_id con formato inválido" }
```

---

### GET /process/results/{process_id}

Get the full result payload including analysis data.

**Path parameters**

| Parameter | Type | Description |
|---|---|---|
| `process_id` | UUID string | ID of the process |

**Response `200 OK`** — `ProcessResponse` with `results` populated when `status == COMPLETED`

```json
{
  "process_id": "7f438c06-a983-4d6f-89b7-2d512cd4f643",
  "status": "COMPLETED",
  "progress": { "total_files": 10, "processed_files": 10, "percentage": 100 },
  "started_at": "2026-04-28T11:30:00Z",
  "completed_at": "2026-04-28T11:30:45Z",
  "estimated_completion": null,
  "results": {
    "total_words": 18432,
    "total_lines": 743,
    "total_characters": 112850,
    "most_frequent_words": ["the", "and", "of", "to", "in"],
    "files_processed": ["Antimatter.txt", "Dark Matter.txt", "..."],
    "summary": "Antimatter.txt: <first 3 sentences>..."
  }
}
```

**Response `404 Not Found`**
```json
{ "detail": "Process not found" }
```

---

### POST /process/stop/{process_id}

Stop a process that is `RUNNING`, `PENDING`, or `PAUSED`. The worker exits at the next file boundary.

**Path parameters**

| Parameter | Type | Description |
|---|---|---|
| `process_id` | UUID string | ID of the process to stop |

**Response `200 OK`** — `ProcessResponse` with `status: "STOPPED"`

**Response `404 Not Found`**

Returned when the process does not exist or is already in a terminal state.

```json
{ "detail": "Process not found" }
```

---

### POST /process/pause/{process_id}

Pause a `RUNNING` process. The worker completes the current file then blocks until resumed.

**Path parameters**

| Parameter | Type | Description |
|---|---|---|
| `process_id` | UUID string | ID of the process to pause |

**Response `200 OK`** — `ProcessResponse` with `status: "PAUSED"`

**Response `404 Not Found`**

Returned when the process does not exist or is not `RUNNING`.

```json
{ "detail": "Process not found or not running" }
```

---

### POST /process/resume/{process_id}

Resume a `PAUSED` process.

**Path parameters**

| Parameter | Type | Description |
|---|---|---|
| `process_id` | UUID string | ID of the process to resume |

**Response `200 OK`** — `ProcessResponse` with `status: "RUNNING"`

**Response `404 Not Found`**

Returned when the process does not exist or is not `PAUSED`.

```json
{ "detail": "Process not found or not paused" }
```

---

### GET /process/logs/{process_id}

Return the activity log entries for a process in chronological order.

**Path parameters**

| Parameter | Type | Description |
|---|---|---|
| `process_id` | UUID string | ID of the process |

**Response `200 OK`**

```json
[
  { "message": "Process created with PENDING status", "created_at": "2026-04-28T11:30:00.123456" },
  { "message": "Process started in background",       "created_at": "2026-04-28T11:30:00.145000" },
  { "message": "Process completed successfully",      "created_at": "2026-04-28T11:30:45.678900" }
]
```

Log levels recorded: `INFO`, `WARNING`, `ERROR`.

**Response `404 Not Found`**
```json
{ "detail": "Process not found" }
```

---

### DELETE /process/clear

Delete all processes in a terminal state (`COMPLETED`, `FAILED`, `STOPPED`) along with their results and activity logs. Active processes are not affected.

**Response `200 OK`**

```json
{ "deleted": 12 }
```

Returns `{ "deleted": 0 }` if no finished processes exist.

---

### GET /health

Health check.

**Response `200 OK`**
```json
{ "status": "UP" }
```

---

## WebSocket

### WS /process/ws/{process_id}

Subscribe to real-time updates for a specific process.

**Connection URL**

```
ws://localhost:8000/process/ws/{process_id}
```

**Server → Client message types**

Progress update (after each file is processed):

```json
{
  "type": "progress",
  "status": "RUNNING",
  "progress": { "total_files": 10, "processed_files": 4, "percentage": 40 }
}
```

Status transition (on start and on terminal state):

```json
{
  "type": "status",
  "status": "COMPLETED",
  "progress": { "total_files": 10, "processed_files": 10, "percentage": 100 }
}
```

**Client behavior**

Close the connection when `status` is `COMPLETED`, `FAILED`, or `STOPPED`. The server does not close it automatically.

**Notes**

- Multiple clients can subscribe to the same `process_id` simultaneously.
- Messages are not buffered. Only events after the connection is established are delivered.
- If the process finishes before the client connects, poll `GET /process/status/{process_id}` instead.

---

## Error Handling

All error responses follow FastAPI's default format:

```json
{ "detail": "Human-readable error message" }
```

`ValueError` exceptions from the service layer are caught globally and returned as `422 Unprocessable Entity`. All errors are logged server-side in structured JSON format.
