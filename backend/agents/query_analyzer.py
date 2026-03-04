"""
Query Analyzer Agent

Agent 1 in the multi-agent pipeline.
Analyzes SQL query structure, complexity, and extracts key information
for subsequent optimization agents.
"""

import re
from typing import List, Dict, Any
from dataclasses import dataclass

from .base_agent import BaseAgent

@dataclass
class QueryAnalysis:
    """Result of query analysis"""
    structure: Dict[str, Any]
    complexity: Dict[str, Any]
    tables: List[str]
    operations: List[str]
    estimated_cost: float

class QueryAnalyzerAgent(BaseAgent):
    """Analyzes SQL query structure and complexity"""
    
    def __init__(self):
        super().__init__("Query Analyzer")
    
    async def _execute(self, sql: str, schema: List[Dict[str, str]]) -> QueryAnalysis:
        """Extract structure and complexity from SQL query"""
        
        # Parse SQL structure
        tables = self._extract_tables(sql)
        operations = self._extract_operations(sql)
        complexity = self._analyze_complexity(sql, operations)
        structure = self._analyze_structure(sql)
        
        # Estimate cost based on complexity factors
        estimated_cost = self._estimate_cost(sql, tables, operations, complexity)
        
        return QueryAnalysis(
            structure=structure,
            complexity=complexity,
            tables=tables,
            operations=operations,
            estimated_cost=estimated_cost
        )
    
    def _extract_tables(self, sql: str) -> List[str]:
        """Extract table names from SQL"""
        # Simple regex for table extraction - can be enhanced
        from_pattern = re.findall(r'FROM\s+(\w+)', sql, re.IGNORECASE)
        join_pattern = re.findall(r'JOIN\s+(\w+)', sql, re.IGNORECASE)
        return list(set(from_pattern + join_pattern))
    
    def _extract_operations(self, sql: str) -> List[str]:
        """Extract SQL operations"""
        operations = []
        if re.search(r'JOIN', sql, re.IGNORECASE):
            operations.append('JOIN')
        if re.search(r'WHERE', sql, re.IGNORECASE):
            operations.append('FILTER')
        if re.search(r'GROUP BY', sql, re.IGNORECASE):
            operations.append('AGGREGATION')
        if re.search(r'ORDER BY', sql, re.IGNORECASE):
            operations.append('SORT')
        if re.search(r'LIMIT', sql, re.IGNORECASE):
            operations.append('LIMIT')
        return operations
    
    def _analyze_complexity(self, sql: str, operations: List[str]) -> Dict[str, Any]:
        """Analyze query complexity"""
        complexity_score = 0
        
        # Base complexity
        complexity_score += len(operations) * 2
        
        # Join complexity
        join_count = len(re.findall(r'JOIN', sql, re.IGNORECASE))
        complexity_score += join_count * 5
        
        # Subquery complexity
        subquery_count = len(re.findall(r'\bSELECT\b.*\bFROM\b.*\bSELECT\b', sql, re.IGNORECASE))
        complexity_score += subquery_count * 10
        
        # Aggregation complexity
        agg_count = len(re.findall(r'(COUNT|SUM|AVG|MAX|MIN)\s*\(', sql, re.IGNORECASE))
        complexity_score += agg_count * 3
        
        return {
            'score': complexity_score,
            'level': 'LOW' if complexity_score < 10 else 'MEDIUM' if complexity_score < 20 else 'HIGH',
            'factors': {
                'joins': join_count,
                'subqueries': subquery_count,
                'aggregations': agg_count,
                'operations': len(operations)
            }
        }
    
    def _analyze_structure(self, sql: str) -> Dict[str, Any]:
        """Analyze SQL structure"""
        return {
            'has_joins': bool(re.search(r'JOIN', sql, re.IGNORECASE)),
            'has_subqueries': bool(re.search(r'\bSELECT\b.*\bFROM\b.*\bSELECT\b', sql, re.IGNORECASE)),
            'has_aggregations': bool(re.search(r'(COUNT|SUM|AVG|MAX|MIN)\s*\(', sql, re.IGNORECASE)),
            'has_filters': bool(re.search(r'WHERE', sql, re.IGNORECASE)),
            'has_sorting': bool(re.search(r'ORDER BY', sql, re.IGNORECASE)),
            'has_limit': bool(re.search(r'LIMIT', sql, re.IGNORECASE))
        }
    
    def _estimate_cost(self, sql: str, tables: List[str], operations: List[str], complexity: Dict[str, Any]) -> float:
        """Estimate query execution cost"""
        base_cost = len(tables) * 100
        operation_cost = len(operations) * 50
        complexity_multiplier = complexity['score'] / 10
        return base_cost + operation_cost * complexity_multiplier
