from botbuilder.schema import Attachment
import json

def build_software_card(app_name: str, versions: list[str]) -> Attachment:
    """
    Returns an adaptive card attachment for a given app with version choices.
    """
    card_json = {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock", 
                "text": f"📦 Install {app_name.title()}", 
                "weight": "Bolder", 
                "size": "Large",
                "color": "Accent"
            },
            {
                "type": "TextBlock", 
                "text": "Please select the version you want to install:", 
                "size": "Medium",
                "spacing": "Medium"
            },
            {
                "type": "Input.ChoiceSet",
                "id": "version",
                "style": "compact",
                "placeholder": "Choose version...",
                "choices": [{"title": f"Version {v}", "value": v} for v in versions]
            }
        ],
        "actions": [
            {
                "type": "Action.Submit", 
                "title": "🚀 Proceed With Installation", 
                "data": {
                    "action": "install",
                    "app": app_name,
                    "timestamp": "{{DATE()}}"
                }
            }
        ]
    }

    return Attachment(content_type="application/vnd.microsoft.card.adaptive", content=card_json)


def build_software_selection_card(catalog: dict) -> Attachment:
    """
    Returns an adaptive card for software selection when user wants to install software 
    but didn't specify which ones.
    """
    # Create choices from catalog
    choices = []
    for app_name, versions in catalog.items():
        latest_version = versions[-1] if versions else "Unknown"
        choices.append({
            "title": f"{app_name.title()} (Latest: {latest_version})",
            "value": app_name
        })
    
    # Sort choices alphabetically
    choices.sort(key=lambda x: x["title"])
    
    card_json = {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock", 
                "text": "🛠️ Software Installation Center", 
                "weight": "Bolder", 
                "size": "Large",
                "color": "Accent"
            },
            {
                "type": "TextBlock", 
                "text": "Select the software you want to install from our catalog:", 
                "size": "Medium",
                "spacing": "Medium",
                "wrap": True
            },
            {
                "type": "Input.ChoiceSet",
                "id": "selected_software",
                "style": "expanded",
                "isMultiSelect": True,
                "choices": choices,
                "placeholder": "Select one or more software..."
            }
        ],
        "actions": [
            {
                "type": "Action.Submit", 
                "title": "📋 Show Installation Options", 
                "data": {
                    "action": "show_versions",
                    "timestamp": "{{DATE()}}"
                }
            }
        ]
    }

    return Attachment(content_type="application/vnd.microsoft.card.adaptive", content=card_json)


def build_admin_approval_card(approval_data: dict) -> Attachment:
    """
    Returns an adaptive card for admin approval of software installation.
    """
    incident_number = approval_data.get("incident_number", "N/A")
    software_name = approval_data.get("software_name", "Unknown")
    version = approval_data.get("version", "N/A")
    requester = approval_data.get("requester", "Unknown User")
    
    card_json = {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": "🔐 ADMIN APPROVAL REQUIRED",
                "weight": "Bolder",
                "size": "Large",
                "color": "Warning",
                "horizontalAlignment": "Center"
            },
            {
                "type": "FactSet",
                "spacing": "Medium",
                "facts": [
                    {
                        "title": "📋 Incident Number:",
                        "value": incident_number
                    },
                    {
                        "title": "👤 Requester:",
                        "value": requester
                    },
                    {
                        "title": "📦 Software:",
                        "value": f"{software_name.title()}"
                    },
                    {
                        "title": "🏷️ Version:",
                        "value": version
                    }
                ]
            },
            {
                "type": "TextBlock",
                "text": "A user wants to install the above software. Do you want to allow this installation?",
                "size": "Medium",
                "spacing": "Medium",
                "wrap": True,
                "color": "Default"
            },
            {
                "type": "Input.Text",
                "id": "admin_comments",
                "placeholder": "Optional: Add comments for approval...",
                "isMultiline": True,
                "maxLength": 500,
                "spacing": "Medium"
            },
            {
                "type": "Input.Text",
                "id": "rejection_reason",
                "placeholder": "If rejecting, please provide reason...",
                "isMultiline": True,
                "maxLength": 500,
                "spacing": "Small"
            }
        ],
        "actions": [
            {
                "type": "Action.Submit",
                "title": "✅ APPROVE",
                "style": "positive",
                "data": {
                    "action": "admin_approve",
                    "incident_number": incident_number,
                    "software_name": software_name,
                    "version": version,
                    "requester": requester,
                    "timestamp": "{{DATE()}}"
                }
            },
            {
                "type": "Action.Submit",
                "title": "❌ REJECT",
                "style": "destructive",
                "data": {
                    "action": "admin_reject",
                    "incident_number": incident_number,
                    "software_name": software_name,
                    "version": version,
                    "requester": requester,
                    "timestamp": "{{DATE()}}"
                }
            }
        ]
    }

    return Attachment(content_type="application/vnd.microsoft.card.adaptive", content=card_json)
# 1. Add feedback card function to card_builder.py

def build_feedback_card(incident_number: str, software_name: str, version: str, installation_status: str) -> Attachment:
    """
    Returns an adaptive card for collecting user feedback after installation completion.
    """
    status_color = "Good" if installation_status == "success" else "Attention"
    status_icon = "✅" if installation_status == "success" else "❌"
    status_text = "Installation Completed Successfully!" if installation_status == "success" else "Installation Failed"
    
    card_json = {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": f"{status_icon} {status_text}",
                "weight": "Bolder",
                "size": "Large",
                "color": status_color,
                "horizontalAlignment": "Center"
            },
            {
                "type": "FactSet",
                "spacing": "Medium",
                "facts": [
                    {
                        "title": "📋 Incident Number:",
                        "value": incident_number
                    },
                    {
                        "title": "📦 Software:",
                        "value": f"{software_name.title()}"
                    },
                    {
                        "title": "🏷️ Version:",
                        "value": version
                    }
                ]
            },
            {
                "type": "TextBlock",
                "text": "Please share your feedback about the installation process:",
                "size": "Medium",
                "spacing": "Medium",
                "wrap": True
            },
            {
                "type": "TextBlock",
                "text": "Rate your experience:",
                "weight": "Bolder",
                "spacing": "Medium"
            },
            {
                "type": "Input.ChoiceSet",
                "id": "rating",
                "style": "expanded",
                "choices": [
                    {
                        "title": "⭐⭐⭐⭐⭐ Excellent (5/5)",
                        "value": "5"
                    },
                    {
                        "title": "⭐⭐⭐⭐ Good (4/5)",
                        "value": "4"
                    },
                    {
                        "title": "⭐⭐⭐ Average (3/5)",
                        "value": "3"
                    },
                    {
                        "title": "⭐⭐ Below Average (2/5)",
                        "value": "2"
                    },
                    {
                        "title": "⭐ Poor (1/5)",
                        "value": "1"
                    }
                ],
                "value": "5" if installation_status == "success" else "3"
            },
            {
                "type": "TextBlock",
                "text": "Additional Comments:",
                "weight": "Bolder",
                "spacing": "Medium"
            },
            {
                "type": "Input.Text",
                "id": "feedback_comments",
                "placeholder": "Please share any comments, suggestions, or issues you experienced...",
                "isMultiline": True,
                "maxLength": 1000,
                "spacing": "Small"
            }
        ],
        "actions": [
            {
                "type": "Action.Submit",
                "title": "📝 Submit Feedback",
                "style": "positive",
                "data": {
                    "action": "submit_feedback",
                    "incident_number": incident_number,
                    "software_name": software_name,
                    "version": version,
                    "installation_status": installation_status,
                    "timestamp": "{{DATE()}}"
                }
            },
            {
                "type": "Action.Submit",
                "title": "Skip Feedback",
                "data": {
                    "action": "skip_feedback",
                    "incident_number": incident_number,
                    "software_name": software_name,
                    "version": version,
                    "installation_status": installation_status
                }
            }
        ]
    }

    return Attachment(content_type="application/vnd.microsoft.card.adaptive", content=card_json)
