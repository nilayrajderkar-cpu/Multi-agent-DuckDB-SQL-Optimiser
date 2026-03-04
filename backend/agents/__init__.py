"""
Multi-Agent SQL Optimization Framework

This package contains the core multi-agent architecture for SQL optimization.
Each agent specializes in a specific aspect of the optimization pipeline.

Agents:
- QueryAnalyzerAgent: Analyzes query structure and complexity
- OptimizerGeneratorAgent: Generates optimization candidates
- ValidatorAgent: Validates and benchmarks candidates
- ExplainerAgent: Generates human-readable explanations
"""

from .base_agent import BaseAgent, AgentStatus, AgentResult
from .query_analyzer import QueryAnalyzerAgent
from .optimizer_generator import OptimizerGeneratorAgent
from .validator import ValidatorAgent
from .explainer import ExplainerAgent
from .orchestrator import MultiAgentOrchestrator

__all__ = [
    'BaseAgent',
    'AgentStatus', 
    'AgentResult',
    'QueryAnalyzerAgent',
    'OptimizerGeneratorAgent',
    'ValidatorAgent',
    'ExplainerAgent',
    'MultiAgentOrchestrator'
]
