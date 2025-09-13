import os
import httpx
from dotenv import load_dotenv
from fastmcp import FastMCP
from datetime import datetime

load_dotenv()

SN_INSTANCE = os.getenv("SN_INSTANCE", "").rstrip("/")
SN_USER = os.getenv("SN_USER")
SN_PASS = os.getenv("SN_PASS")
DEFAULT_TABLE = os.getenv("DEFAULT_TABLE", "incident")

mcp = FastMCP("mcpnowsimilarity")

@mcp.tool()
async def add_incidents(short_description: str, description: str, priority: str, caller: str, state: str, cate: str):
    url = f"{SN_INSTANCE}/api/now/table/incident"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    data = {
        "short_description": short_description,
        "description": description,
        "caller_id": caller if caller else "Guest",
        "priority": priority,
        "state": state,
        "category": cate
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data, auth=(SN_USER, SN_PASS))
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": f"Error creating incident: {str(e)}"}


@mcp.tool()
async def get_table_content():
    url = f"{SN_INSTANCE}/api/now/table/incident"
    headers = {"Accept": "application/json"}
    params = {"sysparm_limit": 5, "sysparm_query": "active=true",
              "sysparm_fields": "number,short_description,state,priority,opened_at,caller_id"}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, auth=(SN_USER, SN_PASS), params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": f"Error fetching incidents: {str(e)}"}


@mcp.tool()
async def update_incident_state(incident_number: str, new_state: str):
    """Update the state of an existing incident in ServiceNow with proper field handling"""
    state_map = {"new": "1", "in progress": "2", "completed": "6", "closed": "7", "cancelled": "8"}
    
    if new_state.lower() not in state_map:
        return {"error": f"Invalid state: {new_state}. Use one of {list(state_map.keys())}"}
    
    try:
        mapped_state = state_map[new_state.lower()]
        
        # Step 1: Lookup sys_id and get current incident data
        url_lookup = f"{SN_INSTANCE}/api/now/table/incident"
        params = {"sysparm_query": f"number={incident_number}", 
                  "sysparm_fields": "sys_id,caller_id,assignment_group,assigned_to"}
        
        async with httpx.AsyncClient() as client:
            lookup_resp = await client.get(url_lookup, auth=(SN_USER, SN_PASS), params=params)
        
        lookup_resp.raise_for_status()
        results = lookup_resp.json().get("result", [])
        
        if not results:
            return {"error": f"Incident {incident_number} not found."}
            
        sys_id = results[0]["sys_id"]
        current_caller = results[0].get("caller_id", "")

        # Step 2: Prepare update payload
        url_update = f"{SN_INSTANCE}/api/now/table/incident/{sys_id}"
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        updates = {"state": mapped_state}

        # Add mandatory fields for terminal states
        if mapped_state in ["6", "7", "8"]:  # Resolved, Closed, or Cancelled
            current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            
            updates.update({
                "close_code": "Solved (Permanently)" if mapped_state != "8" else "Cancelled",
                "close_notes": f"Updated via automated system to {new_state}",
                "resolved_by": current_caller if current_caller else "admin",
                "resolved_at": current_time,
                "work_notes": f"System auto-updated incident to {new_state} state."
            })
            
            if mapped_state == "8":
                updates["u_cancellation_reason"] = "Cancelled via automated system"

        # Step 3: Update the incident
        async with httpx.AsyncClient() as client:
            update_resp = await client.patch(url_update, headers=headers, json=updates, auth=(SN_USER, SN_PASS))
        
        if update_resp.status_code == 403:
            error_details = update_resp.json() if update_resp.content else {}
            return {
                "error": "Permission denied - insufficient privileges or missing required fields",
                "details": error_details,
                "suggestions": [
                    "Check if user has 'itil' role",
                    "Verify state transition is allowed",
                    "Review business rules"
                ]
            }
        elif update_resp.status_code == 400:
            error_details = update_resp.json() if update_resp.content else {}
            return {"error": "Bad request - invalid data or missing required fields", "details": error_details}
            
        update_resp.raise_for_status()
        return update_resp.json()
        
    except Exception as e:
        return {"error": f"Error updating incident: {str(e)}"}


@mcp.tool()
async def update_incident_priority(incident_number: str, new_priority: str):
    try:
        url_lookup = f"{SN_INSTANCE}/api/now/table/incident"
        params = {"sysparm_query": f"number={incident_number}", "sysparm_fields": "sys_id"}
        async with httpx.AsyncClient() as client:
            lookup_resp = await client.get(url_lookup, auth=(SN_USER, SN_PASS), params=params)
        lookup_resp.raise_for_status()
        results = lookup_resp.json().get("result", [])
        if not results:
            return {"error": f"Incident {incident_number} not found."}
        sys_id = results[0]["sys_id"]

        url_update = f"{SN_INSTANCE}/api/now/table/incident/{sys_id}"
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        updates = {"priority": new_priority}
        async with httpx.AsyncClient() as client:
            update_resp = await client.patch(url_update, headers=headers, json=updates, auth=(SN_USER, SN_PASS))
        update_resp.raise_for_status()
        return update_resp.json()
    except Exception as e:
        return {"error": f"Error updating priority: {str(e)}"}


@mcp.tool()
async def close_incident_with_resolution(incident_number: str, resolution_notes: str = "Closed via automated system", close_code: str = "Solved (Permanently)"):
    """Close an incident with proper resolution details"""
    try:
        # Step 1: Get incident details
        url_lookup = f"{SN_INSTANCE}/api/now/table/incident"
        params = {"sysparm_query": f"number={incident_number}", "sysparm_fields": "sys_id,caller_id,state"}
        
        async with httpx.AsyncClient() as client:
            lookup_resp = await client.get(url_lookup, auth=(SN_USER, SN_PASS), params=params)
        
        lookup_resp.raise_for_status()
        results = lookup_resp.json().get("result", [])
        
        if not results:
            return {"error": f"Incident {incident_number} not found."}
            
        sys_id = results[0]["sys_id"]
        current_caller = results[0].get("caller_id", "")

        # Step 2: Close the incident
        url_update = f"{SN_INSTANCE}/api/now/table/incident/{sys_id}"
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        
        current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        
        updates = {
            "state": "7",
            "close_code": close_code,
            "close_notes": resolution_notes,
            "resolved_by": current_caller if current_caller else "admin",
            "resolved_at": current_time,
            "work_notes": f"Incident resolved and closed. Resolution: {resolution_notes}"
        }

        async with httpx.AsyncClient() as client:
            update_resp = await client.patch(url_update, headers=headers, json=updates, auth=(SN_USER, SN_PASS))
        
        if update_resp.status_code in [400, 403]:
            error_details = update_resp.json() if update_resp.content else {}
            return {"error": f"Failed to close incident (HTTP {update_resp.status_code})", "details": error_details}
            
        update_resp.raise_for_status()
        return {"success": True, "message": f"Incident {incident_number} closed successfully", "data": update_resp.json()}
        
    except Exception as e:
        return {"error": f"Error closing incident: {str(e)}"}


@mcp.tool()
async def get_incident_details(incident_number: str):
    """Get detailed information about a specific incident"""
    try:
        url = f"{SN_INSTANCE}/api/now/table/incident"
        params = {"sysparm_query": f"number={incident_number}",
                  "sysparm_fields": "number,short_description,description,state,priority,caller_id,assignment_group,assigned_to,opened_at,resolved_at,close_code,close_notes,work_notes"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, auth=(SN_USER, SN_PASS), params=params)
        
        response.raise_for_status()
        results = response.json().get("result", [])
        
        if not results:
            return {"error": f"Incident {incident_number} not found."}
            
        return {"incident": results[0]}
        
    except Exception as e:
        return {"error": f"Error fetching incident details: {str(e)}"}


if __name__ == "__main__":
    mcp.run(transport='stdio')
