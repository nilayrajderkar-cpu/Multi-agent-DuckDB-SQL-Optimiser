"""
Vercel Serverless Function for SQL Optimization
"""
import sys
import os
import json
from typing import Dict, List

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from agents import MultiAgentOrchestrator

def handler(request):
    """Vercel serverless handler"""
    try:
        # Handle CORS preflight
        if request.method == 'OPTIONS':
            return {
                "statusCode": 200,
                "headers": {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type",
                },
                "body": ""
            }
        
        # Parse request body
        if request.method != 'POST':
            return {
                "statusCode": 405,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({"error": "Method not allowed"})
            }
        
        body = json.loads(request.body)
        sql = body.get('sql', '')
        schema = body.get('schema', [])
        
        if not sql:
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({"error": "SQL query is required"})
            }
        
        # Initialize orchestrator
        orchestrator = MultiAgentOrchestrator()
        
        # Run multi-agent optimization (synchronous for Vercel)
        import asyncio
        result = asyncio.run(orchestrator.optimize_sql(sql, schema))
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps(result)
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
