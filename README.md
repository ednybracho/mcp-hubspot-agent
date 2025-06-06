# HubSpot MCP Agent

A complete MCP (Model Context Protocol) solution for HubSpot integration featuring an intelligent conversational agent that collects customer information and automatically creates records in HubSpot.

## 🏗️ Architecture

This project consists of two main components:

### 1. **MCP Client (Agent)** (`/client/`)
- Conversational AI agent that naturally collects customer information
- Intelligent information extraction from user responses
- Handles appointment scheduling
- Orchestrates HubSpot record creation

### 2. **MCP Server (HubSpot Integration)** (`/server/`)
- Provides HubSpot API integration tools
- Creates and manages contacts, companies, deals, and engagements
- Handles HubSpot authentication and error handling

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- HubSpot account with private app access
- Anthropic API key
- `uv` package manager (or `pip`)

### 1. Clone and Setup

```bash
cd /Users/ebracho/development/mcp-hubspot-agent

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env
```

### 2. Install Dependencies

```bash
# Install client dependencies
cd client && uv sync

# Install server dependencies  
cd ../server && uv sync
```

### 3. Configure HubSpot

1. Go to your HubSpot account → Settings → Integrations → Private Apps
2. Create a new private app
3. Grant these scopes:
   - `crm.objects.contacts.read` & `crm.objects.contacts.write`
   - `crm.objects.companies.read` & `crm.objects.companies.write`
   - `crm.objects.deals.read` & `crm.objects.deals.write`
   - `crm.objects.engagements.read` & `crm.objects.engagements.write`
4. Copy the access token to your `.env` file

### 4. Test Connection

```bash
python test_connection.py
```

### 5. Run the Agent

```bash
python client/agent.py server/hubspot_server.py
```

## 💬 How It Works

### Conversation Flow

1. **Greeting Phase**: Agent introduces itself and begins collecting information
2. **Information Collection**: Naturally gathers:
   - Customer name
   - Email address
   - Phone number
   - Company name
3. **Appointment Scheduling**: Collects preferred appointment date/time
4. **HubSpot Integration**: Automatically creates:
   - Company record
   - Contact record
   - Deal/Lead record
   - Engagement/Meeting record

### Example Conversation

```
Agent: Hello! I'm your sales assistant. I'm here to help you get started with our services.
       Let me collect some basic information and schedule an appointment for you.

You: Hi, I'm interested in your services

Agent: Great to meet you! I'd love to help you get started. Could you tell me your name?

You: I'm John Smith from Acme Corp, you can reach me at john@acme.com or 555-123-4567

Agent: Perfect John! I have your information from Acme Corp. Now, when would be a good time 
       for us to schedule a consultation?

You: How about next Friday?

Agent: Excellent! I've scheduled you for next Friday. Let me create your records in our system...

Agent: Great! I've successfully created your records in our system:
       - Company created: Acme Corp
       - Contact created: John Smith
       - Engagement created: Meeting scheduled for next Friday
       
       Your appointment has been scheduled and you'll receive a confirmation soon!
```

## 🛠️ Available MCP Tools

The HubSpot server provides these tools:

- `create_contact` - Create new contacts
- `create_company` - Create new companies  
- `create_deal` - Create new deals/leads
- `create_engagement` - Create activities (meetings, calls, notes)
- `search_contacts` - Search existing contacts
- `search_companies` - Search existing companies

## 📁 Project Structure

```
mcp-hubspot-agent/
├── client/
│   ├── agent.py              # Main agent application
│   ├── pyproject.toml        # Client dependencies
│   └── README.md             # Client documentation
├── server/
│   ├── hubspot_server.py     # HubSpot MCP server
│   ├── pyproject.toml        # Server dependencies
│   └── README.md             # Server documentation
├── test_connection.py        # Connection test script
├── .env.example              # Environment template
└── README.md                 # This file
```

## 🔧 Configuration

### Environment Variables

```bash
# HubSpot Configuration
HUBSPOT_API_KEY=your_hubspot_private_app_token

# Anthropic Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### Customization

The agent can be customized by modifying:

- **Conversation flow**: Edit the state machine in `client/agent.py`
- **Information extraction**: Modify regex patterns for data extraction
- **HubSpot fields**: Add/modify properties in server tools
- **Engagement types**: Customize engagement creation logic

## 🔍 Troubleshooting

### Common Issues

1. **"HubSpot API key not configured"**
   - Ensure `HUBSPOT_API_KEY` is set in `.env`
   - Verify the private app token is correct

2. **"Permission denied" errors**
   - Check that your HubSpot private app has the required scopes
   - Verify the scopes match those listed above

3. **Connection failures**
   - Run `python test_connection.py` to diagnose issues
   - Check that both client and server dependencies are installed

### Debug Mode

Enable debug output by modifying the agent to show collection status:

```python
# In agent.py, uncomment the debug line:
print(f"[Debug - Collected so far: {self._get_data_collection_status()}]")
```

## 📝 License

This project is provided as-is for educational and development purposes.

## 🤝 Contributing

Feel free to submit issues and enhancement requests!