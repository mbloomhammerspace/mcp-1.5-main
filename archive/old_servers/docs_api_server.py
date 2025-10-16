#!/usr/bin/env python3
"""
FastAPI-based Documentation Service with Swagger UI
Provides document management and RAG capabilities through REST API
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add the webui backend to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "webui" / "backend"))

# Import the MCP docs service
from mcp_docs_service import mcp_docs_service

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Federated Storage MCP Documentation API",
    description="Document management and RAG capabilities for the Federated Storage MCP system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API documentation
class DocumentInfo(BaseModel):
    name: str
    size: int
    type: str

class DocumentListResponse(BaseModel):
    status: str
    data: Dict[str, Any]
    timestamp: str

class DocumentUploadResponse(BaseModel):
    status: str
    data: Dict[str, Any]
    timestamp: str

class DocumentDeleteResponse(BaseModel):
    status: str
    data: Dict[str, Any]
    timestamp: str

class SearchResponse(BaseModel):
    status: str
    data: Dict[str, Any]
    timestamp: str

class ObjectivesContextResponse(BaseModel):
    status: str
    data: Dict[str, Any]
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    service: str
    port: int
    timestamp: float

# API Endpoints

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with service information."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Federated Storage MCP Documentation API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .header { background: #f0f0f0; padding: 20px; border-radius: 8px; }
            .links { margin: 20px 0; }
            .links a { display: inline-block; margin: 10px; padding: 10px 20px; 
                      background: #007bff; color: white; text-decoration: none; border-radius: 4px; }
            .links a:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🏗️ Federated Storage MCP Documentation API</h1>
            <p>Document management and RAG capabilities for the Federated Storage MCP system</p>
        </div>
        <div class="links">
            <a href="/docs">📚 Swagger UI Documentation</a>
            <a href="/redoc">📖 ReDoc Documentation</a>
            <a href="/openapi.json">🔧 OpenAPI Schema</a>
            <a href="/health">❤️ Health Check</a>
        </div>
        <h2>Available Endpoints:</h2>
        <ul>
            <li><strong>GET /documents</strong> - List all documents</li>
            <li><strong>POST /documents/upload</strong> - Upload a new document</li>
            <li><strong>GET /documents/{filename}</strong> - Get document content</li>
            <li><strong>DELETE /documents/{filename}</strong> - Delete a document</li>
            <li><strong>POST /search</strong> - Search documents</li>
            <li><strong>GET /objectives/context</strong> - Get objectives context</li>
            <li><strong>GET /health</strong> - Service health check</li>
        </ul>
    </body>
    </html>
    """

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns the current health status of the documentation service.
    """
    return HealthResponse(
        status="healthy",
        service="federated-storage-mcp-docs",
        port=8001,
        timestamp=datetime.now().timestamp()
    )

@app.get("/documents", response_model=DocumentListResponse)
async def list_documents():
    """
    List all available documents.
    
    Returns a list of all documents in the system with their metadata.
    """
    try:
        result = await mcp_docs_service.list_documents()
        return DocumentListResponse(
            status=result["status"],
            data=result["data"],
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a new document.
    
    Upload a document file to the system. The document will be processed and added to the RAG system.
    
    - **file**: The document file to upload (supports various formats)
    """
    try:
        # Read file content
        content = await file.read()
        
        # Save file
        docs_dir = Path("./backend/docs")
        docs_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = docs_dir / file.filename
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Process with RAG system
        result = await mcp_docs_service.add_document(file.filename, content.decode('utf-8', errors='ignore'))
        
        return DocumentUploadResponse(
            status=result["status"],
            data=result["data"],
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{filename}")
async def get_document(filename: str):
    """
    Get document content.
    
    Retrieve the content of a specific document by filename.
    
    - **filename**: The name of the document to retrieve
    """
    try:
        result = await mcp_docs_service.get_document(filename)
        if result["status"] == "error":
            raise HTTPException(status_code=404, detail=result["message"])
        
        return JSONResponse(
            content={
                "status": result["status"],
                "data": result["data"],
                "timestamp": datetime.now().isoformat()
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/{filename}", response_model=DocumentDeleteResponse)
async def delete_document(filename: str):
    """
    Delete a document.
    
    Remove a document from the system and the RAG system.
    
    - **filename**: The name of the document to delete
    """
    try:
        result = await mcp_docs_service.delete_document(filename)
        if result["status"] == "error":
            raise HTTPException(status_code=404, detail=result["message"])
        
        return DocumentDeleteResponse(
            status=result["status"],
            data=result["data"],
            timestamp=datetime.now().isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search", response_model=SearchResponse)
async def search_documents(
    query: str = Query(..., description="Search query"),
    top_k: int = Query(5, description="Number of results to return")
):
    """
    Search documents.
    
    Search through all documents using the RAG system.
    
    - **query**: The search query
    - **top_k**: Number of results to return (default: 5)
    """
    try:
        result = await mcp_docs_service.search_documents(query, top_k)
        return SearchResponse(
            status=result["status"],
            data=result["data"],
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/objectives/context", response_model=ObjectivesContextResponse)
async def get_objectives_context(
    query: str = Query(..., description="Query for objectives context")
):
    """
    Get objectives context.
    
    Get specific context about objectives from documents.
    
    - **query**: The query to search for objectives context
    """
    try:
        result = await mcp_docs_service.get_objectives_context(query)
        return ObjectivesContextResponse(
            status=result["status"],
            data=result["data"],
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/info")
async def api_info():
    """
    Get API information.
    
    Returns information about the API service.
    """
    return {
        "service": "docs",
        "version": "1.0.0",
        "description": "Document management and RAG capabilities",
        "endpoints": [
            "GET /documents - List all documents",
            "POST /documents/upload - Upload a document",
            "GET /documents/{filename} - Get document content",
            "DELETE /documents/{filename} - Delete a document",
            "POST /search - Search documents",
            "GET /objectives/context - Get objectives context",
            "GET /health - Health check"
        ],
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
