import flask
import json
import time

a = 6
b = 7 
c = a + b
print("niger")
# Simple in-memory storage
scripts = {}

def handler(event, context):
    path = event.get('path', '/')
    method = event.get('httpMethod', 'GET')
    
    # Handle CORS preflight
    if method == 'OPTIONS':
        return {
            'statusCode': 204,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            }
        }
    
    # Home endpoint
    if path == '/':
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                "status": "Flask Proxy Running",
                "endpoints": ["/execute", "/script/:id", "/all", "/clear", "/status"]
            })
        }
    
    # Status endpoint
    if path == '/status' and method == 'GET':
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                "online": True,
                "scripts": len(scripts)
            })
        }
    
    # Execute endpoint
    if path == '/execute' and method == 'POST':
        try:
            body = json.loads(event.get('body', '{}'))
            script = body.get('script', '')
            player = body.get('player', 'Unknown')
            
            script_id = str(int(time.time() * 1000))
            scripts[script_id] = {
                "script": script,
                "player": player,
                "time": time.time()
            }
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    "success": True,
                    "id": script_id
                })
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'body': json.dumps({"error": str(e)})
            }
    
    # Get script by ID
    if path.startswith('/script/') and method == 'GET':
        script_id = path.split('/script/')[1]
        if script_id in scripts:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(scripts[script_id])
            }
        else:
            return {
                'statusCode': 404,
                'body': json.dumps({"error": "Not found"})
            }
    
    # List all scripts
    if path == '/all' and method == 'GET':
        result = {}
        for sid, data in scripts.items():
            result[sid] = {
                "player": data["player"],
                "preview": data["script"][:50] + ("..." if len(data["script"]) > 50 else "")
            }
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                "count": len(result),
                "scripts": result
            })
        }
    
    # Clear all scripts
    if path == '/clear' and method == 'POST':
        scripts.clear()
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({"success": True})
        }
    
    # 404 for unknown routes
    return {
        'statusCode': 404,
        'body': json.dumps({"error": "Endpoint not found"})
    }
