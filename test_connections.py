"""
Test script to verify connections to Jira, Confluence, and Azure OpenAI
"""
import logging
import sys
from config import settings
from jira_integration import JiraManager
from confluence_integration import ConfluenceManager
from vector_store import VectorStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_jira_connection():
    """Test Jira connection"""
    logger.info("=" * 60)
    logger.info("Testing Jira Connection...")
    logger.info("=" * 60)
    
    try:
        if not settings.jira_server or not settings.jira_email or not settings.jira_api_token:
            logger.error("❌ Jira credentials not configured in .env file")
            return False
            
        logger.info(f"Connecting to Jira server: {settings.jira_server}")
        logger.info(f"Using email: {settings.jira_email}")
        
        jira_manager = JiraManager()
        
        # Test with a simple JQL query
        logger.info("Testing JQL query...")
        
        # Get the user's permissions/projects
        projects = jira_manager.client.projects()
        logger.info(f"✅ Successfully connected to Jira!")
        logger.info(f"Found {len(projects)} accessible projects:")
        for project in projects[:5]:  # Show first 5
            logger.info(f"  - {project.key}: {project.name}")
        
        # Test fetching issues if a default project is configured
        if settings.default_jira_project_key:
            logger.info(f"\nTesting issue fetch for project: {settings.default_jira_project_key}")
            issues = jira_manager.search_issues(
                f"project = {settings.default_jira_project_key} ORDER BY updated DESC",
                max_results=5
            )
            logger.info(f"✅ Found {len(issues)} recent issues")
            for issue in issues[:3]:
                logger.info(f"  - {issue['key']}: {issue['summary']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Jira connection failed: {str(e)}", exc_info=True)
        return False

def test_confluence_connection():
    """Test Confluence connection"""
    logger.info("\n" + "=" * 60)
    logger.info("Testing Confluence Connection...")
    logger.info("=" * 60)
    
    try:
        if not settings.confluence_server or not settings.confluence_email or not settings.confluence_api_token:
            logger.error("❌ Confluence credentials not configured in .env file")
            return False
            
        logger.info(f"Connecting to Confluence server: {settings.confluence_server}")
        logger.info(f"Using email: {settings.confluence_email}")
        
        confluence_manager = ConfluenceManager()
        
        # Test getting spaces
        logger.info("Testing space access...")
        spaces = confluence_manager.client.get_all_spaces(limit=10)
        
        logger.info(f"✅ Successfully connected to Confluence!")
        logger.info(f"Found {len(spaces.get('results', []))} accessible spaces:")
        for space in spaces.get('results', [])[:5]:
            logger.info(f"  - {space.get('key')}: {space.get('name')}")
        
        # Test fetching pages if a default space is configured
        if settings.default_confluence_space_key:
            logger.info(f"\nTesting page fetch for space: {settings.default_confluence_space_key}")
            pages = confluence_manager.client.get_all_pages_from_space(
                settings.default_confluence_space_key,
                limit=5
            )
            logger.info(f"✅ Found {len(pages)} recent pages")
            for page in pages[:3]:
                logger.info(f"  - {page.get('title')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Confluence connection failed: {str(e)}", exc_info=True)
        return False

def test_azure_openai_connection():
    """Test Azure OpenAI connection"""
    logger.info("\n" + "=" * 60)
    logger.info("Testing Azure OpenAI Connection...")
    logger.info("=" * 60)
    
    try:
        # Test LLM endpoint
        logger.info("Testing LLM endpoint...")
        if not settings.azure_openai_api_key or not settings.azure_openai_endpoint:
            logger.error("❌ Azure OpenAI LLM credentials not configured in .env file")
            return False
            
        logger.info(f"LLM Endpoint: {settings.azure_openai_endpoint}")
        logger.info(f"LLM Deployment: {settings.azure_openai_gpt_deployment}")
        
        # Test Embedding endpoint
        logger.info("\nTesting Embedding endpoint...")
        if not settings.azure_openai_embedding_api_key or not settings.azure_openai_embedding_endpoint:
            logger.error("❌ Azure OpenAI Embedding credentials not configured in .env file")
            return False
            
        logger.info(f"Embedding Endpoint: {settings.azure_openai_embedding_endpoint}")
        logger.info(f"Embedding Deployment: {settings.azure_openai_embedding_deployment}")
        
        # Test actual embedding generation
        vector_store = VectorStore()
        test_text = ["This is a test message for embedding generation."]
        embeddings = vector_store.get_embeddings(test_text)
        
        logger.info(f"✅ Successfully generated embeddings!")
        logger.info(f"Embedding dimension: {len(embeddings[0])}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Azure OpenAI connection failed: {str(e)}", exc_info=True)
        return False

def test_vector_store():
    """Test ChromaDB vector store"""
    logger.info("\n" + "=" * 60)
    logger.info("Testing Vector Store...")
    logger.info("=" * 60)
    
    try:
        logger.info(f"ChromaDB path: {settings.chroma_db_path}")
        
        vector_store = VectorStore()
        
        # Check collection stats
        count = vector_store.collection.count()
        logger.info(f"✅ Vector store initialized successfully!")
        logger.info(f"Current document count: {count}")
        
        if count > 0:
            # Test a sample query
            results = vector_store.similarity_search("test query", k=1)
            if results:
                logger.info(f"Sample document type: {results[0]['metadata'].get('type')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Vector store test failed: {str(e)}", exc_info=True)
        return False

def main():
    """Run all connection tests"""
    logger.info("\n" + "=" * 60)
    logger.info("STARTING CONNECTION TESTS")
    logger.info("=" * 60 + "\n")
    
    results = {
        "Jira": test_jira_connection(),
        "Confluence": test_confluence_connection(),
        "Azure OpenAI": test_azure_openai_connection(),
        "Vector Store": test_vector_store()
    }
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    for service, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{service}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("\n✅ All tests passed! You're ready to run the application.")
        sys.exit(0)
    else:
        logger.error("\n❌ Some tests failed. Please check the configuration and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()
