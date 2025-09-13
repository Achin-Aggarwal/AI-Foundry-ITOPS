from llm import get_llm_response
import json
import re

INTENT_PROMPT = """
You are an advanced intent classifier. Analyze the user's message and classify it into one of these categories:

1. **install** - User wants to install, download, or get software/applications
2. **cs_it** - User asks CS/IT related questions (programming, algorithms, databases, networking, system administration, software development, computer science concepts, etc.)
3. **other** - General conversation or other topics

For "install" intent:
- Extract specific software names mentioned by the user
- If user just says "install software", "download apps", "I need software" etc. without specifying names, return empty apps list

For "cs_it" intent:
- Topics include: programming languages, algorithms, data structures, databases, networking, cybersecurity, system administration, software engineering, computer architecture, etc.

Output JSON ONLY in this exact format:
{
  "intent": "install" | "cs_it" | "other",
  "apps": ["list", "of", "specific", "software", "names"]
}

Examples:
- "install zoom and slack" → {"intent": "install", "apps": ["zoom", "slack"]}
- "I want to download software" → {"intent": "install", "apps": []}
- "What is a binary search tree?" → {"intent": "cs_it", "apps": []}
- "How do I implement sorting algorithms?" → {"intent": "cs_it", "apps": []}
- "Hello how are you?" → {"intent": "other", "apps": []}
"""

def parse_intent(user_message: str) -> dict:
    try:
        # Get LLM response for intent classification
        response = get_llm_response(f"{INTENT_PROMPT}\nUser message: {user_message}")
        
        # Clean the response - sometimes LLM adds extra text
        response = response.strip()
        
        # Try to extract JSON from the response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            parsed = json.loads(json_str)
            
            # Validate the response format
            if "intent" in parsed and "apps" in parsed:
                # Ensure apps is a list
                if not isinstance(parsed["apps"], list):
                    parsed["apps"] = []
                
                # Normalize app names to lowercase
                parsed["apps"] = [app.lower().strip() for app in parsed["apps"]]
                
                # Validate intent value
                valid_intents = ["install", "cs_it", "other"]
                if parsed["intent"] not in valid_intents:
                    parsed["intent"] = "other"
                
                return parsed
        
        # Fallback parsing if JSON parsing fails
        return fallback_intent_detection(user_message)
        
    except Exception as e:
        print(f"Error in intent parsing: {e}")
        return fallback_intent_detection(user_message)

def fallback_intent_detection(user_message: str) -> dict:
    """
    Fallback intent detection using keyword matching
    """
    message_lower = user_message.lower()
    
    # Check for install intent keywords
    install_keywords = [
        "install", "download", "get", "setup", "add", "deploy", 
        "software", "application", "app", "program", "tool"
    ]
    
    # Check for CS/IT keywords
    cs_it_keywords = [
        "algorithm", "programming", "code", "python", "java", "javascript", 
        "database", "sql", "network", "security", "server", "api", "framework",
        "data structure", "binary tree", "sorting", "recursion", "oop",
        "machine learning", "ai", "system design", "architecture", "devops",
        "git", "version control", "debugging", "testing", "deployment",
        "cloud", "aws", "azure", "docker", "kubernetes", "linux", "windows"
    ]
    
    # Common software names for extraction
    common_software = [
        "zoom", "slack", "teams", "discord", "skype", "chrome", "firefox",
        "vscode", "visual studio", "pycharm", "intellij", "eclipse",
        "photoshop", "illustrator", "premiere", "after effects",
        "office", "word", "excel", "powerpoint", "outlook",
        "spotify", "vlc", "winrar", "7zip", "notepad++", "sublime",
        "docker", "git", "node", "npm", "python", "java"
    ]
    
    # Check for install intent
    if any(keyword in message_lower for keyword in install_keywords):
        # Extract software names
        apps = []
        for software in common_software:
            if software in message_lower:
                apps.append(software)
        
        return {"intent": "install", "apps": apps}
    
    # Check for CS/IT intent
    if any(keyword in message_lower for keyword in cs_it_keywords):
        return {"intent": "cs_it", "apps": []}
    
    # Default to other
    return {"intent": "other", "apps": []}