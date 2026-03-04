"""
Optimizer Generator Agent

Agent 2 in the multi-agent pipeline.
Generates multiple optimization candidates using different strategies:
- Index optimizations
- Join optimizations  
- Structure optimizations
- Filter optimizations
"""

import os
import httpx
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .base_agent import BaseAgent
from .query_analyzer import QueryAnalysis

logger = logging.getLogger(__name__)

@dataclass
class OptimizationCandidate:
    """Single optimization candidate"""
    sql: str
    explanation: str
    estimated_improvement: float
    confidence: float

class OptimizerGeneratorAgent(BaseAgent):
    """Generates optimization candidates using multiple strategies"""
    
    def __init__(self):
        super().__init__("Optimizer Generator")
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.groq_api_url = "https://api.groq.com/openai/v1/chat/completions"
    
    async def _execute(self, sql: str, schema: List[Dict[str, str]], analysis: QueryAnalysis) -> List[OptimizationCandidate]:
        """Generate N optimization candidates"""
        
        candidates = []
        
        # Generate different optimization strategies
        candidates.extend(await self._generate_index_optimizations(sql, schema, analysis))
        candidates.extend(await self._generate_join_optimizations(sql, schema, analysis))
        candidates.extend(await self._generate_structure_optimizations(sql, schema, analysis))
        candidates.extend(await self._generate_filter_optimizations(sql, schema, analysis))
        
        # Sort by estimated improvement and confidence
        candidates.sort(key=lambda x: (x.estimated_improvement, x.confidence), reverse=True)
        
        # Return top candidates
        return candidates[:5]
    
    async def _generate_index_optimizations(self, sql: str, schema: List[Dict[str, str]], analysis: QueryAnalysis) -> List[OptimizationCandidate]:
        """Generate index-based optimizations"""
        candidates = []
        
        # Use Groq to suggest index optimizations
        prompt = self._build_index_prompt(sql, schema, analysis)
        response = await self._call_groq_api(prompt)
        
        if response:
            candidates.append(OptimizationCandidate(
                sql=sql,  # SQL unchanged, just index suggestion
                explanation=response,
                estimated_improvement=0.3,
                confidence=0.8
            ))
        
        return candidates
    
    async def _generate_join_optimizations(self, sql: str, schema: List[Dict[str, str]], analysis: QueryAnalysis) -> List[OptimizationCandidate]:
        """Generate join optimizations"""
        candidates = []
        
        if analysis.structure['has_joins']:
            prompt = self._build_join_prompt(sql, schema, analysis)
            response = await self._call_groq_api(prompt)
            
            if response:
                # Extract optimized SQL from response
                optimized_sql = self._extract_sql_from_response(response, sql)
                candidates.append(OptimizationCandidate(
                    sql=optimized_sql,
                    explanation=response,
                    estimated_improvement=0.4,
                    confidence=0.7
                ))
        
        return candidates
    
    async def _generate_structure_optimizations(self, sql: str, schema: List[Dict[str, str]], analysis: QueryAnalysis) -> List[OptimizationCandidate]:
        """Generate structure optimizations"""
        candidates = []
        
        prompt = self._build_structure_prompt(sql, schema, analysis)
        response = await self._call_groq_api(prompt)
        
        if response:
            optimized_sql = self._extract_sql_from_response(response, sql)
            candidates.append(OptimizationCandidate(
                sql=optimized_sql,
                explanation=response,
                estimated_improvement=0.2,
                confidence=0.6
            ))
        
        return candidates
    
    async def _generate_filter_optimizations(self, sql: str, schema: List[Dict[str, str]], analysis: QueryAnalysis) -> List[OptimizationCandidate]:
        """Generate filter optimizations"""
        candidates = []
        
        if analysis.structure['has_filters']:
            prompt = self._build_filter_prompt(sql, schema, analysis)
            response = await self._call_groq_api(prompt)
            
            if response:
                optimized_sql = self._extract_sql_from_response(response, sql)
                candidates.append(OptimizationCandidate(
                    sql=optimized_sql,
                    explanation=response,
                    estimated_improvement=0.25,
                    confidence=0.7
                ))
        
        return candidates
    
    def _build_index_prompt(self, sql: str, schema: List[Dict[str, str]], analysis: QueryAnalysis) -> str:
        """Build prompt for index optimization suggestions"""
        return f"""Analyze this SQL query and suggest specific indexes that would improve performance:

SQL: {sql}

Schema: {self._format_schema(schema)}

Analysis: {analysis}

Provide specific index recommendations in this format:
INDEX_SUGGESTIONS:
- CREATE INDEX idx_name ON table_name(column_name)
- Reason: explanation of why this index helps

Focus on most impactful indexes for WHERE clauses, JOIN conditions, and ORDER BY clauses."""
    
    def _build_join_prompt(self, sql: str, schema: List[Dict[str, str]], analysis: QueryAnalysis) -> str:
        """Build prompt for join optimization"""
        return f"""Optimize this SQL query with JOIN operations:

SQL: {sql}

Schema: {self._format_schema(schema)}

Analysis: {analysis}

Provide optimized SQL focusing on:
- Join order optimization
- Join type recommendations (INNER vs LEFT vs RIGHT)
- Join condition improvements

Respond with:
OPTIMIZED_SQL:
<the optimized SQL here>

EXPLANATION:
<explanation of join optimizations>"""
    
    def _build_structure_prompt(self, sql: str, schema: List[Dict[str, str]], analysis: QueryAnalysis) -> str:
        """Build prompt for structure optimization"""
        return f"""Optimize this SQL query structure:

SQL: {sql}

Schema: {self._format_schema(schema)}

Analysis: {analysis}

Provide structural optimizations focusing on:
- Query rewriting
- Subquery optimization
- Common table expressions (CTE)
- Query simplification

Respond with:
OPTIMIZED_SQL:
<the optimized SQL here>

EXPLANATION:
<explanation of structural optimizations>"""
    
    def _build_filter_prompt(self, sql: str, schema: List[Dict[str, str]], analysis: QueryAnalysis) -> str:
        """Build prompt for filter optimization"""
        return f"""Optimize this SQL query's WHERE clause and filtering:

SQL: {sql}

Schema: {self._format_schema(schema)}

Analysis: {analysis}

Provide filter optimizations focusing on:
- WHERE clause improvements
- Predicate ordering
- Filter condition optimization
- SARGable predicates

Respond with:
OPTIMIZED_SQL:
<the optimized SQL here>

EXPLANATION:
<explanation of filter optimizations>"""
    
    def _format_schema(self, schema: List[Dict[str, str]]) -> str:
        """Format schema for prompts"""
        if not schema:
            return "No schema provided"
        
        # Group by table
        tables = {}
        for col in schema:
            table = col.get('table_name', 'unknown')
            if table not in tables:
                tables[table] = []
            tables[table].append(f"{col['column_name']} ({col['data_type']})")
        
        result = []
        for table, columns in tables.items():
            result.append(f"Table {table}:")
            for col in columns:
                result.append(f"  - {col}")
        
        return "\n".join(result)
    
    def _extract_sql_from_response(self, response: str, original_sql: str) -> str:
        """Extract optimized SQL from AI response"""
        if "OPTIMIZED_SQL:" in response:
            try:
                _, after_opt = response.split("OPTIMIZED_SQL:", 1)
                if "EXPLANATION:" in after_opt:
                    sql_part, _ = after_opt.split("EXPLANATION:", 1)
                    return sql_part.strip()
                else:
                    return after_opt.strip()
            except:
                pass
        return original_sql  # Return original if extraction fails
    
    async def _call_groq_api(self, prompt: str) -> Optional[str]:
        """Call Groq API for optimization suggestions"""
        try:
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 500,
                "temperature": 0.1
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.groq_api_url, headers=headers, json=payload)
                response.raise_for_status()
                
                data = response.json()
                return data["choices"][0]["message"]["content"]
                
        except Exception as e:
            logger.error(f"Groq API call failed: {e}")
            return None
