from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import uvicorn
import os
import asyncio

# Import our modules
from config import settings
from vector_store import VectorStore
from jira_integration import JiraManager
from confluence_integration import ConfluenceManager
from rag_agent import RAGAgent

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Agentic RAG Assistant",
    description="A RAG-based assistant for Jira and Confluence integration",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
vector_store = VectorStore()
jira_manager = JiraManager()
confluence_manager = ConfluenceManager()
rag_agent = RAGAgent(vector_store)

# Request/Response Models
class QueryRequest(BaseModel):
    query: str
    context: Optional[List[Dict[str, Any]]] = None

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    action: Optional[Dict[str, Any]] = None

class JiraCreateRequest(BaseModel):
    project_key: str
    summary: str
    description: str
    issue_type: str = "Task"
    additional_fields: Optional[Dict[str, Any]] = None

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/status")
async def get_status():
    """Get application status including vector store information"""
    try:
        doc_count = vector_store.collection.count()
        return {
            "status": "running",
            "vector_store": {
                "document_count": doc_count,
                "ready": doc_count > 0
            },
            "integrations": {
                "jira_configured": bool(settings.jira_server and settings.jira_api_token),
                "confluence_configured": bool(settings.confluence_server and settings.confluence_api_token),
                "default_jira_project": settings.default_jira_project_key or None,
                "default_confluence_space": settings.default_confluence_space_key or None
            }
        }
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process a user query and return a response"""
    try:
        # First determine the action
        action = rag_agent.determine_action(request.query)
        
        # Handle different actions
        if action['action'] == 'create_issue':
            params = action.get('parameters', {}) or {}
            project_key = params.get('project_key') or settings.default_jira_project_key
            summary = params.get('summary')
            description = params.get('description') or ""
            issue_type = params.get('issue_type') or "Task"

            missing = []
            if not project_key:
                missing.append('project_key')
            if not summary:
                missing.append('summary')

            if missing:
                return QueryResponse(
                    answer=f"To create a Jira issue, please provide: {', '.join(missing)}.",
                    sources=[],
                    action={"action": "create_issue", "parameters": {"required_fields": missing}}
                )

            issue = jira_manager.create_issue(
                project_key=project_key,
                summary=summary,
                description=description,
                issue_type=issue_type,
            )
            if issue:
                return QueryResponse(
                    answer=f"Created Jira issue {issue['key']} ({issue['url']}).",
                    sources=[],
                    action={"action": "create_issue", "parameters": {"issue": issue}}
                )
            else:
                return QueryResponse(
                    answer="Failed to create Jira issue. Please verify project key and permissions.",
                    sources=[],
                    action={"action": "create_issue"}
                )
        else:
            # Default to search action
            response = rag_agent.generate_response(request.query, request.context)
            return QueryResponse(
                answer=response['answer'],
                sources=response['sources'],
                action=action
            )
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your request"
        )

@app.post("/jira/create-issue")
async def create_jira_issue(request: JiraCreateRequest):
    """Create a new Jira issue"""
    try:
        # Create the issue
        issue = jira_manager.create_issue(
            project_key=request.project_key,
            summary=request.summary,
            description=request.description,
            issue_type=request.issue_type,
            **request.additional_fields or {}
        )
        
        if not issue:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create Jira issue"
            )
            
        return {"status": "success", "issue": issue}
        
    except Exception as e:
        logger.error(f"Error creating Jira issue: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/jira/search")
async def search_jira(jql: str, max_results: int = 10):
    """Search for Jira issues"""
    try:
        issues = jira_manager.search_issues(jql, max_results)
        return {"status": "success", "results": issues}
    except Exception as e:
        logger.error(f"Error searching Jira: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/confluence/search")
async def search_confluence(query: str, limit: int = 10):
    """Search for Confluence pages"""
    try:
        pages = confluence_manager.search_content(query, limit)
        return {"status": "success", "results": pages}
    except Exception as e:
        logger.error(f"Error searching Confluence: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    logger.info("=" * 60)
    logger.info("Starting Agentic RAG Assistant...")
    logger.info("=" * 60)
    
    # Check vector store status
    try:
        doc_count = vector_store.collection.count()
        logger.info(f"Vector store initialized with {doc_count} documents")
        
        if doc_count == 0:
            logger.warning("Vector store is empty! Run 'python ingest_data.py' to populate it.")
        else:
            logger.info(f"✅ Ready to serve queries")
            
    except Exception as e:
        logger.error(f"Error checking vector store: {str(e)}")
    
    logger.info("API Documentation available at: http://localhost:8000/docs")
    logger.info("=" * 60)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )
