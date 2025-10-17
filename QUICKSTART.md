# Quick Start Guide

This guide will help you set up and test the Agentic RAG Assistant quickly.

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Configure Environment Variables

1. Copy the example environment file:
   ```bash
   copy .env.example .env
   ```

2. Edit `.env` and fill in your credentials:

### Required Azure OpenAI Settings:
```env
# LLM Settings
AZURE_OPENAI_API_KEY=your_llm_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_GPT_DEPLOYMENT=gpt-4

# Embedding Settings
AZURE_OPENAI_EMBEDDING_API_KEY=your_embedding_api_key
AZURE_OPENAI_EMBEDDING_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
```

### Required Jira Settings:
```env
JIRA_SERVER=https://your-company.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your_jira_api_token
```

**How to get Jira API Token:**
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Copy the token to your .env file

### Required Confluence Settings:
```env
CONFLUENCE_SERVER=https://your-company.atlassian.net/wiki
CONFLUENCE_EMAIL=your-email@company.com
CONFLUENCE_API_TOKEN=your_confluence_api_token
```

**Note:** You can use the same API token for both Jira and Confluence if they're on the same Atlassian instance.

### Data Source Settings:
```env
DEFAULT_JIRA_PROJECT_KEY=PROJ
DEFAULT_CONFLUENCE_SPACE_KEY=TEAM
REFRESH_DAYS_BACK=30
```

## Step 3: Test Connections

Before ingesting data, test your connections:

```bash
python test_connections.py
```

This will verify:
- ✅ Jira connection and permissions
- ✅ Confluence connection and permissions
- ✅ Azure OpenAI LLM endpoint
- ✅ Azure OpenAI Embedding endpoint
- ✅ ChromaDB vector store

## Step 4: Ingest Data

Once all connections are working, ingest your data:

```bash
python ingest_data.py
```

Or specify custom project/space:

```bash
python ingest_data.py --jira-project MYPROJECT --confluence-space MYSPACE
```

**What this does:**
1. Fetches recent Jira issues (last 30 days by default)
2. Fetches Confluence pages from specified space
3. Generates embeddings using Azure OpenAI
4. Stores everything in ChromaDB vector store

## Step 5: Start the API Server

```bash
uvicorn main:app --reload
```

The API will be available at: http://localhost:8000

## Step 6: Test the API

### View API Documentation
Open in your browser:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Test with cURL

**Health Check:**
```bash
curl http://localhost:8000/health
```

**Query the RAG System:**
```bash
curl -X POST http://localhost:8000/query ^
  -H "Content-Type: application/json" ^
  -d "{\"query\": \"What are the recent high priority issues?\"}"
```

**Search Jira:**
```bash
curl "http://localhost:8000/jira/search?jql=project=PROJ&max_results=5"
```

**Create a Jira Issue:**
```bash
curl -X POST http://localhost:8000/jira/create-issue ^
  -H "Content-Type: application/json" ^
  -d "{\"project_key\": \"PROJ\", \"summary\": \"Test Issue\", \"description\": \"Test from API\", \"issue_type\": \"Task\"}"
```

## Step 7: Test with Postman

1. Import the provided Postman collection (if available)
2. Set environment variable `base_url` to `http://localhost:8000`
3. Test each endpoint

## Common Issues

### Issue: "No Jira issues found"
**Solution:** 
- Check if your DEFAULT_JIRA_PROJECT_KEY is correct
- Verify you have access to the project
- Try increasing REFRESH_DAYS_BACK value

### Issue: "Confluence connection failed"
**Solution:**
- Verify your Confluence space key is correct
- Check if it's a Cloud or Server instance (update `cloud=True/False` in `confluence_integration.py`)
- Ensure your API token has proper permissions

### Issue: "Embedding generation failed"
**Solution:**
- Verify your Azure OpenAI embedding endpoint is correct
- Check if the deployment name matches your Azure setup
- Ensure you have quota available

### Issue: "ChromaDB errors"
**Solution:**
- Delete the `chroma_db` folder and try again
- Check disk space
- Ensure you have write permissions

## Schedule Daily Updates

### Windows Task Scheduler:
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger to daily at 2 AM
4. Action: Start a program
5. Program: `python`
6. Arguments: `E:\UV_Demo\ms_teams_bot\ingest_data.py`
7. Start in: `E:\UV_Demo\ms_teams_bot`

### Linux/Mac Cron:
```bash
# Edit crontab
crontab -e

# Add this line (runs at 2 AM daily)
0 2 * * * cd /path/to/ms_teams_bot && python ingest_data.py >> logs/ingest.log 2>&1
```

## Next Steps

1. Integrate with your Teams bot
2. Add authentication to the API
3. Deploy to production (Azure App Service, AWS, etc.)
4. Switch from ChromaDB to Azure AI Search for better scalability

## Support

If you encounter issues, check:
1. All environment variables are set correctly
2. Run `test_connections.py` to verify all services are accessible
3. Check the logs for detailed error messages
4. Ensure you have the latest dependencies installed
