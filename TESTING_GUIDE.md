# Complete Testing Guide - Agentic RAG Assistant

## Overview
This guide walks you through testing the entire application from scratch.

## Prerequisites
- Python 3.8+
- Azure OpenAI access (LLM + Embedding models)
- Jira Cloud/Server access
- Confluence Cloud/Server access

---

## Step 1: Environment Setup

### 1.1 Install Dependencies
```bash
cd e:\UV_Demo\ms_teams_bot
pip install -r requirements.txt
```

### 1.2 Configure Environment Variables
```bash
# Copy the example file
copy .env.example .env

# Edit .env with your actual credentials
notepad .env
```

**Required settings in .env:**
```env
# Azure OpenAI LLM
AZURE_OPENAI_API_KEY=your_llm_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_GPT_DEPLOYMENT=gpt-4

# Azure OpenAI Embedding
AZURE_OPENAI_EMBEDDING_API_KEY=your_embedding_api_key
AZURE_OPENAI_EMBEDDING_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002

# Jira
JIRA_SERVER=https://your-company.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your_jira_api_token

# Confluence
CONFLUENCE_SERVER=https://your-company.atlassian.net/wiki
CONFLUENCE_EMAIL=your-email@company.com
CONFLUENCE_API_TOKEN=your_confluence_api_token

# Data Sources
DEFAULT_JIRA_PROJECT_KEY=PROJ
DEFAULT_CONFLUENCE_SPACE_KEY=TEAM
REFRESH_DAYS_BACK=30
```

---

## Step 2: Test Connections

Run the connection test script:
```bash
python test_connections.py
```

**Expected Output:**
```
============================================================
STARTING CONNECTION TESTS
============================================================

============================================================
Testing Jira Connection...
============================================================
Connecting to Jira server: https://your-company.atlassian.net
Using email: your-email@company.com
Testing JQL query...
✅ Successfully connected to Jira!
Found 5 accessible projects:
  - PROJ: Project Name
  ...

============================================================
Testing Confluence Connection...
============================================================
Connecting to Confluence server: https://your-company.atlassian.net/wiki
Using email: your-email@company.com
Testing space access...
✅ Successfully connected to Confluence!
Found 3 accessible spaces:
  - TEAM: Team Space
  ...

============================================================
Testing Azure OpenAI Connection...
============================================================
Testing LLM endpoint...
LLM Endpoint: https://your-resource.openai.azure.com/
LLM Deployment: gpt-4
Testing Embedding endpoint...
Embedding Endpoint: https://your-resource.openai.azure.com/
Embedding Deployment: text-embedding-ada-002
✅ Successfully generated embeddings!
Embedding dimension: 1536

============================================================
Testing Vector Store...
============================================================
ChromaDB path: ./chroma_db
✅ Vector store initialized successfully!
Current document count: 0

============================================================
TEST SUMMARY
============================================================
Jira: ✅ PASS
Confluence: ✅ PASS
Azure OpenAI: ✅ PASS
Vector Store: ✅ PASS

✅ All tests passed! You're ready to run the application.
```

**If any test fails:**
- Check credentials in `.env`
- Verify network connectivity
- Check API token permissions
- Review error messages in the output

---

## Step 3: Ingest Data

Run the data ingestion script:
```bash
python ingest_data.py
```

**Expected Output:**
```
============================================================
STARTING DATA INGESTION
============================================================
Start time: 2025-01-17 10:00:00 UTC

Initializing vector store...
Current document count in vector store: 0

============================================================
Starting Jira data ingestion for project: PROJ
============================================================
Fetching Jira issues from the last 30 days...
Found 45 Jira issues
Removing old Jira issues from vector store...
Adding 45 Jira issues to vector store...
✅ Successfully ingested 45 Jira issues

============================================================
Starting Confluence data ingestion for space: TEAM
============================================================
Fetching up to 100 Confluence pages...
Found 67 Confluence pages
Removing old Confluence pages from vector store...
Adding 67 Confluence pages to vector store...
✅ Successfully ingested 67 Confluence pages

============================================================
INGESTION SUMMARY
============================================================
Duration: 45.23 seconds
Initial document count: 0
Final document count: 112
Documents added/updated: 112

Results by source:
  Jira: ✅ SUCCESS
  Confluence: ✅ SUCCESS

✅ Data ingestion completed successfully!
```

**Optional: Use custom project/space**
```bash
python ingest_data.py --jira-project MYPROJ --confluence-space MYSPACE
```

---

## Step 4: Start the API Server

```bash
uvicorn main:app --reload
```

**Expected Output:**
```
============================================================
Starting Agentic RAG Assistant...
============================================================
Vector store initialized with 112 documents
✅ Ready to serve queries
API Documentation available at: http://localhost:8000/docs
============================================================
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

---

## Step 5: Test API Endpoints

### 5.1 Health Check
```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{"status": "healthy"}
```

### 5.2 Status Check
```bash
curl http://localhost:8000/status
```

**Expected Response:**
```json
{
  "status": "running",
  "vector_store": {
    "document_count": 112,
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

### 5.3 RAG Query (Simple Search)
```bash
curl -X POST http://localhost:8000/query ^
  -H "Content-Type: application/json" ^
  -d "{\"query\": \"What are the recent high priority issues?\"}"
```

**Expected Response:**
```json
{
  "answer": "Based on recent data, there are several high priority issues: PROJ-123 (Bug in login system), PROJ-124 (Performance degradation), ...",
  "sources": [
    {
      "source": "jira_issue_PROJ-123",
      "type": "jira_issue",
      "key": "PROJ-123",
      "status": "Open",
      "priority": "High"
    }
  ],
  "action": {
    "action": "search",
    "parameters": {}
  }
}
```

### 5.4 Search Jira
```bash
curl "http://localhost:8000/jira/search?jql=project=PROJ%20ORDER%20BY%20created%20DESC&max_results=5"
```

**Expected Response:**
```json
{
  "status": "success",
  "results": [
    {
      "key": "PROJ-123",
      "summary": "Bug in login system",
      "description": "Users unable to login...",
      "status": "Open",
      "priority": "High",
      ...
    }
  ]
}
```

### 5.5 Search Confluence
```bash
curl "http://localhost:8000/confluence/search?query=documentation&limit=5"
```

**Expected Response:**
```json
{
  "status": "success",
  "results": [
    {
      "id": "12345",
      "title": "API Documentation",
      "content": "This page contains...",
      "url": "https://your-company.atlassian.net/wiki/...",
      ...
    }
  ]
}
```

### 5.6 Create Jira Issue
```bash
curl -X POST http://localhost:8000/jira/create-issue ^
  -H "Content-Type: application/json" ^
  -d "{\"project_key\": \"PROJ\", \"summary\": \"Test Issue from API\", \"description\": \"This is a test issue created via the RAG Assistant API.\", \"issue_type\": \"Task\"}"
```

**Expected Response:**
```json
{
  "status": "success",
  "issue": {
    "key": "PROJ-456",
    "summary": "Test Issue from API",
    "status": "To Do",
    "url": "https://your-company.atlassian.net/browse/PROJ-456",
    ...
  }
}
```

---

## Step 6: Test with Postman

### 6.1 Setup
1. Open Postman
2. Create a new collection: "Agentic RAG Assistant"
3. Set environment variable: `base_url = http://localhost:8000`

### 6.2 Create Requests

**Request 1: Health Check**
- Method: GET
- URL: `{{base_url}}/health`

**Request 2: Status Check**
- Method: GET
- URL: `{{base_url}}/status`

**Request 3: RAG Query**
- Method: POST
- URL: `{{base_url}}/query`
- Headers: `Content-Type: application/json`
- Body (raw JSON):
```json
{
  "query": "Show me recent bugs in the system"
}
```

**Request 4: Jira Search**
- Method: GET
- URL: `{{base_url}}/jira/search?jql=project=PROJ&max_results=10`

**Request 5: Confluence Search**
- Method: GET
- URL: `{{base_url}}/confluence/search?query=API&limit=5`

**Request 6: Create Jira Issue**
- Method: POST
- URL: `{{base_url}}/jira/create-issue`
- Headers: `Content-Type: application/json`
- Body (raw JSON):
```json
{
  "project_key": "PROJ",
  "summary": "Test Issue",
  "description": "Created from Postman",
  "issue_type": "Task"
}
```

---

## Step 7: Interactive API Testing

Open http://localhost:8000/docs in your browser to access the Swagger UI.

**Features:**
- Interactive API documentation
- Try out each endpoint directly
- See request/response schemas
- Test with different parameters

---

## Common Issues & Solutions

### Issue 1: Vector store is empty
**Symptom:** Queries return no results or generic answers

**Solution:**
```bash
python ingest_data.py
```

### Issue 2: Connection errors
**Symptom:** Test connections fail

**Solution:**
- Verify credentials in `.env`
- Check network/firewall
- Ensure API tokens have correct permissions

### Issue 3: Embedding errors
**Symptom:** "Error generating embeddings"

**Solution:**
- Verify Azure OpenAI endpoint and deployment names
- Check API key and quota
- Ensure deployment is active

### Issue 4: No Jira issues found
**Symptom:** Ingestion reports 0 issues

**Solution:**
- Verify project key is correct
- Increase `REFRESH_DAYS_BACK` value
- Check Jira permissions

### Issue 5: Module import errors
**Symptom:** "ModuleNotFoundError"

**Solution:**
```bash
pip install -r requirements.txt
```

---

## Performance Benchmarks

**Expected timings:**
- Connection test: ~10-20 seconds
- Data ingestion (100 documents): ~30-60 seconds
- Single RAG query: ~2-5 seconds
- Jira search: ~1-2 seconds
- Confluence search: ~1-3 seconds

---

## Next Steps

1. ✅ All tests passing
2. ✅ Data ingested successfully
3. ✅ API responding correctly
4. Schedule daily data updates (see QUICKSTART.md)
5. Integrate with Teams bot
6. Deploy to production
7. Set up monitoring and logging

---

## Support

If you encounter issues:
1. Check this guide first
2. Review error messages in logs
3. Run `python test_connections.py` to isolate issues
4. Check `.env` configuration
5. Verify all dependencies are installed
