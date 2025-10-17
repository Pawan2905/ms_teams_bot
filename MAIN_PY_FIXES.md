# main.py Fixes and Improvements

## Issues Fixed

### 1. Missing Import
**Problem:** `asyncio` was used but not imported (line 145, 241)

**Fixed:** Added `import asyncio` at the top of the file

### 2. Duplicate Exception Handlers
**Problem:** The `process_query` function had overlapping try-except blocks causing syntax errors

**Fixed:** Removed duplicate exception handlers and properly structured the try-except block

### 3. Problematic Import
**Problem:** Imported `update_jira_documents` and `update_confluence_documents` from `update_vector_store.py` which would cause circular dependency issues

**Fixed:** Removed the import - these functions should only be used in standalone scripts

### 4. Unused Model
**Problem:** `UpdateRequest` model was defined but not used anywhere

**Fixed:** Removed the unused model to clean up the code

### 5. Overly Complex Startup Event
**Problem:** The startup event tried to set up APScheduler with complex cron parsing, but:
- APScheduler was not in requirements.txt
- Referenced non-existent `settings.refresh_schedule_cron`
- Better to use OS-level scheduling (cron/Task Scheduler)

**Fixed:** Simplified startup event to just:
- Log application startup
- Check vector store document count
- Provide helpful warning if vector store is empty
- Log API documentation URL

## New Features Added

### 1. Status Endpoint
Added a new `/status` endpoint that returns:
- Application running status
- Vector store document count
- Whether vector store is ready (has documents)
- Jira configuration status
- Confluence configuration status
- Default project/space keys

**Usage:**
```bash
curl http://localhost:8000/status
```

**Response:**
```json
{
  "status": "running",
  "vector_store": {
    "document_count": 150,
    "ready": true
  },
  "integrations": {
    "jira_configured": true,
    "confluence_configured": true,
    "default_jira_project": "PROJ",
    "default_confluence_space": "TEAM"
  }
}
```

## Current main.py Structure

### API Endpoints:
1. **GET /health** - Simple health check
2. **GET /status** - Detailed status including vector store and configuration
3. **POST /query** - Main RAG query endpoint with action determination
4. **POST /jira/create-issue** - Create a Jira issue
5. **GET /jira/search** - Search Jira issues using JQL
6. **GET /confluence/search** - Search Confluence pages

### Request/Response Models:
- `QueryRequest` - For RAG queries
- `QueryResponse` - RAG query responses with sources and actions
- `JiraCreateRequest` - For creating Jira issues

### Initialization:
- Vector store
- Jira manager
- Confluence manager
- RAG agent

### Startup Event:
- Checks vector store status
- Logs helpful information
- Warns if vector store is empty

## Testing the Fixed main.py

### 1. Start the server:
```bash
uvicorn main:app --reload
```

### 2. Check health:
```bash
curl http://localhost:8000/health
```

### 3. Check status:
```bash
curl http://localhost:8000/status
```

### 4. View API docs:
Open http://localhost:8000/docs in your browser

### 5. Test RAG query:
```bash
curl -X POST http://localhost:8000/query ^
  -H "Content-Type: application/json" ^
  -d "{\"query\": \"What are the recent issues?\"}"
```

## Important Notes

1. **Data Ingestion:** The main.py no longer handles data ingestion. Use the standalone `ingest_data.py` script for this purpose.

2. **Scheduling:** For daily updates, set up OS-level scheduling:
   - Windows: Task Scheduler
   - Linux/Mac: cron

3. **Vector Store:** The application will warn you on startup if the vector store is empty. Run `python ingest_data.py` to populate it.

4. **Configuration:** Make sure your `.env` file has all required settings before starting the server.

## What Works Now

✅ Clean startup without errors
✅ Proper error handling in all endpoints
✅ Status endpoint for monitoring
✅ RAG queries with context-aware responses
✅ Jira issue creation through API
✅ Jira and Confluence search
✅ Action determination (create_issue vs search)
✅ Helpful logging and warnings

## What to Do Before Running

1. Ensure `.env` is configured with all credentials
2. Run `python test_connections.py` to verify connections
3. Run `python ingest_data.py` to populate vector store
4. Start the server with `uvicorn main:app --reload`
5. Check `/status` endpoint to verify everything is ready
