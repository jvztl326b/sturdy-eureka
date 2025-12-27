# api/index.py - Flask app for Vercel deployment
from flask import Flask, request, jsonify
from flask_cors import CORS
import time
import os

app = Flask(__name__)
CORS(app)  # Allow requests from anywhere

# Store scripts temporarily
script_store = {}

@app.route('/')
def home():
    return jsonify({
        "status": "open proxy - no auth",
        "warning": "THIS IS PUBLICLY ACCESSIBLE",
        "endpoints": {
            "execute": "POST /execute",
            "get_script": "GET /script/<id>",
            "delete": "DELETE /script/<id>",
            "list_all": "GET /all",
            "clear": "POST /clear",
            "status": "GET /status"
        },
        "example_usage": "/execute?script=print('Hello')&player=User"
    })

@app.route('/execute', methods=['POST', 'GET', 'OPTIONS'])
def execute_script():
    """Accept scripts from ANYONE - NO AUTH REQUIRED"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        # Handle both POST and GET for flexibility
        if request.method == 'GET':
            script = request.args.get('script')
            player = request.args.get('player', 'Unknown')
        else:
            data = request.get_json() or {}
            script = data.get('script') or request.form.get('script')
            player = data.get('player', 'Unknown')
        
        if not script:
            return jsonify({"error": "No script provided"}), 400
        
        # Generate ID
        script_id = str(int(time.time() * 1000))
        script_store[script_id] = {
            "script": script,
            "player": player,
            "timestamp": time.time(),
            "ip": request.remote_addr
        }
        
        # Clean old scripts (older than 5 minutes)
        current_time = time.time()
        expired = [k for k, v in script_store.items() 
                  if current_time - v["timestamp"] > 300]
        for key in expired:
            del script_store[key]
        
        return jsonify({
            "status": "success",
            "id": script_id,
            "script": script[:100] + ("..." if len(script) > 100 else ""),
            "message": "Script stored - anyone can retrieve it",
            "url": f"/script/{script_id}"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/script/<script_id>', methods=['GET', 'OPTIONS'])
def get_script(script_id):
    """Retrieve script - NO AUTH REQUIRED"""
    if request.method == 'OPTIONS':
        return '', 200
    
    if script_id in script_store:
        return jsonify(script_store[script_id])
    return jsonify({"error": "Script not found"}), 404

@app.route('/script/<script_id>', methods=['DELETE', 'OPTIONS'])
def delete_script(script_id):
    """Delete script - NO AUTH REQUIRED"""
    if request.method == 'OPTIONS':
        return '', 200
    
    if script_id in script_store:
        del script_store[script_id]
        return jsonify({"status": "deleted"})
    return jsonify({"error": "Script not found"}), 404

@app.route('/all', methods=['GET', 'OPTIONS'])
def list_all():
    """List all scripts - WARNING: PUBLIC"""
    if request.method == 'OPTIONS':
        return '', 200
    
    return jsonify({
        "count": len(script_store),
        "scripts": {k: {"player": v["player"], "preview": v["script"][:50]} 
                   for k, v in script_store.items()}
    })

@app.route('/clear', methods=['POST', 'OPTIONS'])
def clear_all():
    """Clear all scripts - NO AUTH"""
    if request.method == 'OPTIONS':
        return '', 200
    
    script_store.clear()
    return jsonify({"status": "all scripts cleared"})

@app.route('/status', methods=['GET', 'OPTIONS'])
def status():
    if request.method == 'OPTIONS':
        return '', 200
    
    return jsonify({
        "status": "open proxy running",
        "scripts_stored": len(script_store),
        "uptime": time.time(),
        "warning": "NO AUTHENTICATION REQUIRED",
        "server_time": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check for Vercel"""
    return jsonify({
        "status": "healthy",
        "timestamp": time.time()
    })

# Vercel serverless function handler
def handler(event, context):
    from flask import make_response
    import json
    
    # Parse the event
    path = event.get('path', '/')
    method = event.get('httpMethod', 'GET')
    query_params = event.get('queryStringParameters', {}) or {}
    body = event.get('body', '{}')
    
    # Create a mock request
    with app.test_request_context(
        path=path,
        method=method,
        query_string=query_params,
        data=body,
        headers=event.get('headers', {})
    ):
        # Process the request
        response = app.full_dispatch_request()
        
        # Return Vercel-compatible response
        return {
            'statusCode': response.status_code,
            'headers': dict(response.headers),
            'body': response.get_data(as_text=True)
        }

# For local development
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port, debug=True)
