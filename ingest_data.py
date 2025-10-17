"""
Standalone script to ingest data from Jira and Confluence into the vector store.
This can be run manually or scheduled as a cron job/task scheduler.
"""
import logging
import sys
from datetime import datetime
from typing import Optional
from config import settings
from vector_store import VectorStore
from jira_integration import JiraManager
from confluence_integration import ConfluenceManager

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ingest_jira_data(
    vector_store: VectorStore, 
    project_key: Optional[str] = None, 
    days_back: Optional[int] = None
) -> bool:
    """Ingest Jira issues into the vector store"""
    project_key = project_key or settings.default_jira_project_key
    days_back = days_back or settings.refresh_days_back
    
    if not project_key:
        logger.warning("No Jira project key provided. Skipping Jira ingestion.")
        return False
    
    logger.info("=" * 60)
    logger.info(f"Starting Jira data ingestion for project: {project_key}")
    logger.info("=" * 60)
    
    try:
        jira_manager = JiraManager()
        
        # Fetch issues for embedding
        logger.info(f"Fetching Jira issues from the last {days_back} days...")
        jira_docs = jira_manager.get_issues_for_embedding(project_key, days_back)
        
        if not jira_docs:
            logger.warning(f"No Jira issues found for project {project_key}")
            return False
        
        logger.info(f"Found {len(jira_docs)} Jira issues")
        
        # Remove old Jira documents for this project
        logger.info("Removing old Jira issues from vector store...")
        vector_store.delete_by_metadata({"type": "jira_issue"})
        
        # Add new documents
        logger.info(f"Adding {len(jira_docs)} Jira issues to vector store...")
        vector_store.add_documents(jira_docs)
        
        logger.info(f"✅ Successfully ingested {len(jira_docs)} Jira issues")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error ingesting Jira data: {str(e)}", exc_info=True)
        return False

def ingest_confluence_data(
    vector_store: VectorStore, 
    space_key: Optional[str] = None, 
    limit: int = 100
) -> bool:
    """Ingest Confluence pages into the vector store"""
    space_key = space_key or settings.default_confluence_space_key
    
    if not space_key:
        logger.warning("No Confluence space key provided. Skipping Confluence ingestion.")
        return False
    
    logger.info("\n" + "=" * 60)
    logger.info(f"Starting Confluence data ingestion for space: {space_key}")
    logger.info("=" * 60)
    
    try:
        confluence_manager = ConfluenceManager()
        
        # Fetch pages for embedding
        logger.info(f"Fetching up to {limit} Confluence pages...")
        confluence_docs = confluence_manager.get_pages_for_embedding(space_key, limit)
        
        if not confluence_docs:
            logger.warning(f"No Confluence pages found for space {space_key}")
            return False
        
        logger.info(f"Found {len(confluence_docs)} Confluence pages")
        
        # Remove old Confluence documents for this space
        logger.info("Removing old Confluence pages from vector store...")
        vector_store.delete_by_metadata({"type": "confluence_page"})
        
        # Add new documents
        logger.info(f"Adding {len(confluence_docs)} Confluence pages to vector store...")
        vector_store.add_documents(confluence_docs)
        
        logger.info(f"✅ Successfully ingested {len(confluence_docs)} Confluence pages")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error ingesting Confluence data: {str(e)}", exc_info=True)
        return False

def main(jira_project: Optional[str] = None, confluence_space: Optional[str] = None):
    """Main function to run data ingestion"""
    start_time = datetime.utcnow()
    
    logger.info("\n" + "=" * 60)
    logger.info("STARTING DATA INGESTION")
    logger.info("=" * 60)
    logger.info(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    # Initialize vector store
    logger.info("\nInitializing vector store...")
    try:
        vector_store = VectorStore()
        initial_count = vector_store.collection.count()
        logger.info(f"Current document count in vector store: {initial_count}")
    except Exception as e:
        logger.error(f"❌ Failed to initialize vector store: {str(e)}")
        sys.exit(1)
    
    # Ingest data
    results = {}
    
    # Jira ingestion
    jira_success = ingest_jira_data(vector_store, jira_project)
    results['Jira'] = jira_success
    
    # Confluence ingestion
    confluence_success = ingest_confluence_data(vector_store, confluence_space)
    results['Confluence'] = confluence_success
    
    # Summary
    elapsed = (datetime.utcnow() - start_time).total_seconds()
    final_count = vector_store.collection.count()
    
    logger.info("\n" + "=" * 60)
    logger.info("INGESTION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Duration: {elapsed:.2f} seconds")
    logger.info(f"Initial document count: {initial_count}")
    logger.info(f"Final document count: {final_count}")
    logger.info(f"Documents added/updated: {final_count - initial_count}")
    
    logger.info("\nResults by source:")
    for source, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        logger.info(f"  {source}: {status}")
    
    if any(results.values()):
        logger.info("\n✅ Data ingestion completed successfully!")
        sys.exit(0)
    else:
        logger.error("\n❌ All data ingestion attempts failed!")
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest data from Jira and Confluence")
    parser.add_argument("--jira-project", help="Jira project key (overrides .env)")
    parser.add_argument("--confluence-space", help="Confluence space key (overrides .env)")
    
    args = parser.parse_args()
    
    main(jira_project=args.jira_project, confluence_space=args.confluence_space)
