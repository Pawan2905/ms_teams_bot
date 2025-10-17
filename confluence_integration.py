from atlassian import Confluence
from typing import List, Dict, Any, Optional
import logging
from config import settings
import re

logger = logging.getLogger(__name__)

class ConfluenceManager:
    def __init__(self):
        self.client = Confluence(
            url=settings.confluence_server,
            username=settings.confluence_email,
            password=settings.confluence_api_token,
            cloud=True
        )
    
    def search_content(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for content in Confluence using CQL text search."""
        try:
            # Build a CQL that searches pages by text relevance and sorts by last modified
            cql = f'type = page AND text ~ "{query}" ORDER BY lastmodified DESC'

            cql_result = self.client.cql(
                cql=cql,
                limit=limit,
                expand='content.space,content.version'
            )

            pages: List[Dict[str, Any]] = []
            for result in cql_result.get('results', []):
                content = result.get('content', {})
                page_id = content.get('id')
                if not page_id:
                    continue
                # Fetch full page with storage body for better RAG chunks
                try:
                    page = self.client.get_page_by_id(page_id, expand='body.storage,version,space')
                    pages.append(self._format_page(page))
                except Exception as inner_e:
                    logger.warning(f"Failed to fetch page {page_id}: {inner_e}")

            return pages
        except Exception as e:
            logger.error(f"Error searching Confluence: {str(e)}")
            return []
    
    def get_page_content(self, page_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific Confluence page by ID"""
        try:
            page = self.client.get_page_by_id(page_id, expand='body.storage,version,space')
            return self._format_page(page)
        except Exception as e:
            logger.error(f"Error getting Confluence page {page_id}: {str(e)}")
            return None
    
    def _format_page(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """Format Confluence page data into a dictionary"""
        # Clean HTML content
        content = page.get('body', {}).get('storage', {}).get('value', '')
        content = self._clean_html(content)
        
        return {
            'id': page['id'],
            'title': page['title'],
            'content': content,
            'url': f"{self.client.url}/wiki{page['_links']['webui']}",
            'space': page.get('space', {}).get('name', ''),
            'last_updated': page['version']['when'],
            'version': page['version']['number']
        }
    
    def _clean_html(self, html: str) -> str:
        """Remove HTML tags and clean up whitespace"""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', html)
        # Remove multiple spaces and newlines
        text = ' '.join(text.split())
        return text
    
    def get_pages_for_embedding(self, space_key: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get Confluence pages for embedding"""
        try:
            pages = self.client.get_all_pages_from_space(
                space=space_key,
                limit=limit,
                expand='body.storage,version,space'
            )
            
            documents = []
            for page in pages:
                content = f"""
                Confluence Page: {page['title']}
                Space: {page['space']['name']}
                Last Updated: {page['version']['when']}
                
                {self._clean_html(page.get('body', {}).get('storage', {}).get('value', ''))}
                """.strip()
                
                documents.append({
                    'content': content,
                    'source': f"confluence_page_{page['id']}",
                    'type': 'confluence_page',
                    'metadata': {
                        'id': page['id'],
                        'space': page['space']['key'],
                        'updated': page['version']['when']
                    }
                })
                
            return documents
            
        except Exception as e:
            logger.error(f"Error getting Confluence pages for embedding: {str(e)}")
            return []
