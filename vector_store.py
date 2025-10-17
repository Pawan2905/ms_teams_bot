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
        """Add or upsert documents to the vector store.
        Each input doc should include: content, source, type, metadata (dict).
        We store stable IDs using the source value to support idempotent upserts.
        """
        if not documents:
            return

        texts: List[str] = []
        metadatas: List[Dict[str, Any]] = []
        ids: List[str] = []

        for doc in documents:
            source: str = doc.get("source")
            doc_type: str = doc.get("type")
            content: str = doc.get("content", "")
            extra_meta: Dict[str, Any] = doc.get("metadata", {})

            # Build stable ID based on unique source
            stable_id = f"{doc_type}:{source}"

            ids.append(stable_id)
            texts.append(content)
            metadatas.append({
                "source": source,
                "type": doc_type,
                **{f"meta_{k}": v for k, v in extra_meta.items()}
            })

        embeddings = self.get_embeddings(texts)

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
            meta = results['metadatas'][0][i]
            # Reconstruct original metadata dict from flattened meta_* keys
            reconstructed_meta = {
                k.replace('meta_', ''): v for k, v in meta.items() if k.startswith('meta_')
            }
            doc = {
                'content': results['documents'][0][i],
                'metadata': {
                    'source': meta.get('source'),
                    'type': meta.get('type'),
                    **reconstructed_meta
                },
                'distance': results['distances'][0][i]
            }
            documents.append(doc)
            
        return documents
    
    def delete_by_metadata(self, metadata_filter: Dict[str, Any]) -> None:
        """Delete documents matching the metadata filter (supports type/source/meta_*)."""
        self.collection.delete(where=metadata_filter)

    def delete_by_source_prefix(self, prefix: str) -> None:
        """Delete documents whose IDs start with the given prefix (e.g., 'jira_issue:' or 'confluence_page:')."""
        # Chroma supports where_document/where, but ID prefix deletion requires filtering metadatas or listing IDs.
        # We approximate using type filter when prefix maps to a type.
        if prefix.endswith(":"):
            type_name = prefix[:-1].split(":")[-1]
            try:
                self.collection.delete(where={"type": type_name})
            except Exception:
                pass
