"""
Execution Tracker - Tracks agents and tools used during crew execution
"""

from typing import Dict, Set, List, Optional, Any
from threading import Lock
from collections import defaultdict


class ExecutionTracker:
    """Thread-safe tracker for agents and tools used during execution"""
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        with self._lock:
            if self._initialized:
                return
            
            self.executed_agents: List[str] = []  # Changed to list to preserve execution order
            self.used_tools: Set[str] = set()
            self.agent_tools: Dict[str, Set[str]] = defaultdict(set)  # agent -> set of tools
            self.query_analysis: Optional[Any] = None  # Store query_analysis_task output
            self._initialized = True
    
    def reset(self):
        """Reset tracker for new execution"""
        with self._lock:
            self.executed_agents.clear()
            self.used_tools.clear()
            self.agent_tools.clear()
            self.query_analysis = None
    
    def store_query_analysis(self, query_analysis: Any):
        """Store query_analysis_task output for conditional task checks"""
        with self._lock:
            self.query_analysis = query_analysis
    
    def track_agent(self, agent_name: str):
        """Track that an agent executed (preserves execution order)"""
        with self._lock:
            # Only add if not already in list (preserve order, avoid duplicates)
            if agent_name not in self.executed_agents:
                self.executed_agents.append(agent_name)
            # Ensure agent has an entry in agent_tools
            if agent_name not in self.agent_tools:
                self.agent_tools[agent_name] = set()
    
    def track_tool(self, agent_name: str, tool_name: str):
        """Track that a tool was used by an agent"""
        with self._lock:
            self.used_tools.add(tool_name)
            self.agent_tools[agent_name].add(tool_name)
            # Also track the agent if not already tracked (preserve order)
            if agent_name not in self.executed_agents:
                self.executed_agents.append(agent_name)
    
    def get_executed_agents(self) -> List[str]:
        """Get list of executed agents (in execution order)"""
        with self._lock:
            return list(self.executed_agents)  # Return in execution order, not sorted
    
    def get_used_tools(self) -> List[str]:
        """Get list of used tools"""
        with self._lock:
            return sorted(list(self.used_tools))
    
    def get_agent_tools(self) -> Dict[str, List[str]]:
        """Get dictionary of agent -> list of tools used"""
        with self._lock:
            return {
                agent: sorted(list(tools)) 
                for agent, tools in self.agent_tools.items()
            }
    
    def get_summary(self) -> Dict[str, any]:
        """Get summary of execution"""
        with self._lock:
            return {
                "executed_agents": self.get_executed_agents(),
                "used_tools": self.get_used_tools(),
                "agent_tools": self.get_agent_tools()
            }


# Global tracker instance
_tracker = ExecutionTracker()


def get_tracker() -> ExecutionTracker:
    """Get the global execution tracker instance"""
    return _tracker

