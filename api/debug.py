"""
Debug endpoint for Vercel
"""
import sys
import os
import json

def handler(event, context):
    """Debug endpoint"""
    try:
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "message": "Debug endpoint working!",
                "environment": os.environ.get('VERCEL', 'local'),
                "api_key_set": bool(os.environ.get('GROQ_API_KEY')),
                "working_dir": os.getcwd(),
                "python_path": sys.path[:5],
                "event": event
            })
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"error": str(e)})
        }
