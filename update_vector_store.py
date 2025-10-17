import asyncio
import logging
from datetime import datetime, timedelta
from vector_store import VectorStore
from jira_integration import JiraManager
from confluence_integration import ConfluenceManager
from config import settings

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def update_jira_documents(vector_store: VectorStore, project_key: str, days_back: int = 7):
    """Update the vector store with recent Jira issues"""
    try:
        logger.info(f"Fetching Jira issues for project {project_key} from the last {days_back} days...")
        jira_manager = JiraManager()
        
        # First, remove old Jira issues
        logger.info("Removing old Jira issues from vector store...")
        vector_store.delete_by_metadata({"type": "jira_issue"})
        
        # Get recent issues and add to vector store
        jira_docs = jira_manager.get_issues_for_embedding(project_key, days_back)
        if jira_docs:
            logger.info(f"Adding {len(jira_docs)} Jira issues to vector store...")
            vector_store.add_documents(jira_docs)
            logger.info("Successfully updated Jira issues in vector store")
        else:
            logger.warning("No Jira issues found to add to vector store")
            
    except Exception as e:
        logger.error(f"Error updating Jira documents: {str(e)}", exc_info=True)

async def update_confluence_documents(vector_store: VectorStore, space_key: str, limit: int = 100):
    """Update the vector store with Confluence pages"""
    try:
        logger.info(f"Fetching Confluence pages for space {space_key}...")
        confluence_manager = ConfluenceManager()
        
        # First, remove old Confluence pages
        logger.info("Removing old Confluence pages from vector store...")
        vector_store.delete_by_metadata({"type": "confluence_page"})
        
        # Get pages and add to vector store
        confluence_docs = confluence_manager.get_pages_for_embedding(space_key, limit)
        if confluence_docs:
            logger.info(f"Adding {len(confluence_docs)} Confluence pages to vector store...")
            vector_store.add_documents(confluence_docs)
            logger.info("Successfully updated Confluence pages in vector store")
        else:
            logger.warning("No Confluence pages found to add to vector store")
            
    except Exception as e:
        logger.error(f"Error updating Confluence documents: {str(e)}", exc_info=True)

async def main():
    """Main function to update the vector store"""
    start_time = datetime.utcnow()
    logger.info("Starting vector store update...")
    
    # Initialize vector store
    vector_store = VectorStore()
    
    try:
        jira_project = settings.default_jira_project_key
        conf_space = settings.default_confluence_space_key

        tasks = []
        if jira_project:
            tasks.append(update_jira_documents(vector_store, jira_project, settings.refresh_days_back))
        if conf_space:
            tasks.append(update_confluence_documents(vector_store, conf_space))

        if tasks:
            await asyncio.gather(*tasks)
        else:
            logger.warning("No default Jira project or Confluence space configured; nothing to update")
        
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"Vector store update completed in {elapsed:.2f} seconds")
        
    except Exception as e:
        logger.error(f"Error during vector store update: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(main())
