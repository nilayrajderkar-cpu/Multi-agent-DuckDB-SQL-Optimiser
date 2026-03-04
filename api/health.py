"""
Vercel Serverless Function for Health Check
"""
def handler(request):
    """Health check endpoint"""
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": '{"status": "ok", "framework": "Multi-Agent SQL Optimizer", "version": "2.0.0"}'
    }
