"""
Policy Navigator - Main Entry Point
Initializes and runs the Policy Navigator crew
"""

import os
import sys
import warnings
from pathlib import Path

# Suppress all warnings BEFORE any imports
# Suppress TensorFlow warnings
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TensorFlow INFO, WARNING, and ERROR messages

# Suppress Python warnings (TensorFlow-specific, unique to main.py)
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', message='.*oneDNN.*')
warnings.filterwarnings('ignore', message='.*tensorflow.*')

# Note: ChromaDB and CrewAI warning suppressions are handled in crew.py
# which is imported later. This avoids duplicate suppressions.

# Suppress specific logging warnings with custom handler
import logging

# Suppress other loggers
logging.getLogger('tensorflow').setLevel(logging.ERROR)
logging.getLogger('sentence_transformers').setLevel(logging.ERROR)
logging.getLogger('root').setLevel(logging.WARNING)  # Suppress INFO messages from root logger

# Add project root to path BEFORE any imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from policy_navigator.crew import PolicyNavigatorCrew
from policy_navigator.callbacks.execution_tracker import get_tracker
from typing import Optional


def handle_pdf_upload() -> Optional[str]:
    """
    Handle PDF upload with interactive prompts
    
    Returns:
        File path to PDF if uploaded, None otherwise
    """
    print("\n" + "-" * 80)
    upload_choice = input("Do you want to upload a PDF document? (yes/no): ").strip().lower()
    
    if upload_choice not in ['yes', 'y']:
        return None
    
    print("\nPlease provide the path to your PDF file:")
    print("(You can use absolute path or relative path from project root)")
    file_path = input("PDF file path: ").strip()
    
    if not file_path:
        print("⚠ No file path provided. Skipping PDF upload.")
        return None
    
    # Convert to Path object
    pdf_path = Path(file_path)
    
    # If relative path, try relative to project root
    if not pdf_path.is_absolute():
        pdf_path = project_root / pdf_path
    
    # Validate file exists
    if not pdf_path.exists():
        print(f"❌ Error: PDF file not found at {pdf_path}")
        print("Skipping PDF upload.")
        return None
    
    # Validate it's a PDF
    if pdf_path.suffix.lower() != '.pdf':
        print(f"⚠ Warning: File {pdf_path.name} does not have .pdf extension.")
        confirm = input("Do you want to proceed anyway? (yes/no): ").strip().lower()
        if confirm not in ['yes', 'y']:
            return None
    
    print(f"✓ PDF file found: {pdf_path.name}")
    return str(pdf_path)


def initialize_rag_database():
    """Initialize ChromaDB with documents if not already done"""
    from policy_navigator.retrieval.document_processor import DocumentProcessor
    from policy_navigator.retrieval.vector_store import get_vector_store
    
    # Use absolute path for ChromaDB
    db_path = str(project_root / "chroma_db")
    vector_store = get_vector_store(db_path=db_path)
    
    # Check if database already has documents
    if vector_store.get_collection_count() > 0:
        print(f"✓ Vector store already initialized with {vector_store.get_collection_count()} chunks")
        return
    
    print("Initializing RAG database...")
    print("This may take a few minutes for the first run...")
    
    # Process all documents
    processor = DocumentProcessor(data_path=project_root / "data")
    documents = processor.process_all_documents()
    
    if documents:
        # Add to vector store
        vector_store.add_documents(documents)
        print(f"✓ Successfully loaded {len(documents)} document chunks into vector store")
    else:
        print("⚠ Warning: No documents found to process")


def main():
    """Main function to run the Policy Navigator"""
    print("=" * 80)
    print("Policy Navigator - Multi-Agent System")
    print("=" * 80)
    print()
    
    # Initialize RAG database
    try:
        initialize_rag_database()
    except Exception as e:
        print(f"⚠ Warning: Could not initialize RAG database: {e}")
        print("Continuing without RAG initialization...")
    
    print()
    
    # Initialize crew
    print("Initializing Policy Navigator Crew...")
    crew_instance = PolicyNavigatorCrew()
    crew = crew_instance.crew()
    
    print("✓ Crew initialized successfully")
    print()
    
    # Get user query
    print("Enter your agricultural query (or 'quit' to exit):")
    print("-" * 80)
    
    while True:
        user_query = input("\nQuery: ").strip()
        
        if user_query.lower() in ['quit', 'exit', 'q']:
            print("\nThank you for using Policy Navigator!")
            break
        
        if not user_query:
            print("Please enter a valid query.")
            continue
        
        # Handle PDF upload
        pdf_path = handle_pdf_upload()
        
        print("\n" + "=" * 80)
        print("Processing your query...")
        if pdf_path:
            print(f"Processing PDF: {Path(pdf_path).name}")
        print("=" * 80)
        print()
        
        try:
            # Reset execution tracker for new query
            tracker = get_tracker()
            tracker.reset()
            
            # Prepare inputs for crew
            # Always include pdf_file_path to avoid template interpolation errors
            # Set to empty string if no PDF is uploaded (conditional task will handle this)
            inputs = {
                "user_query": user_query,
                "pdf_file_path": pdf_path if pdf_path else ""
            }
            
            # Execute crew with user query and optional PDF
            result = crew.kickoff(inputs=inputs)
            
            print("\n" + "=" * 80)
            print("RESULT")
            print("=" * 80)
            print()
            
            # Display result
            if hasattr(result, 'pydantic') and result.pydantic:
                # Structured output available
                final_response = result.pydantic
                
                # For out-of-scope queries, only show plain text
                if hasattr(final_response, 'is_out_of_scope') and final_response.is_out_of_scope:
                    print(final_response.response_text)
                else:
                    # For in-scope queries, show markdown (which already includes sources and follow-up)
                    if final_response.response_markdown:
                        print(final_response.response_markdown)
                    else:
                        # Fallback to plain text if markdown not available
                        print(final_response.response_text)
            else:
                # Raw output
                print(result.raw if hasattr(result, 'raw') else str(result))
            
            # Display execution tracker information
            print("\n" + "-" * 80)
            print("EXECUTION SUMMARY")
            print("-" * 80)
            
            executed_agents = tracker.get_executed_agents()
            used_tools = tracker.get_used_tools()
            agent_tools = tracker.get_agent_tools()
            
            # Agent display names mapping
            agent_display_names = {
                'query_analyzer': 'Query Analyzer',
                'policy_researcher': 'Policy Researcher',
                'crop_specialist': 'Crop Specialist',
                'pest_advisor': 'Pest Advisor',
                'market_analyst': 'Market Analyst',
                'non_ap_researcher': 'Non-AP Researcher',
                'response_synthesizer': 'Response Synthesizer'
            }
            
            if executed_agents:
                print("\nAgents Executed:")
                for agent in executed_agents:
                    # Format agent name for display
                    agent_display = agent_display_names.get(agent, agent.replace('_', ' ').title())
                    print(f"  • {agent_display}")
                    # Show tools used by this agent
                    if agent in agent_tools and agent_tools[agent]:
                        tools_used = agent_tools[agent]
                        tools_display = ", ".join(tools_used)
                        print(f"    └─ Tools: {tools_display}")
            else:
                print("\nAgents Executed: None")
            
            if used_tools:
                print(f"\nTotal Tools Used: {len(used_tools)}")
                print("All Tools:")
                for tool in used_tools:
                    print(f"  • {tool}")
            else:
                print("\nTotal Tools Used: 0")
            
            print("\n" + "=" * 80)
            print()
            
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user.")
            break
        except Exception as e:
            print(f"\n❌ Error processing query: {e}")
            import traceback
            traceback.print_exc()
            print()


if __name__ == "__main__":
    main()

