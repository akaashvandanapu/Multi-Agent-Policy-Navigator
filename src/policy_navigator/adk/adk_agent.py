"""
ADK (Agent Development Kit) Integration for A2A Communication
Enables interoperability between CrewAI and ADK agents
"""

import os
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

try:
    import google.generativeai as genai
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False
    print("Warning: Google Generative AI not available. ADK features will be limited.")


class A2AMessage(BaseModel):
    """
    Message format for A2A (Agent-to-Agent) communication
    Aligned with A2A Protocol standards for interoperability between CrewAI and ADK agents
    
    This message format enables:
    - Task delegation between agents
    - Context sharing across agent boundaries
    - Status updates and capability discovery
    - Conversation tracking for multi-turn interactions
    """
    from_agent: str
    """Source agent identifier (e.g., 'calculator_agent', 'policy_researcher')"""
    to_agent: str
    """Target agent identifier or broadcast target (e.g., 'crewai_agents', 'adk_agents')"""
    message_type: str
    """Type of message: 'task_delegation', 'task_complete', 'data', 'status_update', 'capability_query'"""
    content: Dict[str, Any]
    """Message payload containing task data, results, or context"""
    timestamp: str
    """ISO format timestamp of message creation"""
    conversation_id: Optional[str] = None
    """Optional conversation ID for tracking multi-turn interactions"""
    status: Optional[str] = None
    """Message status: 'pending', 'processing', 'completed', 'failed'"""
    capabilities: Optional[List[str]] = None
    """List of agent capabilities (for capability discovery)"""
    response_required: bool = False
    """Whether this message requires a response from the recipient"""


class StateManager:
    """Manages shared state between CrewAI and ADK agents"""
    
    def __init__(self):
        import logging
        self.logger = logging.getLogger(__name__)
        self.state: Dict[str, Any] = {}
        self.message_queue: list[A2AMessage] = []
        self.logger.debug("StateManager initialized")
    
    def update_state(self, key: str, value: Any) -> None:
        """Update shared state"""
        self.state[key] = value
        self.logger.debug(f"StateManager: Updated state key '{key}' (value type: {type(value).__name__})")
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """Get value from shared state"""
        value = self.state.get(key, default)
        if value is not None:
            self.logger.debug(f"StateManager: Retrieved state key '{key}' (value type: {type(value).__name__})")
        else:
            self.logger.debug(f"StateManager: State key '{key}' not found, returning default")
        return value
    
    def add_message(self, message: A2AMessage) -> None:
        """Add message to A2A queue"""
        self.message_queue.append(message)
        self.logger.info(f"StateManager: Added A2A message from '{message.from_agent}' to '{message.to_agent}' (type: {message.message_type})")
        self.logger.debug(f"StateManager: Total messages in queue: {len(self.message_queue)}")
    
    def get_messages_for_agent(self, agent_id: str) -> list[A2AMessage]:
        """Get messages intended for a specific agent"""
        messages = [msg for msg in self.message_queue if msg.to_agent == agent_id]
        self.logger.debug(f"StateManager: Retrieved {len(messages)} message(s) for agent '{agent_id}'")
        return messages
    
    def get_all_messages(self) -> list[A2AMessage]:
        """Get all messages in queue (for debugging)"""
        return list(self.message_queue)
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get summary of state and messages (for debugging)"""
        return {
            "state_keys": list(self.state.keys()),
            "total_messages": len(self.message_queue),
            "messages_by_type": {
                msg.message_type: sum(1 for m in self.message_queue if m.message_type == msg.message_type)
                for msg in self.message_queue
            }
        }


# Singleton instance
_state_manager = None


def get_state_manager() -> StateManager:
    """Get singleton StateManager instance"""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager


class ADKAgent:
    """
    ADK Agent for A2A communication with CrewAI agents
    This agent can be used alongside CrewAI agents for interoperability
    """
    
    def __init__(self, agent_id: str = "adk_agent", model_name: Optional[str] = None):
        """
        Initialize ADK agent
        
        Args:
            agent_id: Unique identifier for this agent
            model_name: Google Generative AI model to use (defaults to ADK_MODEL from .env or "gemini-pro")
        """
        self.agent_id = agent_id
        # Use ADK_MODEL from .env if available, otherwise use provided model_name or default
        self.model_name = model_name or os.getenv("ADK_MODEL", "gemini-pro")
        self.state_manager = get_state_manager()
        
        if ADK_AVAILABLE:
            # Try GOOGLE_API_KEY first (from .env), fallback to GEMINI_API_KEY
            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel(self.model_name)
            else:
                self.model = None
                print("Warning: GOOGLE_API_KEY or GEMINI_API_KEY not found. ADK agent will have limited functionality.")
        else:
            self.model = None
    
    def process_message(self, message: A2AMessage) -> Dict[str, Any]:
        """
        Process a message from another agent (CrewAI or ADK)
        
        Args:
            message: A2A message to process
            
        Returns:
            Response dictionary
        """
        # Store message in state
        self.state_manager.add_message(message)
        
        # Update shared state with message content
        state_key = f"{message.from_agent}_output"
        self.state_manager.update_state(state_key, message.content)
        
        return {
            "status": "processed",
            "agent_id": self.agent_id,
            "message_type": message.message_type
        }
    
    def send_message_to_crewai(self, to_agent: str, content: Dict[str, Any], message_type: str = "data") -> None:
        """
        Send a message to a CrewAI agent
        
        Args:
            to_agent: Target CrewAI agent ID
            content: Message content
            message_type: Type of message
        """
        from datetime import datetime
        
        message = A2AMessage(
            from_agent=self.agent_id,
            to_agent=to_agent,
            message_type=message_type,
            content=content,
            timestamp=datetime.now().isoformat()
        )
        
        self.state_manager.add_message(message)
    
    def get_crewai_output(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get output from a CrewAI agent
        
        Args:
            agent_id: CrewAI agent identifier
            
        Returns:
            Agent output if available
        """
        return self.state_manager.get_state(f"{agent_id}_output")
    
    def execute_task(self, task_description: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Execute a task using ADK model
        
        Args:
            task_description: Description of the task
            context: Optional context from other agents
            
        Returns:
            Task result
        """
        if not self.model:
            return "ADK agent not properly configured. Please set GOOGLE_API_KEY or GEMINI_API_KEY."
        
        # Build prompt with context
        prompt = task_description
        if context:
            prompt += f"\n\nContext from other agents:\n{context}"
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error executing task: {str(e)}"


def create_adk_agent(agent_id: str = "adk_agent") -> ADKAgent:
    """
    Factory function to create ADK agent
    
    Args:
        agent_id: Unique identifier for the agent
        
    Returns:
        ADKAgent instance
    """
    return ADKAgent(agent_id=agent_id)


class CalculatorAgent(ADKAgent):
    """
    ADK Agent specialized for agricultural calculations
    Extends ADKAgent with calculator-specific functionality
    """
    
    def __init__(self, agent_id: str = "calculator_agent", model_name: Optional[str] = None):
        """
        Initialize Calculator Agent
        
        Args:
            agent_id: Unique identifier for this agent
            model_name: Google Generative AI model to use
        """
        super().__init__(agent_id=agent_id, model_name=model_name)
    
    def calculate_cost(self, area: float, crop: str, inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Calculate cost of cultivation using ADK model for enhanced calculations
        
        Args:
            area: Area in hectares
            crop: Crop name
            inputs: Optional dictionary of additional inputs
            
        Returns:
            Dictionary with cost calculation results
        """
        # Base costs per hectare (in INR)
        base_costs = {
            "paddy": 45000, "rice": 45000, "maize": 35000, "cotton": 55000,
            "groundnut": 40000, "redgram": 30000, "tur": 30000, "arhar": 30000
        }
        
        base_cost = base_costs.get(crop.lower(), 40000)
        total_cost = base_cost * area
        
        if inputs:
            for value in inputs.values():
                if isinstance(value, (int, float)):
                    total_cost += value * area
        
        return {
            "operation": "cost_estimation",
            "crop": crop,
            "area": area,
            "base_cost_per_hectare": base_cost,
            "total_cost": total_cost,
            "additional_inputs": inputs or {}
        }
    
    def calculate_yield(self, area: float, crop: str, variety: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate expected yield
        
        Args:
            area: Area in hectares
            crop: Crop name
            variety: Optional variety name
            
        Returns:
            Dictionary with yield calculation results
        """
        # Average yields per hectare (in kg)
        yields = {
            "paddy": 5500, "rice": 5500, "maize": 3500, "cotton": 500,
            "groundnut": 2000, "redgram": 1200, "tur": 1200, "arhar": 1200
        }
        
        avg_yield = yields.get(crop.lower(), 3000)
        total_yield = avg_yield * area
        
        return {
            "operation": "yield_calculation",
            "crop": crop,
            "variety": variety,
            "area": area,
            "yield_per_hectare": avg_yield,
            "total_yield": total_yield
        }
    
    def calculate_subsidy(self, scheme: str, area: float, crop: str) -> Dict[str, Any]:
        """
        Calculate subsidy amount
        
        Args:
            scheme: Scheme name
            area: Area in hectares
            crop: Crop name
            
        Returns:
            Dictionary with subsidy calculation results
        """
        # Subsidy rates per hectare (in INR)
        subsidies = {
            "pm_kisan": 6000, "pm-kisan": 6000, "pmfby": 2000,
            "seed_subsidy": 5000, "fertilizer_subsidy": 3000
        }
        
        subsidy_rate = subsidies.get(scheme.lower(), 0)
        total_subsidy = subsidy_rate * area
        
        return {
            "operation": "subsidy_calculation",
            "scheme": scheme,
            "crop": crop,
            "area": area,
            "subsidy_rate_per_hectare": subsidy_rate,
            "total_subsidy": total_subsidy
        }
    
    def calculate_profit(self, revenue: float, cost: float) -> Dict[str, Any]:
        """
        Calculate profit from revenue and cost
        
        Args:
            revenue: Total revenue
            cost: Total cost
            
        Returns:
            Dictionary with profit calculation results
        """
        profit = revenue - cost
        profit_margin = (profit / revenue * 100) if revenue > 0 else 0
        
        return {
            "operation": "profit_calculation",
            "revenue": revenue,
            "cost": cost,
            "profit": profit,
            "profit_margin_percent": profit_margin
        }
    
    def perform_calculation(self, operation: str, values: Dict[str, Any]) -> str:
        """
        Perform agricultural calculation and format result
        
        Args:
            operation: Type of calculation
            values: Input values dictionary
            
        Returns:
            Formatted calculation result string
        """
        if operation == "cost_estimation":
            result = self.calculate_cost(
                area=values.get("area", 0),
                crop=values.get("crop", ""),
                inputs=values.get("inputs")
            )
            output = f"**Cost of Cultivation Calculation**\n\n"
            output += f"Crop: {result['crop']}\n"
            output += f"Area: {result['area']} hectares\n"
            output += f"Base Cost per hectare: ₹{result['base_cost_per_hectare']:,}\n"
            if result['additional_inputs']:
                output += f"\nAdditional Inputs:\n"
                for key, value in result['additional_inputs'].items():
                    output += f"  - {key}: ₹{value:,}\n"
            output += f"\n**Total Cost of Cultivation: ₹{result['total_cost']:,}**\n"
            return output
            
        elif operation == "yield_calculation":
            result = self.calculate_yield(
                area=values.get("area", 0),
                crop=values.get("crop", ""),
                variety=values.get("variety")
            )
            output = f"**Yield Calculation**\n\n"
            output += f"Crop: {result['crop']}\n"
            if result['variety']:
                output += f"Variety: {result['variety']}\n"
            output += f"Area: {result['area']} hectares\n"
            output += f"Average Yield per hectare: {result['yield_per_hectare']} kg\n"
            output += f"\n**Total Expected Yield: {result['total_yield']:,} kg**\n"
            return output
            
        elif operation == "subsidy_calculation":
            result = self.calculate_subsidy(
                scheme=values.get("scheme", ""),
                area=values.get("area", 0),
                crop=values.get("crop", "")
            )
            if result['subsidy_rate_per_hectare'] == 0:
                return f"Error: Unknown scheme '{values.get('scheme', '')}'. Available schemes: PM-KISAN, PMFBY, seed_subsidy, fertilizer_subsidy"
            output = f"**Subsidy Calculation**\n\n"
            output += f"Scheme: {result['scheme']}\n"
            output += f"Crop: {result['crop']}\n"
            output += f"Area: {result['area']} hectares\n"
            output += f"Subsidy Rate per hectare: ₹{result['subsidy_rate_per_hectare']:,}\n"
            output += f"\n**Total Subsidy Amount: ₹{result['total_subsidy']:,}**\n"
            return output
            
        elif operation == "profit_calculation":
            result = self.calculate_profit(
                revenue=values.get("revenue", 0),
                cost=values.get("cost", 0)
            )
            output = f"**Profit Calculation**\n\n"
            output += f"Total Revenue: ₹{result['revenue']:,}\n"
            output += f"Total Cost: ₹{result['cost']:,}\n"
            output += f"\n**Net Profit: ₹{result['profit']:,}**\n"
            output += f"Profit Margin: {result['profit_margin_percent']:.2f}%\n"
            if result['profit'] < 0:
                output += f"\n⚠️ Note: This indicates a loss of ₹{abs(result['profit']):,}\n"
            return output
        else:
            return f"Error: Unknown operation '{operation}'. Valid operations are: cost_estimation, yield_calculation, subsidy_calculation, profit_calculation"


def create_calculator_agent(agent_id: str = "calculator_agent") -> CalculatorAgent:
    """
    Factory function to create Calculator Agent
    
    Args:
        agent_id: Unique identifier for the agent
        
    Returns:
        CalculatorAgent instance
    """
    return CalculatorAgent(agent_id=agent_id)

