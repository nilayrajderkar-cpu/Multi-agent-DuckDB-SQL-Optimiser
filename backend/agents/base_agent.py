"""
Base Agent Framework

Provides the foundation for all agents in the multi-agent SQL optimization system.
Defines common interfaces, status tracking, and result handling.
"""

import logging
import asyncio
from typing import Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class AgentStatus(Enum):
    """Agent execution status"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class AgentResult:
    """Result from agent execution"""
    agent_name: str
    status: AgentStatus
    result: Any
    execution_time_ms: float
    error_message: Optional[str] = None

class BaseAgent:
    """Base class for all optimization agents"""
    
    def __init__(self, name: str):
        self.name = name
        self.status = AgentStatus.IDLE
        self.execution_time_ms = 0.0
        
    async def execute(self, *args, **kwargs) -> AgentResult:
        """Execute the agent with proper timing and error handling"""
        start_time = asyncio.get_event_loop().time()
        self.status = AgentStatus.RUNNING
        
        try:
            logger.info(f"🤖 {self.name}: Starting execution")
            result = await self._execute(*args, **kwargs)
            self.status = AgentStatus.COMPLETED
            execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            logger.info(f"✅ {self.name}: Completed in {execution_time:.1f}ms")
            
            return AgentResult(
                agent_name=self.name,
                status=self.status,
                result=result,
                execution_time_ms=execution_time
            )
        except Exception as e:
            self.status = AgentStatus.FAILED
            execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            logger.error(f"❌ {self.name}: Failed after {execution_time:.1f}ms - {str(e)}")
            
            return AgentResult(
                agent_name=self.name,
                status=self.status,
                result=None,
                execution_time_ms=execution_time,
                error_message=str(e)
            )
    
    async def _execute(self, *args, **kwargs) -> Any:
        """Override this method in subclasses"""
        raise NotImplementedError(f"{self.__class__.__name__}._execute() must be implemented")
