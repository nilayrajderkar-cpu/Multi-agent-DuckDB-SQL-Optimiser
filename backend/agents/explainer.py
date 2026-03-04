"""
Explainer Agent

Agent 4 in the multi-agent pipeline.
Generates human-readable explanations and comprehensive analysis reports.
Transforms technical validation results into actionable insights.
"""

from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass

from .base_agent import BaseAgent
from .optimizer_generator import OptimizationCandidate
from .validator import ValidationResult

class ExplainerAgent(BaseAgent):
    """Generates human-readable explanations"""
    
    def __init__(self):
        super().__init__("Explainer")
    
    async def _execute(self, original_sql: str, validated_candidates: List[Tuple[OptimizationCandidate, ValidationResult]]) -> Dict[str, Any]:
        """Generate human-readable explanations"""
        
        if not validated_candidates:
            return {
                "summary": "No optimizations were generated.",
                "recommendations": [],
                "best_candidate": None
            }
        
        # Find the best candidate (highest improvement that passed validation)
        best_candidate = None
        best_improvement = 0
        
        for candidate, validation in validated_candidates:
            if validation.validation_passed and validation.improvement_percentage > best_improvement:
                best_improvement = validation.improvement_percentage
                best_candidate = (candidate, validation)
        
        # Generate comprehensive explanation
        summary = await self._generate_summary(original_sql, validated_candidates, best_candidate)
        recommendations = await self._generate_recommendations(validated_candidates)
        
        return {
            "summary": summary,
            "recommendations": recommendations,
            "best_candidate": best_candidate,
            "all_candidates": validated_candidates
        }
    
    async def _generate_summary(self, original_sql: str, validated_candidates: List[Tuple[OptimizationCandidate, ValidationResult]], best_candidate: Optional[Tuple[OptimizationCandidate, ValidationResult]]) -> str:
        """Generate overall summary"""
        
        total_candidates = len(validated_candidates)
        successful_validations = sum(1 for _, validation in validated_candidates if validation.validation_passed)
        
        summary = f"🧠 Multi-Agent Analysis Complete\n\n"
        summary += f"Generated {total_candidates} optimization candidates, "
        summary += f"{successful_validations} passed validation.\n\n"
        
        if best_candidate:
            candidate, validation = best_candidate
            summary += f"🏆 Best Optimization:\n"
            summary += f"• Performance improvement: {validation.improvement_percentage:.1f}%\n"
            summary += f"• Cost reduction: {validation.original_cost:.1f} → {validation.optimized_cost:.1f}\n"
            summary += f"• Validation time: {validation.benchmark_time_ms:.1f}ms\n\n"
            summary += f"📋 Recommended changes:\n{candidate.explanation}"
        else:
            summary += "✅ No significant optimizations found.\n"
            summary += "The original query appears to be well-optimized and efficient."
        
        return summary
    
    async def _generate_recommendations(self, validated_candidates: List[Tuple[Optimization Candidate, ValidationResult]]) -> List[str]:
        """Generate specific recommendations"""
        recommendations = []
        
        for candidate, validation in validated_candidates:
            if validation.validation_passed and validation.improvement_percentage > 5:
                recommendations.append(
                    f"• {candidate.explanation} (Improvement: {validation.improvement_percentage:.1f}%)"
                )
        
        if not recommendations:
            recommendations.append("• No significant optimizations recommended - query is already efficient")
        
        return recommendations
