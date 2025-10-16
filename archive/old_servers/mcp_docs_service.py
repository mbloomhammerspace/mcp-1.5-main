#!/usr/bin/env python3
"""
MCP Document Service
Provides document management and RAG capabilities through MCP
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class MCPDocumentService:
    """MCP service for document management and RAG operations."""
    
    def __init__(self, docs_dir: str = "./backend/docs"):
        self.docs_dir = Path(docs_dir)
        self.docs_dir.mkdir(exist_ok=True)
        
        # Import RAG system
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent / "webui" / "backend"))
            from rag_system import rag_system
            self.rag_system = rag_system
        except ImportError:
            logger.warning("RAG system not available, using basic document operations")
            self.rag_system = None
    
    async def list_documents(self) -> Dict[str, Any]:
        """List all available documents."""
        try:
            files = []
            for file_path in self.docs_dir.glob("*"):
                if file_path.is_file():
                    files.append({
                        "name": file_path.name,
                        "size": file_path.stat().st_size,
                        "type": file_path.suffix.lower()
                    })
            
            return {
                "status": "success",
                "data": {
                    "documents": files,
                    "total_count": len(files)
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to list documents: {str(e)}"
            }
    
    async def get_document_content(self, filename: str) -> Dict[str, Any]:
        """Get the content of a specific document."""
        try:
            file_path = self.docs_dir / filename
            if not file_path.exists():
                return {
                    "status": "error",
                    "message": f"Document '{filename}' not found"
                }
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            return {
                "status": "success",
                "data": {
                    "filename": filename,
                    "content": content,
                    "size": len(content)
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to read document: {str(e)}"
            }
    
    async def search_documents(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Search documents using RAG system."""
        try:
            if not self.rag_system:
                return {
                    "status": "error",
                    "message": "RAG system not available"
                }
            
            results = self.rag_system.search(query, top_k)
            
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "content": result.chunk.content,
                    "source_file": result.chunk.source_file,
                    "score": result.score,
                    "citation": result.citation,
                    "context": result.context
                })
            
            return {
                "status": "success",
                "data": {
                    "query": query,
                    "results": formatted_results,
                    "total_found": len(formatted_results)
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Search failed: {str(e)}"
            }
    
    async def get_context_for_query(self, query: str) -> Dict[str, Any]:
        """Get contextual information for a query."""
        try:
            if not self.rag_system:
                return {
                    "status": "error",
                    "message": "RAG system not available"
                }
            
            context = self.rag_system.get_context_for_query(query)
            
            return {
                "status": "success",
                "data": {
                    "query": query,
                    "context": context,
                    "has_context": bool(context.strip())
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to get context: {str(e)}"
            }
    
    async def get_document_stats(self) -> Dict[str, Any]:
        """Get statistics about documents and RAG system."""
        try:
            if not self.rag_system:
                return {
                    "status": "error",
                    "message": "RAG system not available"
                }
            
            stats = self.rag_system.get_stats()
            
            return {
                "status": "success",
                "data": stats
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to get stats: {str(e)}"
            }
    
    async def add_document(self, filename: str, content: str) -> Dict[str, Any]:
        """Add a new document to the system."""
        try:
            file_path = self.docs_dir / filename
            
            # Write the document
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Add to RAG system if available
            if self.rag_system:
                self.rag_system.add_document(file_path)
            
            return {
                "status": "success",
                "data": {
                    "filename": filename,
                    "size": len(content),
                    "added_to_rag": self.rag_system is not None
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to add document: {str(e)}"
            }
    
    async def delete_document(self, filename: str) -> Dict[str, Any]:
        """Delete a document from the system."""
        try:
            file_path = self.docs_dir / filename
            
            if not file_path.exists():
                return {
                    "status": "error",
                    "message": f"Document '{filename}' not found"
                }
            
            # Remove from RAG system if available
            if self.rag_system:
                self.rag_system.remove_document(filename)
            
            # Delete the file
            file_path.unlink()
            
            return {
                "status": "success",
                "data": {
                    "filename": filename,
                    "removed_from_rag": self.rag_system is not None
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to delete document: {str(e)}"
            }
    
    async def get_objectives_context(self, query: str) -> Dict[str, Any]:
        """Get specific context about objectives from documents."""
        try:
            if not self.rag_system:
                return {
                    "status": "error",
                    "message": "RAG system not available"
                }
            
            # Search for objectives-related content
            results = self.rag_system.search(query + " objectives", top_k=3)
            
            objectives_context = ""
            citations = []
            
            for result in results:
                if "objective" in result.chunk.content.lower():
                    objectives_context += f"\n---\n**{result.citation}**\n{result.chunk.content}"
                    citations.append(result.citation)
            
            return {
                "status": "success",
                "data": {
                    "query": query,
                    "context": objectives_context,
                    "citations": citations,
                    "has_objectives_info": bool(objectives_context.strip())
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to get objectives context: {str(e)}"
            }

# Global instance
mcp_docs_service = MCPDocumentService() 