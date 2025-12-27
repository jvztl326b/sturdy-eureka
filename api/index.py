# api/index.py - Vercel-compatible Flask app
from flask import Flask, request, jsonify
from flask_cors import CORS
import time

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Store scripts temporarily
script_store = {}

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "Flask Proxy Running on Vercel",
        "warning": "NO AUTHENTICATION",
        "endpoints": [
            "GET  /status",
            "POST /execute",
            "GET  /script/<id>",
            "GET  /all",
            "POST /clear"
        ]
    })

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        "status": "online",
        "scripts": len(script_store),
        "server": "Flask on Vercel"
    })

@app.route('/execute', methods=['POST'])
def execute():
    try:
        data = request.get_json()
        script = data.get('script', '')
        player = data.get('player', 'Unknown')
        
        if not script:
            return jsonify({"error": "No script"}), 400
        
        script_id = str(int(time.time() * 1000))
        script_store[script_id] = {
            "script": script,
            "player": player,
            "time": time.time()
        }
        
        # Clean old scripts (>5 mins)
        current = time.time()
        for sid in list(script_store.keys()):
            if current - script_store[sid]["time"] > 300:
                del script_store[sid]
        
        return jsonify({
            "id": script_id,
            "success": True,
            "message": "Script stored"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/script/<script_id>', methods=['GET'])
def get_script(script_id):
    if script_id in script_store:
        return jsonify(script_store[script_id])
    return jsonify({"error": "Not found"}), 404

@app.route('/all', methods=['GET'])
def all_scripts():
    scripts = {}
    for sid, data in script_store.items():
        scripts[sid] = {
            "player": data["player"],
            "preview": data["script"][:50] + ("..." if len(data["script"]) > 50 else "")
        }
    
    return jsonify({
        "count": len(scripts),
        "scripts": scripts
    })

@app.route('/clear', methods=['POST'])
def clear():
    script_store.clear()
    return jsonify({"success": True, "message": "All scripts cleared"})

# Vercel requires this handler
def handler(event, context):
    from flask import make_response
    import json
    
    # Parse Vercel event
    path = event.get('path', '/')
    method = event.get('httpMethod', 'GET')
    query = event.get('queryStringParameters', {}) or {}
    body = event.get('body', '{}')
    headers = event.get('headers', {})
    
    # Create mock request
    with app.test_request_context(
        path=path,
        method=method,
        query_string=query,
        data=body,
        headers=headers
    ):
        # Dispatch request
        response = app.full_dispatch_request()
        
        # Return Vercel format
        return {
            'statusCode': response.status_code,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': response.get_data(as_text=True)
        }
