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
from update_vector_store import update_jira_documents, update_confluence_documents

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
class UpdateRequest(BaseModel):
    jira_project_key: Optional[str] = None
    confluence_space_key: Optional[str] = None
    days_back: Optional[int] = None


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
@app.post("/admin/update")
async def admin_update(request: UpdateRequest):
    """Trigger a background update of the vector store for Jira and Confluence."""
    try:
        jira_project = request.jira_project_key or settings.default_jira_project_key
        conf_space = request.confluence_space_key or settings.default_confluence_space_key
        days_back = request.days_back or settings.refresh_days_back

        tasks = []
        if jira_project:
            tasks.append(update_jira_documents(vector_store, jira_project, days_back))
        if conf_space:
            tasks.append(update_confluence_documents(vector_store, conf_space))

        if not tasks:
            raise HTTPException(status_code=400, detail="No project/space configured to update")

        await asyncio.gather(*tasks)
        return {"status": "success", "updated": {
            "jira_project": jira_project if jira_project else None,
            "confluence_space": conf_space if conf_space else None
        }}
    except Exception as e:
        logger.error(f"Error during admin update: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
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
    """Initialize the application and schedule periodic updates."""
    logger.info("Starting up Agentic RAG Assistant...")
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger

        scheduler = AsyncIOScheduler()

        # Parse cron string from settings.refresh_schedule_cron
        cron_expr = settings.refresh_schedule_cron.strip().split()
        if len(cron_expr) == 5:
            trigger = CronTrigger(
                minute=cron_expr[0], hour=cron_expr[1], day=cron_expr[2], month=cron_expr[3], day_of_week=cron_expr[4]
            )
            async def scheduled_job():
                tasks = []
                if settings.default_jira_project_key:
                    tasks.append(update_jira_documents(vector_store, settings.default_jira_project_key, settings.refresh_days_back))
                if settings.default_confluence_space_key:
                    tasks.append(update_confluence_documents(vector_store, settings.default_confluence_space_key))
                if tasks:
                    await asyncio.gather(*tasks)

            scheduler.add_job(scheduled_job, trigger, id="daily_refresh", replace_existing=True)
            scheduler.start()
            logger.info("Scheduled daily refresh job")
        else:
            logger.warning("REFRESH_SCHEDULE_CRON is not a 5-part cron expression; skipping scheduler setup")
    except Exception as e:
        logger.warning(f"Scheduler setup skipped: {e}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )
