"""
RAG Tool for searching agricultural policy and crop information documents
Uses ChromaDB vector store for semantic search
"""

from typing import Optional
from crewai.tools import tool
from policy_navigator.retrieval.vector_store import get_vector_store


@tool("RAG Document Search Tool")
def rag_tool(query: str, category: Optional[str] = None) -> str:
    """Search agricultural policy and crop information documents using RAG.
    
    This tool searches through vectorized documents stored in ChromaDB to find
    relevant information about policies, crops, pests, and agricultural practices.
    Use this tool when you need to retrieve information from the document database.
    
    Args:
        query: Search query about policies, crops, or agricultural information.
               Be specific about what you're looking for (e.g., "PM-KISAN scheme benefits",
               "paddy cultivation practices", "pest management for cotton").
        category: Optional category filter to narrow search scope.
                  Examples: 'Financial Schemes', 'Crop Cultivation Guides', 
                  'Pest Disease Management', 'Soil Health', etc.
                  If not provided, searches across all categories.
    
    Returns:
        Formatted information with sources and relevance scores.
        Each result includes the source document name, category, relevance score,
        and relevant text excerpt.
    """
    # Get vector store with default path (relative to project root)
    import os
    from pathlib import Path
    project_root = Path(__file__).parent.parent.parent.parent
    db_path = str(project_root / "chroma_db")
    vector_store = get_vector_store(db_path=db_path)
    
    # Search for relevant chunks
    results = vector_store.search(
        query=query,
        top_k=5,
        category_filter=category
    )
    
    if not results:
        return f"No relevant information found for: {query}\n\nTry rephrasing your query or removing the category filter."
    
    # Format results
    output = f"**Search Results for:** {query}\n\n"
    
    for idx, result in enumerate(results[:3], 1):
        output += f"**Result {idx}:**\n"
        output += f"Source: {result['source']}\n"
        output += f"Category: {result['category']}\n"
        output += f"Relevance Score: {result['score']:.2f}\n"
        output += f"Content:\n{result['text'][:500]}"
        if len(result['text']) > 500:
            output += "..."
        output += "\n\n"
    
    if len(results) > 3:
        output += f"\n**Total relevant documents found:** {len(results)}"
    
    return output

