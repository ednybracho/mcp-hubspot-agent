import os
from typing import Optional
from hubspot import HubSpot
from hubspot.crm.contacts import SimplePublicObjectInputForCreate
from hubspot.crm.companies import SimplePublicObjectInputForCreate as CompanyInput
from hubspot.crm.deals import SimplePublicObjectInputForCreate as DealInput
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("hubspot-integration")

# HubSpot API configuration
HUBSPOT_API_KEY = os.getenv("HUBSPOT_API_KEY")

if not HUBSPOT_API_KEY:
    print("Warning: HUBSPOT_API_KEY environment variable not set")

# Initialize HubSpot client
hubspot_client = HubSpot(access_token=HUBSPOT_API_KEY) if HUBSPOT_API_KEY else None

@mcp.tool()
def create_contact(
    email: str,
    firstname: str = "",
    lastname: str = "",
    phone: str = "",
    company: str = "",
    website: str = "",
    jobtitle: str = ""
) -> str:
    """Create a new contact in HubSpot.
    
    Args:
        email: Contact's email address (required)
        firstname: Contact's first name
        lastname: Contact's last name  
        phone: Contact's phone number
        company: Contact's company name
        website: Contact's website
        jobtitle: Contact's job title
    """
    
    if not hubspot_client:
        return "HubSpot API key not configured"
    
    properties = {"email": email}
    
    # Add optional properties if provided
    if firstname:
        properties["firstname"] = firstname
    if lastname:
        properties["lastname"] = lastname
    if phone:
        properties["phone"] = phone
    if company:
        properties["company"] = company
    if website:
        properties["website"] = website
    if jobtitle:
        properties["jobtitle"] = jobtitle
    
    try:
        contact_input = SimplePublicObjectInputForCreate(properties=properties)
        result = hubspot_client.crm.contacts.basic_api.create(simple_public_object_input_for_create=contact_input)
        return f"Contact created successfully with ID: {result.id}"
    except Exception as e:
        return f"Failed to create contact: {str(e)}"

@mcp.tool()
def create_company(
    name: str,
    domain: str = "",
    industry: str = "",
    phone: str = "",
    city: str = "",
    state: str = "",
    country: str = ""
) -> str:
    """Create a new company in HubSpot.
    
    Args:
        name: Company name (required)
        domain: Company domain/website
        industry: Company industry
        phone: Company phone number
        city: Company city
        state: Company state/province
        country: Company country
    """
    
    if not hubspot_client:
        return "HubSpot API key not configured"
    
    properties = {"name": name}
    
    # Add optional properties if provided
    if domain:
        properties["domain"] = domain
    if industry:
        properties["industry"] = industry
    if phone:
        properties["phone"] = phone
    if city:
        properties["city"] = city
    if state:
        properties["state"] = state
    if country:
        properties["country"] = country
    
    try:
        company_input = CompanyInput(properties=properties)
        result = hubspot_client.crm.companies.basic_api.create(simple_public_object_input_for_create=company_input)
        return f"Company created successfully with ID: {result.id}"
    except Exception as e:
        return f"Failed to create company: {str(e)}"

@mcp.tool()
def create_lead(
    dealname: str,
    amount: str = "0",
    dealstage: str = "appointmentscheduled",
    pipeline: str = "default",
    closedate: str = "",
    description: str = ""
) -> str:
    """Create a new lead (deal) in HubSpot.
    
    Args:
        dealname: Deal name (required)
        amount: Deal amount in cents
        dealstage: Deal stage (default: appointmentscheduled)
        pipeline: Sales pipeline (default: default)
        closedate: Expected close date (YYYY-MM-DD format)
        description: Deal description
    """
    
    if not hubspot_client:
        return "HubSpot API key not configured"
    
    properties = {
        "dealname": dealname,
        "amount": amount,
        "dealstage": dealstage,
        "pipeline": pipeline
    }
    
    # Add optional properties if provided
    if closedate:
        properties["closedate"] = closedate
    if description:
        properties["description"] = description
    
    try:
        deal_input = DealInput(properties=properties)
        result = hubspot_client.crm.deals.basic_api.create(simple_public_object_input_for_create=deal_input)
        return f"Lead created successfully with ID: {result.id}"
    except Exception as e:
        return f"Failed to create lead: {str(e)}"


@mcp.tool()
def search_contacts(query: str, limit: int = 10) -> str:
    """Search for contacts in HubSpot.
    
    Args:
        query: Search query (email, name, company, etc.)
        limit: Maximum number of results to return (default: 10)
    """
    
    if not hubspot_client:
        return "HubSpot API key not configured"
    
    try:
        from hubspot.crm.contacts import PublicObjectSearchRequest
        
        search_request = PublicObjectSearchRequest(
            query=query,
            limit=limit,
            after=0
        )
        
        result = hubspot_client.crm.contacts.search_api.do_search(public_object_search_request=search_request)
        
        if not result.results:
            return "No contacts found matching the search query."
        
        contact_list = []
        for contact in result.results:
            props = contact.properties
            contact_info = f"ID: {contact.id}, "
            contact_info += f"Name: {props.get('firstname', '')} {props.get('lastname', '')}, "
            contact_info += f"Email: {props.get('email', '')}, "
            contact_info += f"Company: {props.get('company', '')}"
            contact_list.append(contact_info)
        
        return "Found contacts:\n" + "\n".join(contact_list)
    except Exception as e:
        return f"Failed to search contacts: {str(e)}"

@mcp.tool()
def search_companies(query: str, limit: int = 10) -> str:
    """Search for companies in HubSpot.
    
    Args:
        query: Search query (company name, domain, etc.)
        limit: Maximum number of results to return (default: 10)
    """
    
    if not hubspot_client:
        return "HubSpot API key not configured"
    
    try:
        from hubspot.crm.companies import PublicObjectSearchRequest
        
        search_request = PublicObjectSearchRequest(
            query=query,
            limit=limit,
            after=0
        )
        
        result = hubspot_client.crm.companies.search_api.do_search(public_object_search_request=search_request)
        
        if not result.results:
            return "No companies found matching the search query."
        
        company_list = []
        for company in result.results:
            props = company.properties
            company_info = f"ID: {company.id}, "
            company_info += f"Name: {props.get('name', '')}, "
            company_info += f"Domain: {props.get('domain', '')}, "
            company_info += f"Industry: {props.get('industry', '')}"
            company_list.append(company_info)
        
        return "Found companies:\n" + "\n".join(company_list)
    except Exception as e:
        return f"Failed to search companies: {str(e)}"

@mcp.tool()
def create_engagement(
    type: str = "MEETING",
    timestamp: str = "",
    body: str = "",
    subject: str = ""
) -> str:
    """Create a new engagement (activity) in HubSpot.
    
    Args:
        type: Engagement type (MEETING, CALL, EMAIL, NOTE, etc.)
        timestamp: Unix timestamp in milliseconds
        body: Engagement body/description
        subject: Engagement subject/title
    """
    
    if not hubspot_client:
        return "HubSpot API key not configured"
    
    try:
        from hubspot.crm.objects.notes import SimplePublicObjectInputForCreate as NoteInput
        import time
        
        properties = {
            "hs_note_body": body or f"{type} engagement created",
            "hs_timestamp": timestamp or str(int(time.time() * 1000))
        }
        
        if subject:
            properties["hs_note_title"] = subject
        
        # Create as a note since engagements require more complex setup
        note_input = NoteInput(properties=properties)
        result = hubspot_client.crm.objects.notes.basic_api.create(simple_public_object_input_for_create=note_input)
        return f"Engagement created successfully with ID: {result.id}"
    except Exception as e:
        return f"Failed to create engagement: {str(e)}"

if __name__ == "__main__":
    # Run the server
    mcp.run(transport="stdio")