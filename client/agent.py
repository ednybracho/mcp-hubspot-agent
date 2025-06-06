import asyncio
import sys
from typing import Optional, Dict, List
from contextlib import AsyncExitStack
from datetime import datetime

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

class HubSpotAgent:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic()
        
        # Conversation state
        self.collected_data = {
            "name": None,
            "email": None,
            "phone": None,
            "company_name": None,
            "appointment_date": None
        }
        self.conversation_state = "greeting"
        
    async def connect_to_server(self, server_script_path: str):
        """Connect to the HubSpot MCP Server"""
        is_python = server_script_path.endswith(".py")
        is_js = server_script_path.endswith(".js")
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")
        
        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )
        
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        
        await self.session.initialize()
        
        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\\nConnected to HubSpot server with tools:", [tool.name for tool in tools])
    
    def get_conversation_prompt(self, user_input: str) -> str:
        """Generate appropriate conversation prompt based on current state"""
        
        data_status = self._get_data_collection_status()
        
        if self.conversation_state == "greeting":
            return f"""You are a friendly sales agent collecting information from a potential customer.
            
Current conversation state: Initial greeting
User input: "{user_input}"

Your goals:
1. Start with a warm greeting and introduction
2. Begin collecting: name, email, phone, and company name
3. Be conversational and natural, don't ask all questions at once
4. Ask for one piece of information at a time

Current collected data: {data_status}

Respond naturally and ask for the next piece of missing information."""

        elif self.conversation_state == "collecting_info":
            return f"""You are a friendly sales agent continuing to collect customer information.
            
Current conversation state: Collecting basic information
User input: "{user_input}"

Your goals:
1. Extract any information provided by the user
2. Continue collecting missing information: name, email, phone, company name
3. Be natural and conversational
4. Once you have all basic info, transition to scheduling

Current collected data: {data_status}

If all basic information is collected, ask about scheduling an appointment. Otherwise, ask for the next missing piece of information."""

        elif self.conversation_state == "scheduling":
            return f"""You are a friendly sales agent working on scheduling an appointment.
            
Current conversation state: Scheduling appointment
User input: "{user_input}"

Your goals:
1. Help schedule an appointment date and time
2. Extract appointment information from user input
3. Confirm all details before proceeding

Current collected data: {data_status}

Focus on getting a specific appointment date and time."""

        elif self.conversation_state == "creating_hubspot_records":
            return f"""You are finalizing the customer onboarding process.
            
Current conversation state: Creating HubSpot records
User input: "{user_input}"

All information has been collected: {self.collected_data}

Use the available HubSpot tools to:
1. Create the company record
2. Create the contact record
3. Create the lead record
4. Create the engagement record for the appointment

Respond with confirmation of what was created."""

    def _get_data_collection_status(self) -> str:
        """Get a summary of what data has been collected"""
        collected = []
        missing = []
        
        for key, value in self.collected_data.items():
            if value:
                collected.append(f"{key}: {value}")
            else:
                missing.append(key)
        
        status = ""
        if collected:
            status += "Collected: " + ", ".join(collected)
        if missing:
            status += " | Missing: " + ", ".join(missing)
        
        return status or "No data collected yet"
    
    def _extract_info_from_response(self, response_text: str, user_input: str):
        """Extract and update collected information from conversation"""
        user_lower = user_input.lower()
        
        # Simple pattern matching for information extraction
        if "@" in user_input and not self.collected_data["email"]:
            # Extract email
            words = user_input.split()
            for word in words:
                if "@" in word:
                    self.collected_data["email"] = word.strip(".,!?")
                    break
        
        # Extract phone (simple pattern)
        import re
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        phone_match = re.search(phone_pattern, user_input)
        if phone_match and not self.collected_data["phone"]:
            self.collected_data["phone"] = phone_match.group()
        
        # Extract name (if they say "I'm X" or "My name is X")
        if not self.collected_data["name"]:
            name_patterns = [
                r"i'?m\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)",
                r"my name is\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)",
                r"name'?s\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)"
            ]
            for pattern in name_patterns:
                match = re.search(pattern, user_lower)
                if match:
                    self.collected_data["name"] = match.group(1).title()
                    break
        
        # Extract company
        if not self.collected_data["company_name"]:
            company_patterns = [
                r"work at\s+([a-zA-Z][a-zA-Z\s&,.-]+)",
                r"company is\s+([a-zA-Z][a-zA-Z\s&,.-]+)",
                r"from\s+([a-zA-Z][a-zA-Z\s&,.-]+(?:\s+(?:inc|llc|corp|company|ltd))?)"
            ]
            for pattern in company_patterns:
                match = re.search(pattern, user_lower)
                if match:
                    self.collected_data["company_name"] = match.group(1).title()
                    break
        
        # Extract appointment date
        if not self.collected_data["appointment_date"]:
            # Simple date patterns
            date_patterns = [
                r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
                r"\b(\d{1,2}/\d{1,2}/\d{4})\b",
                r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}\b"
            ]
            for pattern in date_patterns:
                match = re.search(pattern, user_lower)
                if match:
                    self.collected_data["appointment_date"] = match.group()
                    break
    
    def _update_conversation_state(self):
        """Update conversation state based on collected data"""
        basic_info_complete = all([
            self.collected_data["name"],
            self.collected_data["email"], 
            self.collected_data["phone"],
            self.collected_data["company_name"]
        ])
        
        if self.conversation_state == "greeting" and any(self.collected_data.values()):
            self.conversation_state = "collecting_info"
        elif self.conversation_state == "collecting_info" and basic_info_complete:
            self.conversation_state = "scheduling"
        elif self.conversation_state == "scheduling" and self.collected_data["appointment_date"]:
            self.conversation_state = "creating_hubspot_records"
    
    async def process_user_input(self, user_input: str) -> str:
        """Process user input and generate appropriate response"""
        
        # Extract information from user input
        self._extract_info_from_response("", user_input)
        
        # Update conversation state
        self._update_conversation_state()
        
        # Generate conversation prompt
        prompt = self.get_conversation_prompt(user_input)
        
        # If we're ready to create HubSpot records, use tools
        if self.conversation_state == "creating_hubspot_records":
            return await self._create_hubspot_records()
        
        # Otherwise, continue conversation
        messages = [{"role": "user", "content": prompt}]
        
        # Get available tools (though we won't use them until final state)
        response = await self.session.list_tools()
        available_tools = [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema
            }
            for tool in response.tools
        ]
        
        # Get response from Claude
        response = self.anthropic.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=1000,
            messages=messages,
            tools=available_tools if self.conversation_state == "creating_hubspot_records" else []
        )
        
        return response.content[0].text
    
    async def create_contact(self) -> str:
        """Create a contact using the MCP tools"""
        try:
            # Create contact
            contact_result = await self.session.call_tool("create_contact", {
                "email": self.collected_data["email"],
                "firstname": self.collected_data["name"].split()[0] if self.collected_data["name"] else "",
                "lastname": self.collected_data["name"].split()[-1] if self.collected_data["name"] else "",
                "phone": self.collected_data["phone"],
                "company": self.collected_data["company_name"]
            })
            
            return f"Contact created: {contact_result.content}"
            
        except Exception as e:
            return f"Error creating contact: {str(e)}"
    
    async def _create_hubspot_records(self) -> str:
        """Create all HubSpot records using the MCP tools"""
        results = []
        
        try:
            # Create company
            company_result = await self.session.call_tool("create_company", {
                "name": self.collected_data["company_name"]
            })
            results.append(f"Company created: {company_result.content}")
            
            # Create contact
            contact_result = await self.session.call_tool("create_contact", {
                "email": self.collected_data["email"],
                "firstname": self.collected_data["name"].split()[0] if self.collected_data["name"] else "",
                "lastname": self.collected_data["name"].split()[-1] if self.collected_data["name"] else "",
                "phone": self.collected_data["phone"],
                "company": self.collected_data["company_name"]
            })
            results.append(f"Contact created: {contact_result.content}")
            
            # Create engagement
            engagement_result = await self.session.call_tool("create_engagement", {
                "type": "MEETING",
                "timestamp": str(int(datetime.now().timestamp() * 1000)),
                "body": f"Scheduled appointment for {self.collected_data['appointment_date']}"
            })
            results.append(f"Engagement created: {engagement_result.content}")
            
            return "Great! I've successfully created your records in our system:\\n\\n" + "\\n".join(results) + "\\n\\nYour appointment has been scheduled and you'll receive a confirmation soon!"
            
        except Exception as e:
            return f"I've collected all your information but encountered an issue creating the records: {str(e)}. Let me try again or connect you with someone who can help."
    
    async def start_conversation(self):
        """Start the interactive conversation"""
        print("\\nHello! I'm your sales assistant. I'm here to help you get started with our services.")
        print("Let me collect some basic information and schedule an appointment for you.")
        print("Type 'quit' to exit at any time.\\n")
        
        # Initial state already set in __init__
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() == "quit":
                    print("\\nThank you for your time! Have a great day!")
                    break
                
                response = await self.process_user_input(user_input)
                print(f"\\nAgent: {response}\\n")
                
                # Show current status (for debugging)
                if any(self.collected_data.values()):
                    print(f"[Debug - Collected so far: {self._get_data_collection_status()}]\\n")
                
                # If we've completed everything, end conversation
                if self.conversation_state == "creating_hubspot_records" and all(self.collected_data.values()):
                    print("Thank you! Everything has been set up. Have a great day!")
                    break
                
            except Exception as e:
                print(f"\\nError: {str(e)}\\n")
    
    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()

async def main():
    if len(sys.argv) < 2:
        print("Usage: python agent.py <path_to_hubspot_server_script>")
        sys.exit(1)
    
    agent = HubSpotAgent()
    try:
        await agent.connect_to_server(sys.argv[1])
        await agent.start_conversation()
    finally:
        await agent.cleanup()

if __name__ == "__main__":
    asyncio.run(main())