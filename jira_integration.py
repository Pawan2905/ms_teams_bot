from jira import JIRA
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from config import settings

logger = logging.getLogger(__name__)

class JiraManager:
    def __init__(self):
        self.client = JIRA(
            server=settings.jira_server,
            basic_auth=(settings.jira_email, settings.jira_api_token)
        )
    
    def search_issues(self, jql: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """Search for Jira issues using JQL"""
        try:
            issues = self.client.search_issues(jql, maxResults=max_results)
            return [self._format_issue(issue) for issue in issues]
        except Exception as e:
            logger.error(f"Error searching Jira issues: {str(e)}")
            return []
    
    def get_issue(self, issue_key: str) -> Optional[Dict[str, Any]]:
        """Get a single Jira issue by key"""
        try:
            issue = self.client.issue(issue_key)
            return self._format_issue(issue)
        except Exception as e:
            logger.error(f"Error getting Jira issue {issue_key}: {str(e)}")
            return None
    
    def create_issue(self, project_key: str, summary: str, description: str, 
                    issue_type: str = "Task", **kwargs) -> Optional[Dict[str, Any]]:
        """Create a new Jira issue"""
        try:
            issue_dict = {
                'project': {'key': project_key},
                'summary': summary,
                'description': description,
                'issuetype': {'name': issue_type},
                **kwargs
            }
            
            issue = self.client.create_issue(fields=issue_dict)
            return self._format_issue(issue)
        except Exception as e:
            logger.error(f"Error creating Jira issue: {str(e)}")
            return None
    
    def _format_issue(self, issue) -> Dict[str, Any]:
        """Format Jira issue data into a dictionary"""
        return {
            'key': issue.key,
            'summary': issue.fields.summary or '',
            'description': issue.fields.description or 'No description provided',
            'status': issue.fields.status.name,
            'created': issue.fields.created,
            'updated': issue.fields.updated,
            'reporter': getattr(issue.fields.reporter, 'displayName', None),
            'assignee': getattr(issue.fields.assignee, 'displayName', None) if hasattr(issue.fields, 'assignee') and issue.fields.assignee else None,
            'url': f"{self.client.server_url}/browse/{issue.key}",
            'type': issue.fields.issuetype.name,
            'project': issue.fields.project.key,
            'labels': getattr(issue.fields, 'labels', []),
            'priority': getattr(issue.fields, 'priority', None) and issue.fields.priority.name or 'None'
        }
    
    def get_issues_for_embedding(self, project_key: str, days_back: int = 30) -> List[Dict[str, Any]]:
        """Get recent Jira issues for embedding"""
        jql = f"project = {project_key} AND updated >= -{days_back}d ORDER BY updated DESC"
        issues = self.search_issues(jql, max_results=100)
        
        documents = []
        for issue in issues:
            content = f"""
Jira Issue: {issue['key']}
Summary: {issue['summary']}
Status: {issue['status']}
Priority: {issue.get('priority', 'None')}
Type: {issue['type']}
Description: {issue['description']}
Assignee: {issue.get('assignee', 'Unassigned')}
Reporter: {issue.get('reporter', 'Unknown')}
Created: {issue['created']}
Updated: {issue['updated']}
Labels: {', '.join(issue.get('labels', []))}
URL: {issue['url']}
            """.strip()
            
            documents.append({
                'content': content,
                'source': f"jira_issue_{issue['key']}",
                'type': 'jira_issue',
                'metadata': {
                    'key': issue['key'],
                    'project': issue['project'],
                    'status': issue['status'],
                    'priority': issue.get('priority', 'None'),
                    'updated': issue['updated']
                }
            })
            
        return documents
