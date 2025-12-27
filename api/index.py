# api/index.py - Flask app for Vercel
from flask import Flask, request, jsonify
import time
import json

# Initialize Flask app
app = Flask(__name__)

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
        }
    })

@app.route('/execute', methods=['POST', 'GET'])
def execute_script():
    """Accept scripts from ANYONE - NO AUTH REQUIRED"""
    try:
        # Handle both POST and GET for flexibility
        if request.method == 'GET':
            script = request.args.get('script')
            player = request.args.get('player', 'Unknown')
        else:
            data = request.get_json(silent=True) or {}
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
            "ip": request.remote_addr or 'unknown'
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
            "message": "Script stored - anyone can retrieve it"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/script/<script_id>', methods=['GET'])
def get_script(script_id):
    """Retrieve script - NO AUTH REQUIRED"""
    if script_id in script_store:
        return jsonify(script_store[script_id])
    return jsonify({"error": "Script not found"}), 404

@app.route('/script/<script_id>', methods=['DELETE'])
def delete_script(script_id):
    """Delete script - NO AUTH REQUIRED"""
    if script_id in script_store:
        del script_store[script_id]
        return jsonify({"status": "deleted"})
    return jsonify({"error": "Script not found"}), 404

@app.route('/all', methods=['GET'])
def list_all():
    """List all scripts - WARNING: PUBLIC"""
    return jsonify({
        "count": len(script_store),
        "scripts": {k: {"player": v["player"], "preview": v["script"][:50]} 
                   for k, v in script_store.items()}
    })

@app.route('/clear', methods=['POST'])
def clear_all():
    """Clear all scripts - NO AUTH"""
    script_store.clear()
    return jsonify({"status": "all scripts cleared"})

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        "status": "open proxy running",
        "scripts_stored": len(script_store),
        "uptime": time.time(),
        "warning": "NO AUTHENTICATION REQUIRED"
    })

# CORS headers
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# This is required for Vercel
def handler(event, context):
    return app(event, context)
