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
            raise ValueError("El script del servidor debe ser un archivo .py o .js")
        
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
        print("\\nConectado al servidor HubSpot con herramientas:", [tool.name for tool in tools])
    
    def get_conversation_prompt(self, user_input: str) -> str:
        """Generate appropriate conversation prompt based on current state"""
        
        data_status = self._get_data_collection_status()
        
        if self.conversation_state == "greeting":
            return f"""Eres un agente de ventas amigable que recopila información de un cliente potencial.
            
Estado actual de la conversación: Saludo inicial
Entrada del usuario: "{user_input}"

Tus objetivos:
1. Comenzar con un saludo cálido y una presentación
2. Comenzar a recopilar: nombre, correo electrónico, teléfono y nombre de la empresa
3. Ser conversacional y natural, no hagas todas las preguntas de una vez
4. Pedir una información a la vez

Datos recopilados actualmente: {data_status}

Responde de manera natural y pide la siguiente información que falte."""

        elif self.conversation_state == "collecting_info":
            return f"""Eres un agente de ventas amigable que continúa recopilando información del cliente.
            
Estado actual de la conversación: Recopilando información básica
Entrada del usuario: "{user_input}"

Tus objetivos:
1. Extraer cualquier información proporcionada por el usuario
2. Continuar recopilando información faltante: nombre, correo electrónico, teléfono, nombre de la empresa
3. Ser natural y conversacional
4. Una vez que tengas toda la información básica, pasar a la programación de citas

Datos recopilados actualmente: {data_status}

Si toda la información básica está recopilada, pregunta sobre programar una cita. De lo contrario, pide la siguiente información que falte."""

        elif self.conversation_state == "scheduling":
            return f"""Eres un agente de ventas amigable trabajando en programar una cita.
            
Estado actual de la conversación: Programando cita
Entrada del usuario: "{user_input}"

Tus objetivos:
1. Ayudar a programar una fecha y hora de cita
2. Extraer información de la cita de la entrada del usuario
3. Confirmar todos los detalles antes de proceder

Datos recopilados actualmente: {data_status}

Concéntrate en obtener una fecha y hora específica para la cita."""

        elif self.conversation_state == "creating_hubspot_records":
            return f"""Estás finalizando el proceso de incorporación del cliente.
            
Estado actual de la conversación: Creando registros de HubSpot
Entrada del usuario: "{user_input}"

Toda la información ha sido recopilada: {self.collected_data}

Usa las herramientas disponibles de HubSpot para:
1. Crear el registro de la empresa
2. Crear el registro del contacto
3. Crear el registro del prospecto
4. Crear el registro de compromiso para la cita

Responde con confirmación de lo que fue creado."""

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
            status += "Recopilado: " + ", ".join(collected)
        if missing:
            status += " | Falta: " + ", ".join(missing)
        
        return status or "No se han recopilado datos aún"
    
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
        
        # Extract name (Spanish and English patterns)
        if not self.collected_data["name"]:
            name_patterns = [
                r"i'?m\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)",
                r"my name is\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)",
                r"name'?s\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)",
                r"soy\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)",
                r"me llamo\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)",
                r"mi nombre es\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)",
                r"nombre\s+es\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)"
            ]
            for pattern in name_patterns:
                match = re.search(pattern, user_lower)
                if match:
                    self.collected_data["name"] = match.group(1).title()
                    break
        
        # Extract company (Spanish and English patterns)
        if not self.collected_data["company_name"]:
            company_patterns = [
                r"work at\s+([a-zA-Z][a-zA-Z\s&,.-]+)",
                r"company is\s+([a-zA-Z][a-zA-Z\s&,.-]+)",
                r"from\s+([a-zA-Z][a-zA-Z\s&,.-]+(?:\s+(?:inc|llc|corp|company|ltd))?)",
                r"trabajo en\s+([a-zA-Z][a-zA-Z\s&,.-]+)",
                r"trabajo para\s+([a-zA-Z][a-zA-Z\s&,.-]+)",
                r"mi empresa es\s+([a-zA-Z][a-zA-Z\s&,.-]+)",
                r"empresa es\s+([a-zA-Z][a-zA-Z\s&,.-]+)",
                r"de\s+([a-zA-Z][a-zA-Z\s&,.-]+(?:\s+(?:inc|llc|corp|company|ltd|sa|srl))?)",
                r"en\s+([a-zA-Z][a-zA-Z\s&,.-]+(?:\s+(?:inc|llc|corp|company|ltd|sa|srl))?)"
            ]
            for pattern in company_patterns:
                match = re.search(pattern, user_lower)
                if match:
                    self.collected_data["company_name"] = match.group(1).title()
                    break
        
        # Extract appointment date (Spanish and English patterns)
        if not self.collected_data["appointment_date"]:
            # Date patterns for both languages
            date_patterns = [
                r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
                r"\b(lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)\b",
                r"\b(\d{1,2}/\d{1,2}/\d{4})\b",
                r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}\b",
                r"\b(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+\d{1,2}\b",
                r"\bel\s+(lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)\b",
                r"\bmañana\b",
                r"\btomorrow\b"
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
            
            return f"Contacto creado: {contact_result.content}"
            
        except Exception as e:
            return f"Error creando contacto: {str(e)}"
    
    async def _create_hubspot_records(self) -> str:
        """Create all HubSpot records using the MCP tools"""
        results = []
        
        try:
            # Create company
            company_result = await self.session.call_tool("create_company", {
                "name": self.collected_data["company_name"]
            })
            results.append(f"Empresa creada: {company_result.content}")
            
            # Create contact
            contact_result = await self.session.call_tool("create_contact", {
                "email": self.collected_data["email"],
                "firstname": self.collected_data["name"].split()[0] if self.collected_data["name"] else "",
                "lastname": self.collected_data["name"].split()[-1] if self.collected_data["name"] else "",
                "phone": self.collected_data["phone"],
                "company": self.collected_data["company_name"]
            })
            results.append(f"Contacto creado: {contact_result.content}")
            
            # Create engagement
            engagement_result = await self.session.call_tool("create_engagement", {
                "type": "MEETING",
                "timestamp": str(int(datetime.now().timestamp() * 1000)),
                "body": f"Cita programada para {self.collected_data['appointment_date']}"
            })
            results.append(f"Compromiso creado: {engagement_result.content}")
            
            return "¡Excelente! He creado exitosamente tus registros en nuestro sistema:\\n\\n" + "\\n".join(results) + "\\n\\n¡Tu cita ha sido programada y recibirás una confirmación pronto!"
            
        except Exception as e:
            return f"He recopilado toda tu información pero encontré un problema creando los registros: {str(e)}. Déjame intentar de nuevo o conectarte con alguien que pueda ayudarte."
    
    async def start_conversation(self):
        """Start the interactive conversation"""
        print("\\n¡Hola! Soy tu asistente de ventas. Estoy aquí para ayudarte a comenzar con nuestros servicios.")
        print("Déjame recopilar alguna información básica y programar una cita para ti.")
        print("Escribe 'quit' para salir en cualquier momento.\\n")
        
        # Initial state already set in __init__
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() == "quit":
                    print("\\n¡Gracias por tu tiempo! ¡Que tengas un gran día!")
                    break
                
                response = await self.process_user_input(user_input)
                print(f"\\nAgente: {response}\\n")
                
                # Show current status (for debugging)
                if any(self.collected_data.values()):
                    print(f"[Debug - Recopilado hasta ahora: {self._get_data_collection_status()}]\\n")
                
                # If we've completed everything, end conversation
                if self.conversation_state == "creating_hubspot_records" and all(self.collected_data.values()):
                    print("¡Gracias! Todo ha sido configurado. ¡Que tengas un gran día!")
                    break
                
            except Exception as e:
                print(f"\\nError: {str(e)}\\n")
    
    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()

async def main():
    if len(sys.argv) < 2:
        print("Uso: python agent.py <ruta_al_script_del_servidor_hubspot>")
        sys.exit(1)
    
    agent = HubSpotAgent()
    try:
        await agent.connect_to_server(sys.argv[1])
        await agent.start_conversation()
    finally:
        await agent.cleanup()

if __name__ == "__main__":
    asyncio.run(main())