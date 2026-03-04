"""
Multi-Agent Orchestrator

Coordinates the execution of all agents in the SQL optimization pipeline.
Manages agent lifecycle, data flow, and result compilation.
"""

import logging
from typing import Dict, Any

from .base_agent import AgentStatus
from .query_analyzer import QueryAnalyzerAgent
from .optimizer_generator import OptimizerGeneratorAgent
from .validator import ValidatorAgent
from .explainer import ExplainerAgent

logger = logging.getLogger(__name__)

class MultiAgentOrchestrator:
    """Orchestrates the multi-agent SQL optimization pipeline"""
    
    def __init__(self):
        self.agents = {
            'analyzer': QueryAnalyzerAgent(),
            'optimizer': OptimizerGeneratorAgent(),
            'validator': ValidatorAgent(),
            'explainer': ExplainerAgent()
        }
        self.results = {}
    
    async def optimize_sql(self, sql: str, schema: List[Dict[str, str]]) -> Dict[str, Any]:
        """Run the complete multi-agent optimization pipeline"""
        
        logger.info("🚀 Starting Multi-Agent SQL Optimization Pipeline")
        logger.info(f"📝 Query: {sql[:100]}{'...' if len(sql) > 100 else ''}")
        
        # Agent 1: Query Analysis
        logger.info("🔹 Agent 1: Analyzing query structure and complexity")
        analysis_result = await self.agents['analyzer'].execute(sql, schema)
        self.results['analyzer'] = analysis_result
        
        if analysis_result.status != AgentStatus.COMPLETED:
            raise Exception(f"Query analysis failed: {analysis_result.error_message}")
        
        analysis = analysis_result.result
        
        # Agent 2: Generate Optimization Candidates
        logger.info("🔹 Agent 2: Generating optimization candidates")
        optimizer_result = await self.agents['optimizer'].execute(sql, schema, analysis)
        self.results['optimizer'] = optimizer_result
        
        if optimizer_result.status != AgentStatus.COMPLETED:
            raise Exception(f"Optimization generation failed: {optimizer_result.error_message}")
        
        candidates = optimizer_result.result
        
        # Agent 3: Validate Candidates
        logger.info("🔹 Agent 3: Validating optimization candidates")
        validation_result = await self.agents['validator'].execute(sql, candidates)
        self.results['validator'] = validation_result
        
        if validation_result.status != AgentStatus.COMPLETED:
            raise Exception(f"Validation failed: {validation_result.error_message}")
        
        validated_candidates = validation_result.result
        
        # Agent 4: Generate Explanations
        logger.info("🔹 Agent 4: Generating human-readable explanations")
        explanation_result = await self.agents['explainer'].execute(sql, validated_candidates)
        self.results['explainer'] = explanation_result
        
        if explanation_result.status != AgentStatus.COMPLETED:
            raise Exception(f"Explanation generation failed: {explanation_result.error_message}")
        
        explanation_data = explanation_result.result
        
        # Compile final results
        final_result = self._compile_results()
        
        logger.info("✅ Multi-Agent Optimization Pipeline Completed Successfully")
        logger.info(f"📊 Pipeline Performance: {final_result['pipeline_performance']['total_time_ms']:.1f}ms total")
        
        return final_result
    
    def _compile_results(self) -> Dict[str, Any]:
        """Compile results from all agents into final response"""
        
        analyzer_result = self.results['analyzer'].result if self.results['analyzer'].result else {}
        optimizer_result = self.results['optimizer'].result if self.results['optimizer'].result else []
        validation_result = self.results['validator'].result if self.results['validator'].result else []
        explanation_result = self.results['explainer'].result if self.results['explainer'].result else {}
        
        # Get best candidate
        best_candidate = explanation_result.get('best_candidate')
        optimized_sql = ""
        explanation = ""
        
        if best_candidate:
            candidate, validation = best_candidate
            optimized_sql = candidate.sql
            explanation = explanation_result.get('summary', '')
        else:
            optimized_sql = "No optimization recommended"
            explanation = explanation_result.get('summary', 'No optimizations available')
        
        return {
            'optimized_sql': optimized_sql,
            'explanation': explanation,
            'agent_results': {
                'analyzer': {
                    'status': self.results['analyzer'].status.value,
                    'execution_time_ms': self.results['analyzer'].execution_time_ms,
                    'analysis': analyzer_result.structure if analyzer_result else None
                },
                'optimizer': {
                    'status': self.results['optimizer'].status.value,
                    'execution_time_ms': self.results['optimizer'].execution_time_ms,
                    'candidates_generated': len(optimizer_result) if optimizer_result else 0
                },
                'validator': {
                    'status': self.results['validator'].status.value,
                    'execution_time_ms': self.results['validator'].execution_time_ms,
                    'candidates_validated': len(validation_result) if validation_result else 0
                },
                'explainer': {
                    'status': self.results['explainer'].status.value,
                    'execution_time_ms': self.results['explainer'].execution_time_ms,
                    'recommendations': explanation_result.get('recommendations', []) if explanation_result else []
                }
            },
            'pipeline_performance': {
                'total_time_ms': sum(result.execution_time_ms for result in self.results.values()),
                'agents_completed': sum(1 for result in self.results.values() if result.status == AgentStatus.COMPLETED)
            }
        }
