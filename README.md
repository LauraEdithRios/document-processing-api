# Document Processing API

Asynchronous document processing system built with FastAPI. Reads and analyzes a collection of text files, tracking each job's progress in real time through a REST API, WebSocket updates, and a browser-based dashboard.

---

## Features

- **Async processing** — each job runs in a background thread so the API stays responsive
- **Full lifecycle control** — start, pause, resume, and stop any job at any time
- **Real-time progress** — WebSocket pushes per-file progress to connected clients
- **Persistent state** — SQLite stores every process, result, and activity log
- **Web dashboard** — single-page UI with live progress bars, status indicators, detail panel, and activity log
- **Structured logging** — JSON-formatted logs on every HTTP request and worker event
- **Docker ready** — single `docker compose up` to run the full stack

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.136 |
| Server | Uvicorn (with `websockets` for WS support) |
| ORM | SQLAlchemy 2.0 |
| Database | SQLite (WAL mode) |
| Validation | Pydantic v2 |
| Real-time | WebSocket (native FastAPI) |
| Testing | pytest + httpx |
| Container | Docker / Docker Compose |

---

## Project Structure

```
document-processing-api/
├── app/
│   ├── main.py                    # FastAPI app, lifespan, middleware, routes
│   ├── api/
│   │   └── v1/
│   │       └── process.py         # All HTTP and WebSocket endpoints
│   ├── core/
│   │   ├── database.py            # SQLAlchemy engine (WAL mode) + session
│   │   ├── logging_config.py      # JSON structured logging
│   │   ├── process_signals.py     # Thread-safe pause/resume/shutdown signals
│   │   └── ws_manager.py          # WebSocket connection manager
│   ├── models/
│   │   ├── process.py             # Process table
│   │   ├── process_result.py      # Analysis results table
│   │   ├── activity_log.py        # Per-process activity log table
│   │   └── process_status.py      # Status enum
│   ├── schemas/
│   │   └── process.py             # Pydantic request/response schemas
│   ├── services/
│   │   └── process_service.py     # Business logic and orchestration
│   ├── repositories/
│   │   └── process_repository.py  # All database queries
│   └── workers/
│       └── document_worker.py     # Text file analysis engine
├── data/
│   └── texts/                     # Input text files (10 sample documents)
├── static/
│   └── index.html                 # Web dashboard (vanilla JS, no build step)
├── tests/
│   ├── conftest.py
│   └── test_process_api.py
├── storage/                       # Created at runtime — holds the SQLite DB
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Setup

### Prerequisites

- Python 3.11+
- pip

### Local installation

```bash
# Clone the repository
git clone <repository-url>
cd document-processing-api

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt
pip install websockets            # Required for WebSocket support
```

### Run the server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.  
The dashboard is served at `http://localhost:8000/`.

To slow down processing and observe real-time progress, set the delay between files:

```bash
# Linux / macOS
WORKER_FILE_DELAY=1 uvicorn app.main:app --reload

# Windows PowerShell
$env:WORKER_FILE_DELAY="1"; uvicorn app.main:app --reload
```

---

## Docker

### Build and run

```bash
docker compose up --build
```

The API is exposed on port `8000`. The Docker Compose file sets `WORKER_FILE_DELAY=0.5` by default and mounts two volumes:

| Volume | Purpose |
|---|---|
| `db_data` | Persists the SQLite database across container restarts |
| `./data/texts` | Mounts the sample text files into the container |

### Stop

```bash
docker compose down
```

---

## API Reference

All endpoints are prefixed with `/process`.

### Start a process

```
POST /process/start
```

Creates a new job and immediately begins processing documents in the background.

**Response `201`**

```json
{
  "process_id": "7f438c06-a983-4d6f-89b7-2d512cd4f643",
  "status": "PENDING",
  "progress": {
    "total_files": 0,
    "processed_files": 0,
    "percentage": 0
  },
  "started_at": null,
  "completed_at": null,
  "estimated_completion": null,
  "results": null
}
```

---

### List all processes

```
GET /process/list
```

Returns all processes ordered from newest to oldest.

**Response `200`** — array of process summaries including `created_at`, `started_at`, and `completed_at`.

---

### Get process status

```
GET /process/status/{process_id}
```

Returns the current state and progress of a single process.

---

### Get process results

```
GET /process/results/{process_id}
```

Returns the full response including analysis results once the process is `COMPLETED`.

**Response `200`**

```json
{
  "process_id": "...",
  "status": "COMPLETED",
  "progress": { "total_files": 10, "processed_files": 10, "percentage": 100 },
  "started_at": "2026-04-28T11:30:00Z",
  "completed_at": "2026-04-28T11:30:45Z",
  "results": {
    "total_words": 18432,
    "total_lines": 743,
    "total_characters": 112850,
    "most_frequent_words": ["the", "and", "of", "to", "in"],
    "files_processed": ["Antimatter.txt", "Dark Matter.txt", "..."],
    "summary": "..."
  }
}
```

---

### Stop a process

```
POST /process/stop/{process_id}
```

Stops a `RUNNING`, `PENDING`, or `PAUSED` process. The worker exits cleanly at the next file boundary.

---

### Pause a process

```
POST /process/pause/{process_id}
```

Pauses a `RUNNING` process. The worker blocks between files until resumed.

---

### Resume a process

```
POST /process/resume/{process_id}
```

Resumes a `PAUSED` process.

---

### Get activity log

```
GET /process/logs/{process_id}
```

Returns the ordered list of log entries for a process.

**Response `200`**

```json
[
  { "message": "Process created with PENDING status", "created_at": "2026-04-28T11:30:00Z" },
  { "message": "Process started in background",       "created_at": "2026-04-28T11:30:00Z" },
  { "message": "Process completed successfully",      "created_at": "2026-04-28T11:30:45Z" }
]
```

---

### Clear finished processes

```
DELETE /process/clear
```

Deletes all `COMPLETED`, `FAILED`, and `STOPPED` processes along with their results and logs. Active processes (`RUNNING`, `PENDING`, `PAUSED`) are not affected.

**Response `200`**

```json
{ "deleted": 12 }
```

---

### Health check

```
GET /health
```

```json
{ "status": "UP" }
```

---

## WebSocket

```
WS /process/ws/{process_id}
```

Subscribe to live updates for a specific process. The server pushes a JSON message on each status change and after each file is processed.

**Progress message**

```json
{
  "type": "progress",
  "status": "RUNNING",
  "progress": {
    "total_files": 10,
    "processed_files": 3,
    "percentage": 30
  }
}
```

**Status change message**

```json
{
  "type": "status",
  "status": "COMPLETED",
  "progress": {
    "total_files": 10,
    "processed_files": 10,
    "percentage": 100
  }
}
```

The client closes the connection once a terminal status (`COMPLETED`, `FAILED`, `STOPPED`) is received.

---

## Process States

```
PENDING ──► RUNNING ──► COMPLETED
               │
               ├──► PAUSED ──► RUNNING
               │
               └──► STOPPED

         (error) ──► FAILED
```

| Status | Description |
|---|---|
| `PENDING` | Job created, worker not yet started |
| `RUNNING` | Worker is actively processing files |
| `PAUSED` | Worker is blocked, waiting for resume signal |
| `STOPPED` | Manually stopped by the user |
| `COMPLETED` | All files processed successfully |
| `FAILED` | Unhandled exception during processing |

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `WORKER_FILE_DELAY` | `0` | Seconds to wait after processing each file. Useful for observing real-time progress. |

---

## Document Analysis

The worker processes every `.txt` file found in `data/texts/` and computes:

| Metric | Description |
|---|---|
| Total words | Alphabetic tokens of 2+ characters (case-insensitive) |
| Total lines | Line count including blank lines |
| Total characters | Raw character count |
| Top 5 words | Most frequent words across all documents combined |
| Summary | First 3 sentences extracted from each document |

Files are processed in configurable batches (default: 2 files per batch). The pause signal is checked before each file so the worker can stop or pause cleanly without leaving partial results.

---

## Approach & Design Decisions

### Layered architecture

The codebase is split into four explicit layers: API handlers → Service → Repository → Models. Each layer has a single responsibility. Handlers only parse HTTP input and format responses. The service owns business logic and orchestration. The repository owns all SQL queries. This separation makes each layer independently testable and replaceable.

### SQLite with WAL mode

SQLite was chosen for zero-infrastructure simplicity — no external database server required. WAL (Write-Ahead Logging) mode was enabled to allow concurrent reads and writes without contention: in the default journal mode, a background thread committing after each file holds an EXCLUSIVE lock that blocks any simultaneous HTTP read, causing `OperationalError: database is locked`. WAL eliminates this by allowing readers to proceed without waiting for writers.

### Real threading for background workers

FastAPI's `BackgroundTasks` runs synchronous functions in a thread pool via `run_in_threadpool`. This means the worker executes in a real OS thread, fully decoupled from the asyncio event loop. Blocking operations — file I/O, `time.sleep` for the configurable delay — do not affect API responsiveness.

### threading.Event for pause/resume signals

A `threading.Event` per process provides a clean, low-overhead way to block the worker between files. The worker calls `event.wait(timeout=0.5)` in a short loop rather than a single blocking `wait()`. The timeout ensures the worker can detect a shutdown signal even while paused, preventing the thread from hanging indefinitely when the server restarts.

A centralized `process_signals` module manages all active events. On application shutdown (FastAPI lifespan teardown), `process_signals.shutdown()` sets all events, unblocking every paused worker so threads exit cleanly.

### Cross-thread WebSocket broadcasting

WebSocket connections live in the asyncio event loop; the worker runs in a separate thread. `WSManager.broadcast_from_thread` uses `asyncio.run_coroutine_threadsafe` to safely schedule `send_json` on the main event loop from the worker thread without requiring locks or queues.

### WebSocket + polling hybrid on the frontend

WebSocket delivers per-file progress with minimal latency. A 500 ms polling fallback runs in parallel, ensuring the UI stays consistent if the WebSocket connection drops, hasn't connected yet, or if a process was started from another client. The two mechanisms are additive: the poll re-renders from authoritative database state; the WS provides smoother in-between updates.

### Vanilla JS frontend

No framework, no bundler, no build step. The entire dashboard is a single HTML file served by FastAPI's `StaticFiles`. This minimises operational complexity while still delivering a functional real-time UI with WebSocket integration, event delegation, and CSS animations.

---

## Key Findings & Technical Considerations

### SQLite locking under concurrent access

Without WAL mode, the background worker's `db.commit()` after each file holds an EXCLUSIVE lock for a few milliseconds. If an HTTP request reads the database during that window it fails with `OperationalError: database is locked`. This is not visible in unit tests (which use a single-threaded in-memory DB) but manifests immediately under real concurrent usage.

### Server hang on reload with a paused process

A paused worker calls `threading.Event.wait()` with no timeout. When uvicorn reloads (e.g. `--reload` mode detects a file change), the lifespan teardown runs but the paused thread never exits, causing the server to hang. The fix has two parts: use `wait(timeout=0.5)` in a loop so the thread periodically checks for shutdown, and call `process_signals.shutdown()` in the lifespan `finally` block to forcibly set all events.

### WebSocket timing race on process creation

If the client connects a WebSocket immediately after the POST that creates a process — before the list refresh has rendered the row in the DOM — every incoming WS message calls `updateRow` on a non-existent element. All updates are silently dropped. The fix is to connect the WebSocket inside `renderList`, after the row exists, rather than in the `startProcess` handler.

### Action buttons destroyed mid-click by DOM replacement

Replacing a button's outer HTML while the browser is still processing a click event causes the click handler to fire on a detached element. The fix is to only replace action buttons when the process status actually changes, not on every WebSocket progress message.

### fetch() cache and stale list responses

Without explicit `Cache-Control` headers on the API, some browsers may serve a cached response for `GET /process/list`. This means the list appears empty after creating a process, even though the server has the record. Adding `cache: 'no-store'` to every `fetch()` call forces a fresh network request.

---

## Running Tests

```bash
pytest tests/ -v
```

Tests use an in-memory SQLite database injected via a fixture in `conftest.py`, so they run in complete isolation with no disk side effects.

---

## Web Dashboard

Served at `http://localhost:8000/`, the dashboard provides:

- **Process table** — live status, animated progress bar, start time, completion time, and duration for every job
- **Action buttons** — Pause, Resume, and Stop controls for active processes
- **Detail panel** — click any row to see full statistics (words, lines, characters, files), top words, and the timestamped activity log
- **Start Process** — creates a new job and auto-scrolls to it with the detail panel open
- **Clear finished** — removes all completed, stopped, and failed processes in one click

The UI is implemented in plain HTML/CSS/JavaScript with no build step or external dependencies. Real-time updates are delivered via WebSocket with a 500 ms polling fallback for resilience.
