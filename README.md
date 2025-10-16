# Agentic RAG Assistant for Jira and Confluence

A Retrieval-Augmented Generation (RAG) based assistant that integrates with Jira and Confluence to provide intelligent responses and automate tasks.

## Features

- Natural language querying of Jira issues and Confluence pages
- Context-aware responses using Azure OpenAI
- Vector similarity search with ChromaDB
- Daily automatic updates of the knowledge base
- RESTful API for integration with other applications

## Prerequisites

- Python 3.8+
- Azure OpenAI service with GPT and embedding models deployed
- Jira Cloud/Server with API access
- Confluence Cloud/Server with API access

## Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd ms_teams_bot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file based on `.env.example` and fill in your credentials:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

## Configuration

Edit the `.env` file with your specific configuration:

```env
# Azure OpenAI Settings
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint
AZURE_OPENAI_API_VERSION=2023-05-15
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=your_embedding_deployment_name
AZURE_OPENAI_GPT_DEPLOYMENT=your_gpt_deployment_name

# Jira Settings
JIRA_SERVER=your_jira_server_url
JIRA_EMAIL=your_jira_email
JIRA_API_TOKEN=your_jira_api_token

# Confluence Settings
CONFLUENCE_SERVER=your_confluence_server_url
CONFLUENCE_EMAIL=your_confluence_email
CONFLUENCE_API_TOKEN=your_confluence_api_token
```

## Running the Application

1. Start the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```

2. The API will be available at `http://localhost:8000`

3. Access the API documentation at `http://localhost:8000/docs`

## Updating the Vector Store

To update the vector store with the latest data from Jira and Confluence, run:

```bash
python update_vector_store.py
```

You can schedule this to run daily using a cron job or Windows Task Scheduler.

## API Endpoints

- `POST /query` - Process a natural language query
- `POST /jira/create-issue` - Create a new Jira issue
- `GET /jira/search` - Search Jira issues
- `GET /confluence/search` - Search Confluence pages
- `GET /health` - Health check endpoint

## Example Usage

### Query the RAG system:
```bash
curl -X 'POST' \
  'http://localhost:8000/query' \
  -H 'Content-Type: application/json' \
  -d '{"query": "What are the recent high priority issues in Jira?"}'
```

### Create a Jira issue:
```bash
curl -X 'POST' \
  'http://localhost:8000/jira/create-issue' \
  -H 'Content-Type: application/json' \
  -d '{
    "project_key": "YOUR_PROJECT",
    "summary": "Test issue from RAG assistant",
    "description": "This is a test issue created by the RAG assistant.",
    "issue_type": "Task"
  }'
```

## Deployment

For production deployment, consider using:
- Gunicorn with Uvicorn workers
- Environment variable management (e.g., Azure Key Vault)
- Containerization with Docker
- Orchestration with Kubernetes

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
