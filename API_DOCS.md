# API Documentation — Document Processing System

## Base URL


http://localhost:8000


## Interactive Documentation

FastAPI generates automatic interactive docs at runtime:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Common Response Schemas

### ProcessResponse

Returned by `/start`, `/stop`, `/status`, and `/results`.

| Field | Type | Description |
|-------|------|-------------|
| `process_id` | `string (UUID)` | Unique process identifier |
| `status` | `string` | Current state (see [Process States](#process-states)) |
| `progress` | `ProgressResponse` | File processing counters |
| `started_at` | `datetime \| null` | UTC timestamp when processing started |
| `estimated_completion` | `datetime \| null` | Always `null` in current version |
| `results` | `ProcessResultResponse \| null` | Populated only when status is `COMPLETED` |

### ProgressResponse

| Field | Type | Description |
|-------|------|-------------|
| `total_files` | `integer` | Total `.txt` files found |
| `processed_files` | `integer` | Files successfully processed |
| `percentage` | `integer` | Completion percentage (0–100) |

### ProcessResultResponse

| Field | Type | Description |
|-------|------|-------------|
| `total_words` | `integer` | Combined word count across all files |
| `total_lines` | `integer` | Combined line count |
| `total_characters` | `integer` | Combined character count |
| `most_frequent_words` | `string[]` | Top 5 most frequent words |
| `files_processed` | `string[]` | Names of successfully processed files |
| `summary` | `string \| null` | First 3 sentences of each processed file |

### ProcessListItemResponse

Returned by `/list`.

| Field | Type | Description |
|-------|------|-------------|
| `process_id` | `string (UUID)` | Unique process identifier |
| `status` | `string` | Current state |
| `progress` | `ProgressResponse` | File processing counters |
| `created_at` | `datetime` | UTC timestamp of process creation |
| `started_at` | `datetime \| null` | UTC timestamp when processing started |
| `completed_at` | `datetime \| null` | UTC timestamp when process ended |

### Error Response

| Field | Type | Description |
|-------|------|-------------|
| `detail` | `string` | Human-readable error message |

---

## Process States

| State | Description |
|-------|-------------|
| `PENDING` | Process created, waiting to start |
| `RUNNING` | Processing documents |
| `COMPLETED` | Finished successfully |
| `FAILED` | Terminated with error |
| `STOPPED` | Manually stopped |

---

## Endpoints

### `GET /health`

Health check.

**Response `200 OK`**

```json
{
  "status": "UP"
}
```

---

### `POST /process/start`

Creates and immediately starts a new document analysis process. The process is created with status `PENDING` and the analysis runs asynchronously in the background.

**Request body:** None

**Response `201 Created`** — `ProcessResponse`

```json
{
  "process_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "PENDING",
  "progress": {
    "total_files": 0,
    "processed_files": 0,
    "percentage": 0
  },
  "started_at": null,
  "estimated_completion": null,
  "results": null
}
```

> `results` is `null` at creation time. Query `/results/{process_id}` once the process reaches `COMPLETED`.

---

### `GET /process/status/{process_id}`

Returns the current state and progress of a process.

**Path parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `process_id` | `string (UUID)` | Yes | Process identifier |

**Response `200 OK`** — `ProcessResponse`

```json
{
  "process_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "RUNNING",
  "progress": {
    "total_files": 10,
    "processed_files": 4,
    "percentage": 40
  },
  "started_at": "2024-01-15T10:30:00.000000Z",
  "estimated_completion": null,
  "results": null
}
```

**Response `404 Not Found`**

```json
{ "detail": "Process not found" }
```

**Response `422 Unprocessable Entity`** — Invalid UUID format

```json
{ "detail": "process_id con formato inválido" }
```

---

### `GET /process/list`

Returns all processes ordered by creation date (most recent first).

**Response `200 OK`** — `ProcessListItemResponse[]`

```json
[
  {
    "process_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "status": "COMPLETED",
    "progress": {
      "total_files": 10,
      "processed_files": 10,
      "percentage": 100
    },
    "created_at": "2024-01-15T10:29:50.000000Z",
    "started_at": "2024-01-15T10:30:00.000000Z",
    "completed_at": "2024-01-15T10:30:45.000000Z"
  }
]
```

Returns an empty array `[]` if no processes exist.

---

### `POST /process/stop/{process_id}`

Stops a process. Only processes in `PENDING` or `RUNNING` state can be stopped. Processes already in `COMPLETED`, `FAILED`, or `STOPPED` state return `404`.

**Path parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `process_id` | `string (UUID)` | Yes | Process identifier |

**Request body:** None

**Response `200 OK`** — `ProcessResponse`

```json
{
  "process_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "STOPPED",
  "progress": {
    "total_files": 10,
    "processed_files": 3,
    "percentage": 30
  },
  "started_at": "2024-01-15T10:30:00.000000Z",
  "estimated_completion": null,
  "results": null
}
```

**Response `404 Not Found`** — Process not found or not in a stoppable state

```json
{ "detail": "Process not found" }
```

---

### `GET /process/results/{process_id}`

Returns the process state plus analysis results. The `results` field is populated only when the process has reached `COMPLETED` status.

**Path parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `process_id` | `string (UUID)` | Yes | Process identifier |

**Response `200 OK`** — `ProcessResponse`

```json
{
  "process_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "COMPLETED",
  "progress": {
    "total_files": 10,
    "processed_files": 10,
    "percentage": 100
  },
  "started_at": "2024-01-15T10:30:00.000000Z",
  "estimated_completion": null,
  "results": {
    "total_words": 12450,
    "total_lines": 620,
    "total_characters": 78300,
    "most_frequent_words": ["the", "of", "and", "to", "a"],
    "files_processed": [
      "Antimatter.txt",
      "Dark Matter.txt",
      "Jules Verne.txt"
    ],
    "summary": "Antimatter.txt: Antimatter is composed of antiparticles...\nDark Matter.txt: Dark matter is a hypothetical form..."
  }
}
```

**Response `404 Not Found`**

```json
{ "detail": "Process not found" }
```

**Response `422 Unprocessable Entity`** — Invalid UUID format

```json
{ "detail": "process_id con formato inválido" }
```

---

### `GET /process/logs/{process_id}`

Returns the activity log of a process, ordered chronologically.

**Path parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `process_id` | `string (UUID)` | Yes | Process identifier |

**Response `200 OK`** — `LogEntry[]`

```json
[
  {
    "message": "Process created with PENDING status",
    "created_at": "2024-01-15T10:29:50.000000Z"
  },
  {
    "message": "Process started in background",
    "created_at": "2024-01-15T10:30:00.000000Z"
  },
  {
    "message": "Process completed successfully",
    "created_at": "2024-01-15T10:30:45.000000Z"
  }
]
```

**Response `404 Not Found`**

```json
{ "detail": "Process not found" }
```

---

## HTTP Status Code Summary

| Code | Meaning |
|------|---------|
| `200 OK` | Request succeeded |
| `201 Created` | Process created successfully |
| `404 Not Found` | Process does not exist or is not in a valid state for the operation |
| `422 Unprocessable Entity` | Invalid UUID format or validation error |
| `500 Internal Server Error` | Unexpected server error |

---

## Typical Usage Flow

```
1. POST /process/start          → receive process_id (status: PENDING)
2. GET  /process/status/{id}    → poll until status is COMPLETED or FAILED
3. GET  /process/results/{id}   → retrieve analysis results
4. GET  /process/logs/{id}      → inspect activity log
```

To stop a running process:

```
POST /process/stop/{id}         → status transitions to STOPPED
```
