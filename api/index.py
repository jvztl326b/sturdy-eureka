# api/index.py - Vercel-compatible Flask app
from flask import Flask, request, jsonify
import time
import json

# Initialize Flask app
app = Flask(__name__)

# Store scripts temporarily
script_store = {}

@app.route('/', methods=['GET'])
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

@app.route('/execute', methods=['POST', 'GET', 'OPTIONS'])
def execute_script():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        if request.method == 'GET':
            script = request.args.get('script')
            player = request.args.get('player', 'Unknown')
        else:
            data = request.get_json(silent=True) or {}
            script = data.get('script') or request.form.get('script')
            player = data.get('player', 'Unknown')
        
        if not script:
            return jsonify({"error": "No script provided"}), 400
        
        script_id = str(int(time.time() * 1000))
        script_store[script_id] = {
            "script": script,
            "player": player,
            "timestamp": time.time()
        }
        
        return jsonify({
            "status": "success",
            "id": script_id,
            "message": "Script stored"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/script/<script_id>', methods=['GET', 'OPTIONS'])
def get_script(script_id):
    if request.method == 'OPTIONS':
        return '', 204
    
    if script_id in script_store:
        return jsonify(script_store[script_id])
    return jsonify({"error": "Script not found"}), 404

@app.route('/all', methods=['GET', 'OPTIONS'])
def list_all():
    if request.method == 'OPTIONS':
        return '', 204
    
    return jsonify({
        "count": len(script_store),
        "scripts": {k: {"player": v["player"], "preview": v["script"][:50]} 
                   for k, v in script_store.items()}
    })

@app.route('/clear', methods=['POST', 'OPTIONS'])
def clear_all():
    if request.method == 'OPTIONS':
        return '', 204
    
    script_store.clear()
    return jsonify({"status": "all scripts cleared"})

@app.route('/status', methods=['GET', 'OPTIONS'])
def status():
    if request.method == 'OPTIONS':
        return '', 204
    
    return jsonify({
        "status": "open proxy running",
        "scripts_stored": len(script_store)
    })

# CORS headers middleware
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    return response

# Vercel requires this handler
def handler(event, context):
    return app(event, context)
