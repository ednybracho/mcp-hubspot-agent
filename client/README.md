# HubSpot Agent Client

This MCP Client acts as a conversational agent that collects customer information and creates records in HubSpot.

## Features

- **Conversational Data Collection**: Naturally collects customer information during conversation
- **Smart Information Extraction**: Automatically extracts name, email, phone, and company from user responses
- **Appointment Scheduling**: Handles appointment date collection
- **HubSpot Integration**: Automatically creates Contact, Company, Deal, and Engagement records

## Information Collected

1. **Name**: Customer's full name
2. **Email**: Customer's email address
3. **Phone**: Customer's phone number
4. **Company**: Customer's company name
5. **Appointment Date**: Preferred appointment date/time

## Conversation Flow

1. **Greeting**: Warm introduction and start collecting basic info
2. **Information Collection**: Gather name, email, phone, company
3. **Appointment Scheduling**: Schedule appointment date
4. **HubSpot Record Creation**: Create all necessary records in HubSpot

## Usage

```bash
# Install dependencies
uv sync

# Run the agent (requires running HubSpot server)
python agent.py ../server/hubspot_server.py
```

## Environment Variables

Create a `.env` file in the root directory with:

```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
HUBSPOT_API_KEY=your_hubspot_private_app_token_here
```