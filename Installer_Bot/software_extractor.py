# software_extractor.py
from llm import get_llm_response
from db_connector import get_all_software_names, search_software_by_partial_name
import json
import re


def get_software_extraction_prompt(available_software: list[str], user_message: str) -> str:
    """
    Create a prompt for LLM to extract software names from user message.
    """
    software_list = "\n".join([f"- {software}" for software in available_software])
    
    prompt = f"""You are a software name extraction expert. Your task is to identify which software from the available database the user wants to install.

AVAILABLE SOFTWARE IN DATABASE:
{software_list}

USER MESSAGE: "{user_message}"

INSTRUCTIONS:
1. Extract software names that the user wants to install
2. Match user requests to the EXACT names from the available software list above
3. Handle common variations (e.g., "chrome" → "Google Chrome", "vscode" → "Visual Studio Code")
4. If user says "install software" or similar without specifying, return empty apps list
5. If no matches found, return empty apps list

OUTPUT FORMAT (JSON only):
{{
  "intent": "install" | "other",
  "apps": ["Exact Software Name 1", "Exact Software Name 2"],
  "confidence": "high" | "medium" | "low",
  "reasoning": "Brief explanation of matches made"
}}

EXAMPLES:
User: "install chrome" → {{"intent": "install", "apps": ["Google Chrome"], "confidence": "high", "reasoning": "Chrome matches Google Chrome"}}
User: "I need vscode and python" → {{"intent": "install", "apps": ["Visual Studio Code", "Python"], "confidence": "high", "reasoning": "vscode→Visual Studio Code, python→Python"}}
User: "what is AI?" → {{"intent": "other", "apps": [], "confidence": "high", "reasoning": "Not an installation request"}}
"""
    return prompt


def extract_software_names(user_message: str) -> dict:
    """
    Use LLM to extract software names from user message based on available database software.
    """
    try:
        # Get available software from database
        available_software = get_all_software_names()
        
        if not available_software:
            return {"intent": "other", "apps": [], "confidence": "low", "reasoning": "No software available in database"}
        
        # Create extraction prompt
        prompt = get_software_extraction_prompt(available_software, user_message)
        
        # Get LLM response
        response = get_llm_response(prompt)
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            result = json.loads(json_str)
            
            # Validate structure
            if all(key in result for key in ["intent", "apps", "confidence"]):
                # Ensure apps is a list of strings
                if not isinstance(result["apps"], list):
                    result["apps"] = []
                
                # Verify extracted software names exist in database
                verified_apps = []
                for app in result["apps"]:
                    if app in available_software:
                        verified_apps.append(app)
                    else:
                        # Try fuzzy matching
                        matches = search_software_by_partial_name(app)
                        if matches:
                            verified_apps.append(matches[0])  # Take best match
                
                result["apps"] = verified_apps
                return result
        
        # Fallback if JSON parsing fails
        return fallback_extraction(user_message, available_software)
        
    except Exception as e:
        print(f"Software extraction error: {e}")
        return {"intent": "other", "apps": [], "confidence": "low", "reasoning": f"Extraction failed: {str(e)}"}


def fallback_extraction(user_message: str, available_software: list[str]) -> dict:
    """
    Fallback extraction using keyword matching when LLM fails.
    """
    message_lower = user_message.lower()
    
    # Check for install intent
    install_keywords = ["install", "setup", "download", "get", "need", "want"]
    if not any(keyword in message_lower for keyword in install_keywords):
        return {"intent": "other", "apps": [], "confidence": "high", "reasoning": "No install keywords detected"}
    
    # Find matching software
    found_software = []
    for software in available_software:
        software_lower = software.lower()
        software_words = software_lower.split()
        
        # Check if any word from software name is in user message
        for word in software_words:
            if len(word) > 2 and word in message_lower:  # Ignore very short words
                found_software.append(software)
                break
        
        # Check common abbreviations
        if "visual studio code" == software_lower and any(term in message_lower for term in ["vscode", "vs code"]):
            found_software.append(software)
        elif "google chrome" == software_lower and "chrome" in message_lower:
            found_software.append(software)
        elif "microsoft teams" == software_lower and "teams" in message_lower:
            found_software.append(software)
        elif "node.js" == software_lower and any(term in message_lower for term in ["node", "nodejs"]):
            found_software.append(software)
        elif "docker desktop" == software_lower and "docker" in message_lower:
            found_software.append(software)
    
    # Remove duplicates
    found_software = list(dict.fromkeys(found_software))
    
    confidence = "medium" if found_software else "low"
    reasoning = f"Fallback matching found {len(found_software)} software"
    
    return {
        "intent": "install",
        "apps": found_software,
        "confidence": confidence,
        "reasoning": reasoning
    }


def validate_software_exists(software_names: list[str]) -> tuple[list[str], list[str]]:
    """
    Validate that software names exist in database.
    Returns (found_software, missing_software)
    """
    available_software = get_all_software_names()
    found = []
    missing = []
    
    for software in software_names:
        if software in available_software:
            found.append(software)
        else:
            missing.append(software)
    
    return found, missing