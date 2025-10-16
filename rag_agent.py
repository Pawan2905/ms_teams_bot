from typing import List, Dict, Any, Optional
from openai import AzureOpenAI
from config import settings
import logging
import json

logger = logging.getLogger(__name__)

class RAGAgent:
    def __init__(self, vector_store):
        self.vector_store = vector_store
        self.client = AzureOpenAI(
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            azure_endpoint=settings.azure_openai_endpoint,
        )
    
    def generate_response(self, query: str, context: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate a response to the user query using RAG"""
        try:
            # If no context provided, retrieve relevant documents
            if context is None:
                context = self._retrieve_relevant_documents(query)
            
            # Format the context for the prompt
            context_str = "\n\n".join([doc['content'] for doc in context])
            
            # Create the prompt with context
            prompt = f"""You are a helpful assistant that helps with Jira and Confluence. 
            Use the following context to answer the question. If you don't know the answer, say you don't know.
            
            Context:
            {context_str}
            
            Question: {query}
            
            Answer:"""
            
            # Generate response using Azure OpenAI
            response = self.client.chat.completions.create(
                model=settings.azure_openai_gpt_deployment,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that helps with Jira and Confluence."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            return {
                'answer': response.choices[0].message.content,
                'sources': [doc['metadata'] for doc in context]
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {
                'answer': "I'm sorry, I encountered an error while processing your request.",
                'sources': []
            }
    
    def _retrieve_relevant_documents(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant documents from the vector store"""
        try:
            return self.vector_store.similarity_search(query, k=k)
        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}")
            return []
    
    def determine_action(self, query: str) -> Dict[str, Any]:
        """Determine the appropriate action based on the user query"""
        try:
            # Use the LLM to classify the query
            response = self.client.chat.completions.create(
                model=settings.azure_openai_gpt_deployment,
                messages=[
                    {
                        "role": "system", 
                        "content": """Analyze the user query and determine the appropriate action. 
                        Return a JSON object with 'action' (one of: 'search', 'create_issue', 'unknown') 
                        and any relevant parameters."""
                    },
                    {"role": "user", "content": query}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            try:
                action = json.loads(response.choices[0].message.content)
                return {
                    'action': action.get('action', 'unknown'),
                    'parameters': action.get('parameters', {})
                }
            except json.JSONDecodeError:
                return {'action': 'search', 'parameters': {}}
                
        except Exception as e:
            logger.error(f"Error determining action: {str(e)}")
            return {'action': 'search', 'parameters': {}}
