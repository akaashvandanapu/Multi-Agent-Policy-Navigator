"""
Flask API Backend for Policy Navigator
Handles all agent orchestration and provides REST endpoints
"""

import os
import sys
from pathlib import Path

# Add project root and src directory to path
# Use resolve() to get absolute paths
project_root = Path(__file__).resolve().parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

# Load environment variables BEFORE any other imports
from dotenv import load_dotenv
load_dotenv(override=True)

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import traceback

# Configure logging with detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global orchestrator instance (lazy loaded)
orchestrator = None

def get_orchestrator():
    """Lazy load orchestrator to handle import errors gracefully"""
    global orchestrator
    if orchestrator is None:
        try:
            # Debug: Log paths
            logger.info(f"📁 Project root: {project_root}")
            logger.info(f"📁 Src path: {src_path}")
            logger.info(f"📁 Python path: {sys.path[:3]}")
            
            # Import here to catch errors
            from policy_navigator.core.orchestrator import MainOrchestrator
            logger.info("✅ Successfully imported MainOrchestrator")
            
            orchestrator = MainOrchestrator()
            logger.info("✅ Orchestrator initialized successfully")
        except ImportError as e:
            logger.error(f"❌ Import error: {e}")
            logger.error(f"❌ Python path: {sys.path}")
            logger.error(f"❌ Project root exists: {project_root.exists()}")
            logger.error(f"❌ Src path exists: {src_path.exists()}")
            logger.error(f"❌ Policy navigator exists: {(src_path / 'policy_navigator').exists()}")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to initialize orchestrator: {e}")
            logger.error(traceback.format_exc())
            raise
    return orchestrator

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint - doesn't initialize orchestrator"""
    return jsonify({
        'status': 'healthy',
        'backend': 'api_ready',
        'agents': 7,
        'tools': 4,
        'note': 'Orchestrator loads on first query'
    }), 200

@app.route('/query', methods=['POST'])
def process_query():
    """Process user query through agent pipeline"""
    try:
        # Log incoming request
        logger.info("="*80)
        logger.info("📥 INCOMING API REQUEST: /query")
        logger.info("="*80)
        
        data = request.get_json()
        query = data.get('query', '')
        user_id = data.get('user_id', 'default_user')
        session_id = data.get('session_id', None)
        
        logger.info(f"📝 Query: {query}")
        logger.info(f"👤 User ID: {user_id}")
        logger.info(f"🔑 Session ID: {session_id}")
        
        if not query:
            logger.warning("❌ Query is empty")
            return jsonify({'error': 'Query is required'}), 400
        
        # Get orchestrator
        logger.info("🔄 Getting orchestrator instance...")
        orch = get_orchestrator()
        
        # Process query through orchestrator
        logger.info("🚀 Starting query processing through orchestrator...")
        result_dict = orch.process_query(
            user_query=query,
            user_id=user_id,
            session_id=session_id
        )
        
        logger.info("✅ Orchestrator returned result")
        logger.info(f"📊 Result type: {type(result_dict)}")
        
        # Log result structure
        logger.info("📋 Result structure:")
        logger.info(f"   - Has 'query': {'query' in result_dict}")
        logger.info(f"   - Has 'response_text': {'response_text' in result_dict}")
        logger.info(f"   - Has 'response_markdown': {'response_markdown' in result_dict}")
        logger.info(f"   - Has 'workflow_info': {'workflow_info' in result_dict}")
        logger.info(f"   - Has 'workflow_details': {'workflow_details' in result_dict}")
        
        # Log workflow_details if present
        if 'workflow_details' in result_dict:
            workflow_details = result_dict.get('workflow_details', {})
            if isinstance(workflow_details, dict):
                logger.info(f"   - workflow_details.agents count: {len(workflow_details.get('agents', []))}")
                logger.info(f"   - workflow_details.fallbacks count: {len(workflow_details.get('fallbacks', []))}")
                logger.info(f"   - workflow_details.requirements_met: {workflow_details.get('requirements_met', {})}")
        
        # Ensure workflow_details is present (orchestrator should provide it, but add fallback)
        if 'workflow_details' not in result_dict:
            logger.warning("⚠️  workflow_details not found in result_dict, setting empty dict")
            result_dict['workflow_details'] = {}
        
        # Ensure workflow_info is present
        if 'workflow_info' not in result_dict:
            logger.warning("⚠️  workflow_info not found in result_dict, setting empty string")
            result_dict['workflow_info'] = ''
        
        logger.info("="*80)
        logger.info("📤 SENDING API RESPONSE")
        logger.info("="*80)
        
        return jsonify({
            'success': True,
            'result': result_dict
        }), 200
        
    except Exception as e:
        logger.error("="*80)
        logger.error("❌ ERROR PROCESSING QUERY")
        logger.error("="*80)
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error("Full traceback:")
        logger.error(traceback.format_exc())
        logger.error("="*80)
        
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }), 500

@app.route('/upload', methods=['POST'])
def upload_document():
    """Handle document upload and verification"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        query = request.form.get('query', '')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Save file temporarily
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name
        
        logger.info(f"Processing uploaded file: {file.filename}")
        
        # Get orchestrator
        orch = get_orchestrator()
        
        # Process document (returns dict with success, response, validation_result, metadata)
        result = orch.process_document_upload(tmp_path, query)
        
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except Exception as e:
            logger.warning(f"Could not delete temp file {tmp_path}: {e}")
        
        # Return in format expected by frontend (same as /query endpoint)
        # Frontend expects result.response_markdown or result.response_text
        if result.get('success', False):
            # Check if result contains full result structure
            if 'result' in result:
                # Full result structure available - return like /query endpoint
                return jsonify({
                    'success': True,
                    'result': result['result']
                }), 200
            else:
                # Fallback: construct result structure from available data
                metadata = result.get('metadata', {})
                return jsonify({
                    'success': True,
                    'result': {
                        'query': query or "Summarize this agricultural policy document",
                        'response_text': result.get('response', ''),
                        'response_markdown': metadata.get('response_markdown', result.get('response', '')),
                        'workflow_details': metadata.get('workflow_details', {}),
                        'workflow_info': metadata.get('workflow_info', ''),
                        'sources': metadata.get('sources', []),
                        'confidence_score': metadata.get('confidence_score', 0.95),
                        'validation_result': result.get('validation_result'),
                        'metadata': metadata
                    }
                }), 200
        else:
            # Error case
            return jsonify({
                'success': False,
                'error': result.get('response', 'Document upload failed'),
                'validation_result': result.get('validation_result')
            }), 400
        
    except Exception as e:
        logger.error(f"Error processing upload: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/agents', methods=['GET'])
def get_agents_info():
    """Get information about available agents"""
    return jsonify({
        'agents': [
            {'id': 1, 'name': 'Query Understanding', 'type': 'CrewAI'},
            {'id': 2, 'name': 'Policy Retrieval', 'type': 'CrewAI'},
            {'id': 3, 'name': 'Realtime Information', 'type': 'CrewAI'},
            {'id': 4, 'name': 'Pest Management', 'type': 'CrewAI'},
            {'id': 5, 'name': 'Crop Cultivation', 'type': 'Google ADK'},
            {'id': 6, 'name': 'Document Verification', 'type': 'Google ADK'},
            {'id': 7, 'name': 'Response Synthesis', 'type': 'CrewAI'}
        ],
        'tools': [
            'Policy Retrieval Tool',
            'Crop Information Tool',
            'Ollama Web Search MCP',
            'Document Upload Handler'
        ]
    }), 200

@app.route('/', methods=['GET'])
def index():
    """API info endpoint"""
    return jsonify({
        'name': 'Policy Navigator API',
        'version': '1.0',
        'endpoints': {
            'health': '/health',
            'query': '/query (POST)',
            'upload': '/upload (POST)',
            'agents': '/agents'
        }
    }), 200

if __name__ == '__main__':
    print("\n" + "="*80)
    print("🚀 Policy Navigator Flask API")
    print("="*80)
    print("\n📍 Starting server on http://localhost:5000")
    print("\n🔗 Endpoints:")
    print("   - GET  /health  - Health check")
    print("   - POST /query   - Process user query")
    print("   - POST /upload  - Upload document")
    print("   - GET  /agents  - Get agents info")
    print("\n" + "="*80 + "\n")
    
    # Disable reloader on Windows to avoid socket errors
    # Set USE_RELOADER=1 in .env to enable reloader (not recommended on Windows)
    use_reloader = os.getenv('USE_RELOADER', '0').lower() in ('1', 'true', 'yes')
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=use_reloader)

