"""
Script to initialize ChromaDB with agricultural documents
Run this script once to populate the vector database
"""

import os
import sys
import warnings
import logging
from pathlib import Path

# Suppress all warnings BEFORE any imports
# Suppress TensorFlow warnings
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Suppress Python warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', message='.*oneDNN.*')
warnings.filterwarnings('ignore', message='.*tensorflow.*')
# Suppress ChromaDB deprecation warning about CHROMA_OPENAI_API_KEY (we use SentenceTransformer, not OpenAI)
warnings.filterwarnings('ignore', category=DeprecationWarning, module='chromadb')
warnings.filterwarnings('ignore', message='.*CHROMA_OPENAI_API_KEY.*')
warnings.filterwarnings('ignore', message='.*legacy embedding function.*')
warnings.filterwarnings('ignore', message='.*collection_configuration.*')
warnings.filterwarnings('ignore', message='.*Direct api_key configuration.*')
warnings.filterwarnings('ignore', message='.*will not be persisted.*')

# Suppress ChromaDB telemetry errors
os.environ['ANONYMIZED_TELEMETRY'] = 'False'
logging.getLogger('tensorflow').setLevel(logging.ERROR)
logging.getLogger('chromadb.telemetry').setLevel(logging.ERROR)
logging.getLogger('chromadb.telemetry.product.posthog').setLevel(logging.ERROR)

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from policy_navigator.retrieval.document_processor import DocumentProcessor
from policy_navigator.retrieval.vector_store import get_vector_store


def main():
    """Initialize RAG database"""
    print("=" * 80)
    print("Initializing RAG Database for Policy Navigator")
    print("=" * 80)
    print()
    
    # Get data path
    data_path = project_root / "data"
    
    if not data_path.exists():
        print(f"Error: Data directory not found at {data_path}")
        return
    
    print(f"Data directory: {data_path}")
    print()
    
    # Initialize vector store
    print("Initializing vector store...")
    vector_store = get_vector_store(db_path=str(project_root / "chroma_db"))
    
    # Check if already populated
    count = vector_store.get_collection_count()
    if count > 0:
        print(f"Vector store already contains {count} chunks.")
        response = input("Do you want to reinitialize? (yes/no): ").strip().lower()
        if response != 'yes':
            print("Skipping initialization.")
            return
        print("Clearing existing collection...")
        vector_store.clear_collection()
    
    # Process documents
    print("Processing documents...")
    processor = DocumentProcessor(data_path=str(data_path))
    documents = processor.process_all_documents()
    
    if not documents:
        print("No documents found to process.")
        return
    
    print(f"Processed {len(documents)} document chunks")
    print()
    
    # Add to vector store
    print("Adding documents to vector store...")
    vector_store.add_documents(documents)
    
    # Verify
    final_count = vector_store.get_collection_count()
    print()
    print("=" * 80)
    print(f"✓ Successfully initialized RAG database with {final_count} chunks")
    print("=" * 80)


if __name__ == "__main__":
    main()

