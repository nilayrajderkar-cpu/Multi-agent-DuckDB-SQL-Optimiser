"""
Vercel Serverless Function for Multi-Agent SQL Optimizer
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from main import app
from fastapi.responses import JSONResponse

# Vercel serverless handler
def handler(request):
    """Handle Vercel serverless requests"""
    return JSONResponse({"message": "Multi-Agent SQL Optimizer API", "status": "ready"})
