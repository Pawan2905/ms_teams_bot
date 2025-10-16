from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import uvicorn
import os

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

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process a user query and return a response"""
    try:
        # First determine the action
        action = rag_agent.determine_action(request.query)
        
        # Handle different actions
        if action['action'] == 'create_issue':
            # For demo purposes, we'll just return a message about creating an issue
            # In a real app, you would call jira_manager.create_issue() here
            return QueryResponse(
                answer=f"I can help you create a Jira issue. Please provide the following details: {action['parameters']}",
                sources=[],
                action=action
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

# Background task to update the vector store
@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    logger.info("Starting up Agentic RAG Assistant...")
    
    # You can add initialization code here, such as loading data into the vector store
    # For example:
    # await update_vector_store()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )
