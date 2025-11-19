"""
ADK Agent Adapter for CrewAI Integration
Makes ADK agents compatible with CrewAI framework using BaseAgentAdapter pattern

This adapter implements A2A (Agent-to-Agent) Protocol concepts for local ADK agents:
- Enables interoperability between CrewAI and Google ADK agents
- Uses StateManager as the A2A communication channel (similar to A2A protocol endpoints)
- Implements task delegation pattern where CrewAI agents can delegate to ADK agents
- Supports capability discovery and status tracking

Note: This uses an adapter pattern for local ADK agents rather than remote A2A endpoints.
For remote A2A agents, use CrewAI's native A2AConfig with endpoint URLs.
"""

import logging
import json
from typing import Dict, Any, Optional, List, Type, ClassVar
from datetime import datetime

from crewai.agents.agent_adapters.base_agent_adapter import BaseAgentAdapter
from crewai.tools import BaseTool
from crewai import Task, LLM
from pydantic import BaseModel, Field

from policy_navigator.adk.adk_agent import (
    CalculatorAgent,
    create_calculator_agent,
    get_state_manager,
    A2AMessage
)

logger = logging.getLogger(__name__)


class ADKAgentAdapter(BaseAgentAdapter):
    """
    Adapter to make ADK agents compatible with CrewAI using A2A Protocol concepts
    
    This adapter enables A2A communication between CrewAI and Google ADK agents:
    - Wraps ADK agents (CalculatorAgent) to work as CrewAI agents
    - Implements A2A task delegation pattern
    - Uses StateManager as the A2A communication channel
    - Supports capability discovery and status tracking
    
    A2A Protocol Alignment:
    - Task Delegation: CrewAI agents delegate tasks to ADK agents via this adapter
    - Message Exchange: Uses A2AMessage format for communication
    - Capability Discovery: Agents expose capabilities for task routing
    - Status Tracking: Tracks task execution status through A2A messages
    """
    
    # Agent capabilities mapping (similar to agent-card.json in A2A protocol)
    AGENT_CAPABILITIES: ClassVar[Dict[str, List[str]]] = {
        "calculator_agent": [
            "cost_estimation",
            "yield_calculation", 
            "subsidy_calculation",
            "profit_calculation",
            "agricultural_financial_analysis"
        ],
    }
    
    # Instance fields (Pydantic fields with defaults)
    adk_agent: Optional[Any] = Field(default=None, exclude=True)
    agent_id: str = Field(default="")
    state_manager: Optional[Any] = Field(default=None, exclude=True)
    capabilities: List[str] = Field(default_factory=list)
    crewai_tools: List[BaseTool] = Field(default_factory=list, exclude=True)
    output_pydantic: Optional[Type[BaseModel]] = Field(default=None, exclude=True)
    output_json: bool = Field(default=False, exclude=True)
    function_calling_llm: Optional[LLM] = Field(default=None, exclude=True)
    # BaseAgent attributes that might be accessed
    step_callback: Optional[Any] = Field(default=None, exclude=True)
    task_callback: Optional[Any] = Field(default=None, exclude=True)
    verbose: bool = Field(default=False, exclude=True)
    allow_delegation: bool = Field(default=False, exclude=True)
    max_iter: Optional[int] = Field(default=None, exclude=True)
    max_execution_time: Optional[int] = Field(default=None, exclude=True)
    callbacks: List[Any] = Field(default_factory=list, exclude=True)
    
    def __init__(
        self,
        adk_agent: Any,  # CalculatorAgent
        agent_config: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ):
        """
        Initialize ADK Agent Adapter with A2A Protocol support
        
        Args:
            adk_agent: ADK agent instance (CalculatorAgent)
            agent_config: Agent configuration from agents.yaml
            **kwargs: Additional arguments passed to BaseAgentAdapter
        """
        # Extract role, goal, backstory from config (required by BaseAgent)
        if agent_config:
            role = agent_config.get("role", "ADK Agent")
            goal = agent_config.get("goal", "Execute tasks using ADK")
            backstory = agent_config.get("backstory", "An ADK agent integrated with CrewAI")
        else:
            role = "ADK Agent"
            goal = "Execute tasks using ADK"
            backstory = "An ADK agent integrated with CrewAI"
        
        # Extract common BaseAgent attributes from kwargs
        function_calling_llm = kwargs.pop('function_calling_llm', None)
        step_callback = kwargs.pop('step_callback', None)
        task_callback = kwargs.pop('task_callback', None)
        verbose = kwargs.pop('verbose', False)
        allow_delegation = kwargs.pop('allow_delegation', False)
        max_iter = kwargs.pop('max_iter', None)
        max_execution_time = kwargs.pop('max_execution_time', None)
        callbacks = kwargs.pop('callbacks', [])
        
        # Call parent constructor with required fields first
        super().__init__(
            role=role,
            goal=goal,
            backstory=backstory,
            agent_config=agent_config,
            function_calling_llm=function_calling_llm,
            verbose=verbose,
            allow_delegation=allow_delegation,
            max_iter=max_iter,
            max_execution_time=max_execution_time,
            **kwargs
        )
        
        # Set attributes that might not be set by parent
        if not hasattr(self, 'function_calling_llm') or self.function_calling_llm is None:
            self.function_calling_llm = function_calling_llm
        if not hasattr(self, 'step_callback') or self.step_callback is None:
            self.step_callback = step_callback
        if not hasattr(self, 'task_callback') or self.task_callback is None:
            self.task_callback = task_callback
        if not hasattr(self, 'verbose'):
            self.verbose = verbose
        if not hasattr(self, 'allow_delegation'):
            self.allow_delegation = allow_delegation
        if not hasattr(self, 'max_iter'):
            self.max_iter = max_iter
        if not hasattr(self, 'max_execution_time'):
            self.max_execution_time = max_execution_time
        if not hasattr(self, 'callbacks'):
            self.callbacks = callbacks
        
        # Set instance fields after parent initialization
        # These fields are declared with Field() defaults, so we can set them normally
        self.adk_agent = adk_agent
        self.agent_id = adk_agent.agent_id
        self.state_manager = get_state_manager()
        
        # Get agent capabilities for A2A protocol
        self.capabilities = self.AGENT_CAPABILITIES.get(adk_agent.agent_id, [])
        
        logger.info(f"Initialized ADKAgentAdapter for agent: {adk_agent.agent_id} with A2A Protocol support")
        logger.debug(f"ADKAgentAdapter ({adk_agent.agent_id}): Capabilities: {self.capabilities}")
    
    def configure_tools(self, tools: Optional[List[BaseTool]] = None) -> None:
        """
        Configure tools for the ADK agent
        ADK agents typically don't use CrewAI tools directly,
        but we store them for potential future use
        
        Args:
            tools: List of CrewAI BaseTool instances
        """
        if tools:
            logger.debug(f"ADKAgentAdapter ({self.agent_id}): Received {len(tools)} tools")
            # ADK agents use their own methods, not CrewAI tools
            # Store tools for reference but don't convert them
            self.crewai_tools = tools
        else:
            self.crewai_tools = []
            logger.debug(f"ADKAgentAdapter ({self.agent_id}): No tools provided")
    
    def configure_structured_output(self, task: Task) -> None:
        """
        Configure structured output for the ADK agent based on task requirements
        
        Args:
            task: CrewAI Task object with output_pydantic or output_json requirements
        """
        self.output_pydantic = None
        self.output_json = False
        
        if hasattr(task, 'output_pydantic') and task.output_pydantic:
            self.output_pydantic = task.output_pydantic
            logger.debug(f"ADKAgentAdapter ({self.agent_id}): Configured Pydantic output: {task.output_pydantic.__name__}")
        
        if hasattr(task, 'output_json') and task.output_json:
            self.output_json = True
            logger.debug(f"ADKAgentAdapter ({self.agent_id}): Configured JSON output")
    
    def execute(self, task: Task, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Execute a task using the ADK agent (A2A Protocol task delegation)
        
        This method implements A2A Protocol task delegation pattern:
        1. Receives task from CrewAI agent (delegation)
        2. Executes task using ADK agent capabilities
        3. Creates A2A message for result communication
        4. Returns structured result to CrewAI workflow
        
        Args:
            task: CrewAI Task to execute (delegated from CrewAI agent)
            context: Optional context from previous tasks (A2A context sharing)
            
        Returns:
            Task result as string (will be converted to structured format if needed)
        """
        logger.info(f"ADKAgentAdapter ({self.agent_id}): Executing delegated task via A2A Protocol: {task.description[:100]}...")
        
        # Create A2A message for task delegation (status: processing)
        self._create_a2a_delegation_message(task, context)
        
        # Configure structured output
        self.configure_structured_output(task)
        
        # Extract task description and parameters
        task_description = task.description
        if context:
            # Handle both dict and string contexts
            if isinstance(context, dict):
                task_description += f"\n\nContext from previous tasks:\n{json.dumps(context, indent=2)}"
            elif isinstance(context, str):
                task_description += f"\n\nContext from previous tasks:\n{context}"
        
        # Determine agent type and execute accordingly
        result = None
        execution_status = "completed"
        
        try:
            if isinstance(self.adk_agent, CalculatorAgent):
                result = self._execute_calculation_task(task, context)
            else:
                # Generic ADK agent execution
                result = self.adk_agent.execute_task(task_description, context)
        except Exception as e:
            execution_status = "failed"
            result = f"Error executing task: {str(e)}"
            logger.error(f"ADKAgentAdapter ({self.agent_id}): Task execution failed: {e}")
        
        # Store result in StateManager for A2A communication
        self._store_result_in_state(result)
        
        # Create A2A message with status
        self._create_a2a_message(result, execution_status)
        
        # Convert to structured output if needed
        if self.output_pydantic:
            result = self._convert_to_pydantic(result, self.output_pydantic)
        elif self.output_json:
            result = self._convert_to_json(result)
        
        return result
    
    def _create_a2a_delegation_message(self, task: Task, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Create A2A message for task delegation (A2A Protocol)
        
        This message indicates that a task has been delegated to this ADK agent
        """
        import uuid
        
        a2a_message = A2AMessage(
            from_agent="crewai_workflow",
            to_agent=self.agent_id,
            message_type="task_delegation",
            content={
                "task_description": task.description[:500],
                "task_id": getattr(task, 'id', 'unknown'),
                "context_available": context is not None
            },
            timestamp=datetime.now().isoformat(),
            conversation_id=str(uuid.uuid4()),
            status="processing",
            capabilities=self.capabilities,
            response_required=True
        )
        
        self.state_manager.add_message(a2a_message)
        logger.debug(f"ADKAgentAdapter ({self.agent_id}): Received A2A task delegation message")
    
    def _execute_calculation_task(self, task: Task, context: Optional[Dict[str, Any]] = None) -> str:
        """Execute calculation task"""
        # Extract calculation parameters from task description or context
        operation = None
        values = {}
        
        # Try to extract from context first
        if context:
            operation = context.get("operation")
            values = context.get("values", {})
        
        # If not in context, try to parse from task description
        if not operation:
            import re
            # Look for operation type in description
            if "cost" in task.description.lower() or "cost_estimation" in task.description.lower():
                operation = "cost_estimation"
            elif "yield" in task.description.lower() or "yield_calculation" in task.description.lower():
                operation = "yield_calculation"
            elif "subsidy" in task.description.lower() or "subsidy_calculation" in task.description.lower():
                operation = "subsidy_calculation"
            elif "profit" in task.description.lower() or "profit_calculation" in task.description.lower():
                operation = "profit_calculation"
            
            # Try to extract values from description
            # This is a simplified extraction - in practice, the task description should be clear
            if "area" in task.description.lower():
                area_match = re.search(r'area[:\s]+([0-9.]+)', task.description, re.IGNORECASE)
                if area_match:
                    values["area"] = float(area_match.group(1))
            
            if "crop" in task.description.lower():
                crop_match = re.search(r'crop[:\s]+([a-zA-Z]+)', task.description, re.IGNORECASE)
                if crop_match:
                    values["crop"] = crop_match.group(1)
        
        if not operation:
            return "Error: Could not determine calculation operation from task description or context"
        
        # Perform calculation
        result_str = self.adk_agent.perform_calculation(operation, values)
        
        return result_str
    
    def _store_result_in_state(self, result: Any) -> None:
        """Store task result in StateManager"""
        state_key = f"{self.agent_id}_output"
        result_data = {
            "result": result,
            "timestamp": datetime.now().isoformat(),
            "agent_id": self.agent_id
        }
        self.state_manager.update_state(state_key, result_data)
        logger.debug(f"ADKAgentAdapter ({self.agent_id}): Stored result in StateManager")
    
    def _create_a2a_message(self, result: Any, status: str = "completed") -> None:
        """
        Create A2A message after task completion
        
        Implements A2A Protocol message exchange:
        - Sends task completion notification to CrewAI agents
        - Includes agent capabilities for discovery
        - Sets status for tracking (completed/failed)
        """
        import uuid
        
        a2a_message = A2AMessage(
            from_agent=self.agent_id,
            to_agent="crewai_agents",  # Broadcast to all CrewAI agents (A2A pattern)
            message_type="task_complete",
            content={
                "agent_id": self.agent_id,
                "result_summary": str(result)[:500] if result else "No result",
                "capabilities": self.capabilities,
                "timestamp": datetime.now().isoformat()
            },
            timestamp=datetime.now().isoformat(),
            conversation_id=str(uuid.uuid4()),  # Track this conversation
            status=status,
            capabilities=self.capabilities,
            response_required=False
        )
        
        self.state_manager.add_message(a2a_message)
        logger.info(f"ADKAgentAdapter ({self.agent_id}): Created A2A message to CrewAI agents (A2A Protocol)")
        logger.debug(f"ADKAgentAdapter ({self.agent_id}): A2A Message - Type: {a2a_message.message_type}, Status: {a2a_message.status}, Capabilities: {a2a_message.capabilities}")
    
    def _convert_to_pydantic(self, result: str, pydantic_model: Type[BaseModel]) -> str:
        """Convert result string to Pydantic model format"""
        try:
            # Try to parse as JSON first
            if isinstance(result, str):
                try:
                    result_dict = json.loads(result)
                except json.JSONDecodeError:
                    # If not JSON, try to create a dict from the string
                    result_dict = {"raw_output": result}
            else:
                result_dict = result
            
            # Create Pydantic model instance
            # Generic Pydantic model creation
            model_instance = pydantic_model.model_validate(result_dict)
            return model_instance.model_dump_json()
        except Exception as e:
            logger.warning(f"ADKAgentAdapter ({self.agent_id}): Failed to convert to Pydantic, returning raw result: {e}")
            return result if isinstance(result, str) else json.dumps(result)
    
    def _convert_to_json(self, result: str) -> str:
        """Convert result to JSON format"""
        try:
            if isinstance(result, str):
                # Try to parse as JSON to validate
                json.loads(result)
                return result
            else:
                return json.dumps(result)
        except json.JSONDecodeError:
            # If not valid JSON, wrap it
            return json.dumps({"result": result})
    
    def execute_task(
        self,
        task: Task,
        context: Optional[str] = None,
        tools: Optional[List[BaseTool]] = None
    ) -> Any:
        """
        Execute a task (required abstract method from BaseAgentAdapter)
        
        This method matches the BaseAgent.execute_task() signature:
        - task: CrewAI Task to execute
        - context: Optional context string from previous tasks
        - tools: Optional list of tools (ADK agents don't use CrewAI tools directly)
        
        Args:
            task: CrewAI Task to execute
            context: Optional context string from previous tasks
            tools: Optional list of CrewAI BaseTool instances (ignored for ADK agents)
            
        Returns:
            Task result
        """
        # Convert context string to dict if needed
        context_dict = None
        if context:
            try:
                # Try to parse as JSON
                context_dict = json.loads(context)
            except (json.JSONDecodeError, TypeError):
                # If not JSON, treat as plain string
                context_dict = {"context": context}
        
        # ADK agents don't use CrewAI tools directly, but we log them for debugging
        if tools:
            logger.debug(f"ADKAgentAdapter ({self.agent_id}): Received {len(tools)} tools (not used by ADK agent)")
        
        return self.execute(task, context_dict)
    
    def create_agent_executor(self) -> Any:
        """
        Create agent executor (required abstract method from BaseAgentAdapter)
        
        For ADK agents, we return the ADK agent itself as the executor
        
        Returns:
            ADK agent instance that can execute tasks
        """
        logger.debug(f"ADKAgentAdapter ({self.agent_id}): Creating agent executor")
        return self.adk_agent
    
    def get_delegation_tools(self) -> List[BaseTool]:
        """
        Get delegation tools (required abstract method from BaseAgentAdapter)
        
        ADK agents don't expose tools for delegation, they handle tasks directly
        
        Returns:
            Empty list (ADK agents handle tasks internally)
        """
        logger.debug(f"ADKAgentAdapter ({self.agent_id}): Getting delegation tools (none for ADK agents)")
        return []


def create_calculator_adapter(agent_config: Optional[Dict[str, Any]] = None) -> ADKAgentAdapter:
    """
    Factory function to create Calculator ADK Agent Adapter
    
    Args:
        agent_config: Agent configuration from agents.yaml
        
    Returns:
        ADKAgentAdapter instance wrapping CalculatorAgent
    """
    calc_agent = create_calculator_agent()
    return ADKAgentAdapter(adk_agent=calc_agent, agent_config=agent_config)

