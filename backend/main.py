"""
Multi-Agent SQL Optimization Framework

A sophisticated database optimization system using 4 specialized AI agents.
Each agent focuses on a specific aspect of the optimization pipeline for maximum effectiveness.

Architecture:
- Agent 1: Query Analyzer (Structure + Complexity Extraction)
- Agent 2: Optimizer Generator (N Rewrites)
- Agent 3: Validator (Benchmark + Cost Comparison)
- Agent 4: Explainer (Human-Readable Explanations)
"""

import logging
import os
from typing import List, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agents import MultiAgentOrchestrator

# Configure logging for production
import sys
if os.environ.get('VERCEL'):
    # Vercel environment - only console logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
else:
    # Local development - file logging
    os.makedirs('logs', exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/optimizer.log')
        ]
    )
logger = logging.getLogger(__name__)

app = FastAPI(
    title="🧠 Multi-Agent SQL Optimization Framework",
    description="Advanced database optimization using 4 specialized AI agents",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize multi-agent orchestrator
orchestrator = MultiAgentOrchestrator()

class OptimizeRequest(BaseModel):
    """Request model for SQL optimization"""
    sql: str
    schema: List[Dict[str, str]] = []

class OptimizeResponse(BaseModel):
    """Response model for SQL optimization"""
    optimized_sql: str
    explanation: str
    agent_results: Dict = {}
    pipeline_performance: Dict = {}

@app.get("/debug")
async def debug():
    """Debug endpoint to check environment"""
    return {
        "environment": os.environ.get('VERCEL', 'local'),
        "api_key_set": bool(os.environ.get('GROQ_API_KEY')),
        "agents_loaded": list(orchestrator.agents.keys()),
        "working_dir": os.getcwd(),
        "python_path": sys.path[:3]  # First few entries
    }

@app.get("/")
async def root():
    """API root endpoint with framework information"""
    return {
        "message": "🧠 Multi-Agent SQL Optimization Framework",
        "description": "Advanced database optimization using 4 specialized AI agents",
        "version": "2.0.0",
        "architecture": {
            "agents": [
                "🔹 Agent 1 – Query Analyzer (Structure + Complexity Extraction)",
                "🔹 Agent 2 – Optimizer Generator (N Rewrites)", 
                "🔹 Agent 3 – Validator (Benchmark + Cost Comparison)",
                "🔹 Agent 4 – Explainer (Human-Readable Explanations)"
            ],
            "pipeline": "Sequential execution with error handling and result compilation"
        },
        "features": [
            "Multi-turn AI optimization",
            "Real-time agent status tracking",
            "Comprehensive performance metrics",
            "Human-readable explanations"
        ]
    }

@app.get("/api/optimize-sql/test")
def optimize_sql_test() -> OptimizeResponse:
    """Test endpoint for API connectivity"""
    return OptimizeResponse(
        optimized_sql="SELECT * FROM my_table LIMIT 10;  -- indexed scan",
        explanation="Mock: use LIMIT to avoid full scan; ensure my_table has an index on filter column.",
        agent_results={
            "analyzer": {"status": "completed", "execution_time_ms": 45.2},
            "optimizer": {"status": "completed", "execution_time_ms": 120.5, "candidates_generated": 3},
            "validator": {"status": "completed", "execution_time_ms": 89.1, "candidates_validated": 3},
            "explainer": {"status": "completed", "execution_time_ms": 67.3}
        },
        pipeline_performance={"total_time_ms": 322.1, "agents_completed": 4}
    )

@app.post("/api/optimize-sql/mock", response_model=OptimizeResponse)
async def optimize_sql_mock(req: OptimizeRequest) -> OptimizeResponse:
    """Mock optimization endpoint for testing"""
    return OptimizeResponse(
        optimized_sql=f"SELECT * FROM ({req.sql}) optimized_query LIMIT 1000",
        explanation="🧠 Multi-Agent Analysis Complete\n\nGenerated 3 optimization candidates, 3 passed validation.\n\n🏆 Best Optimization:\n• Performance improvement: 15.2%\n• Cost reduction: 450.0 → 382.5\n• Validation time: 2.1ms\n\n📋 Recommended changes:\n• Added LIMIT clause to prevent full table scans",
        agent_results={
            "analyzer": {
                "status": "completed",
                "execution_time_ms": 1.2,
                "analysis": {"has_joins": False, "has_subqueries": False, "has_aggregations": False, "has_filters": True, "has_sorting": False, "has_limit": False}
            },
            "optimizer": {
                "status": "completed", 
                "execution_time_ms": 120.5,
                "candidates_generated": 3
            },
            "validator": {
                "status": "completed",
                "execution_time_ms": 2.1,
                "candidates_validated": 3
            },
            "explainer": {
                "status": "completed",
                "execution_time_ms": 67.3,
                "recommendations": ["• Added LIMIT clause for better performance", "• Consider adding indexes on filter columns"]
            }
        },
        pipeline_performance={
            "total_time_ms": 191.1,
            "agents_completed": 4
        }
    )

@app.post("/api/optimize-sql", response_model=OptimizeResponse)
async def optimize_sql(req: OptimizeRequest) -> OptimizeResponse:
    """Main optimization endpoint using multi-agent pipeline"""
    try:
        logger.info(f"🚀 Starting multi-agent optimization for SQL: {req.sql[:100]}{'...' if len(req.sql) > 100 else ''}")
        
        # Run multi-agent optimization pipeline
        result = await orchestrator.optimize_sql(req.sql, req.schema)
        
        logger.info(f"✅ Multi-agent optimization completed in {result['pipeline_performance']['total_time_ms']:.1f}ms")
        
        return OptimizeResponse(
            optimized_sql=result['optimized_sql'],
            explanation=result['explanation'],
            agent_results=result['agent_results'],
            pipeline_performance=result['pipeline_performance']
        )
        
    except Exception as e:
        logger.error(f"❌ Multi-agent optimization failed: {str(e)}")
        raise RuntimeError(f"Multi-agent optimization failed: {str(e)}")

@app.get("/health")
def health() -> dict:
    """Health check endpoint"""
    return {
        "status": "ok", 
        "framework": "Multi-Agent SQL Optimizer",
        "version": "2.0.0",
        "agents": list(orchestrator.agents.keys())
    }

@app.get("/ready")
def ready() -> dict:
    """Ready check endpoint"""
    return {
        "ready": True, 
        "agents": list(orchestrator.agents.keys()),
        "framework": "Multi-Agent SQL Optimization Framework"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)