import os
import chromadb
from typing import List, Dict, Any, Optional
from chromadb.config import Settings
from openai import AzureOpenAI
from config import settings
import logging

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.chroma_db_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            )
        )
        
        self.embedding_client = AzureOpenAI(
            api_key=settings.azure_openai_embedding_api_key,
            api_version=settings.azure_openai_api_version,
            azure_endpoint=settings.azure_openai_embedding_endpoint,
        )
        
        self.collection = self.client.get_or_create_collection(
            name="jira_confluence_docs",
            metadata={"hnsw:space": "cosine"}
        )
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts using Azure OpenAI"""
        try:
            response = self.embedding_client.embeddings.create(
                input=texts,
                model=settings.azure_openai_embedding_deployment
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Add documents to the vector store"""
        if not documents:
            return
            
        texts = [doc["content"] for doc in documents]
        metadatas = [{"source": doc["source"], "type": doc["type"]} for doc in documents]
        ids = [f"{doc['type']}_{i}" for i, doc in enumerate(documents)]
        
        # Generate embeddings
        embeddings = self.get_embeddings(texts)
        
        # Add to collection
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=texts
        )
    
    def similarity_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents to the query"""
        # Get query embedding
        query_embedding = self.get_embeddings([query])[0]
        
        # Query the collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k
        )
        
        # Format results
        documents = []
        for i in range(len(results['ids'][0])):
            doc = {
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i]
            }
            documents.append(doc)
            
        return documents
    
    def delete_by_metadata(self, metadata_filter: Dict[str, str]) -> None:
        """Delete documents matching the metadata filter"""
        self.collection.delete(where=metadata_filter)
