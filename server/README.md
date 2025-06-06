# HubSpot MCP Server

This MCP Server provides tools for integrating with HubSpot CRM using the official HubSpot Python client library. It allows creation and management of contacts, companies, and deals.

## Available Tools

### Contact Management
- **create_contact**: Create a new contact with email, name, phone, company details
- **search_contacts**: Search for existing contacts by query

### Company Management  
- **create_company**: Create a new company with name, domain, industry details
- **search_companies**: Search for existing companies by query

### Deal Management
- **create_deal**: Create a new deal/lead with amount, stage, pipeline details

### Engagement Management
- **create_engagement**: Create activities (meetings, calls, notes) with type, timestamp, and body

## HubSpot API Setup

1. Create a private app in your HubSpot account:
   - Go to Settings > Integrations > Private Apps
   - Create a new private app
   - Grant necessary scopes (contacts, companies, deals)
   - Copy the access token

2. Set environment variable:
   ```bash
   export HUBSPOT_API_KEY=your_private_app_token
   ```

## Usage

```bash
# Install dependencies
uv sync

# Run the server
python hubspot_server.py
```

## Dependencies

This server uses the official HubSpot Python client library:
- `hubspot-api-client>=9.1.0`

## Required HubSpot Scopes

Your HubSpot private app needs these scopes:
- `crm.objects.contacts.read`
- `crm.objects.contacts.write`
- `crm.objects.companies.read`
- `crm.objects.companies.write`
- `crm.objects.deals.read`
- `crm.objects.deals.write`