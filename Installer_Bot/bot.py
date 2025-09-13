from botbuilder.core import ActivityHandler, TurnContext, MessageFactory
from botbuilder.schema import ChannelAccount, ActivityTypes
from intent_parser import parse_intent
from llm import get_llm_response, get_cs_it_response
from db_connector import (
    fetch_all_software,
    fetch_software_by_names,
    get_software_info,
    search_software_fuzzy,
    log_software_request,
    log_feedback  # Add this
)
from card_builder import (
    build_software_card,
    build_software_selection_card,
    build_admin_approval_card,
    build_feedback_card  # Add this
)
import os
import asyncio
import sys
import json
import httpx
from groq import Groq
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List
from rundeck import run_rundeck_job, check_job_status

load_dotenv()
SN_INSTANCE = os.getenv("SN_INSTANCE", "").rstrip("/")
SN_USER = os.getenv("SN_USER")
SN_PASS = os.getenv("SN_PASS")

class MyBot(ActivityHandler):
    def __init__(self):
        super().__init__()
        self.is_admin_mode = False  # Track if bot is in admin mode
        self.pending_approval = {}  # Store pending approval data

    async def on_message_activity(self, turn_context: TurnContext):
        # Handle card submissions
        if turn_context.activity.value:
            await self._handle_card_submission(turn_context)
            return
           
        user_msg = turn_context.activity.text or ""
        parsed = parse_intent(user_msg)

        if parsed["intent"] == "install":
            await self._handle_install_intent(turn_context, parsed, user_msg)
        elif parsed["intent"] == "cs_it":
            await self._handle_cs_it_intent(turn_context, user_msg)
        else:
            await self._handle_general_intent(turn_context, user_msg)

    async def _handle_install_intent(self, turn_context: TurnContext, parsed: dict, user_msg: str):
        """Handle software installation requests"""
        apps = parsed["apps"]

        if not apps:  
            catalog = fetch_all_software()
            if not catalog:
                await turn_context.send_activity("⚠️ Sorry, no software available in the catalog.")
                return
           
            await turn_context.send_activity("I can help you install software! Here's what's available:")
            selection_card = build_software_selection_card(catalog)
            await turn_context.send_activity(MessageFactory.attachment(selection_card))
           
        elif len(apps) == 1:
            catalog = fetch_software_by_names(apps)
            if not catalog:
                catalog = search_software_fuzzy(apps[0])
            if not catalog:
                await turn_context.send_activity(
                    f"⚠️ Sorry, I couldn't find '{apps[0]}' in our software catalog. "
                    "Try asking 'install software' to see what's available."
                )
                return

            for app, versions in catalog.items():
                await turn_context.send_activity(f"Great! I found {app.title()} for you:")
                card = build_software_card(app, versions)
                await turn_context.send_activity(MessageFactory.attachment(card))
               
        else:
            catalog = fetch_software_by_names(apps)
            if not catalog:
                await turn_context.send_activity(
                    "⚠️ Sorry, I couldn't find any of the requested software in the catalog."
                )
                return

            found_apps = list(catalog.keys())
            missing_apps = [app for app in apps if app not in found_apps]
           
            if missing_apps:
                await turn_context.send_activity(
                    f"⚠️ I couldn't find: {', '.join(missing_apps)}. "
                    f"But I found these software options for you:"
                )
            else:
                await turn_context.send_activity("Great! I found all the software you requested:")

            for app, versions in catalog.items():
                card = build_software_card(app, versions)
                await turn_context.send_activity(MessageFactory.attachment(card))

    async def _handle_cs_it_intent(self, turn_context: TurnContext, user_msg: str):
        """Handle CS/IT related queries"""
        await turn_context.send_activity("🤖 Let me help you with that technical question...")
        reply = get_cs_it_response(user_msg)
        await turn_context.send_activity(reply)

    async def _handle_general_intent(self, turn_context: TurnContext, user_msg: str):
        """Handle general conversation"""
        reply = get_llm_response(user_msg)
        await turn_context.send_activity(reply)

    # ----------------- FIXED METHODS -----------------
    @staticmethod
    async def extract_incident_data(user_input: str) -> Dict[str, Any]:
        """Extract structured JSON incident data from user input safely."""
        def create_messages(system_msg: str, user_msg: str) -> List[Dict[str, str]]:
            return [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ]
       
        incident_extraction_system_msg = """You are a ServiceNow incident creation assistant.
        Return ONLY a JSON object with the following fields:
        {
        "short_description": "...",
        "description": "...",
        "category": "...",
        "caller": "Guest"
        }"""
       
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        model = os.getenv("GROQ_MODEL", "llama3-8b-8192")
       
        prompt = f"Analyze this user input and extract incident information in JSON format: \"{user_input}\""
        messages = create_messages(incident_extraction_system_msg, prompt)
       
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.1,
            max_tokens=500
        )
       
        response_content = completion.choices[0].message.content.strip()
        print(f"DEBUG - Raw LLM response: {response_content}")
       
        # Try parsing JSON safely
        try:
            return json.loads(response_content)
        except json.JSONDecodeError:
            print("⚠️ LLM response was not valid JSON, falling back to default incident data.")
            return {
                "short_description": user_input,
                "description": user_input,
                "category": "Software",
                "caller": "Guest"
            }

    @staticmethod
    async def create_incident_direct(incident_data: Dict[str, Any]) -> Optional[Dict]:
        """Create an incident directly in ServiceNow via REST API."""
        try:
            print("🔥 Creating incident via ServiceNow API...")
            url = f"{SN_INSTANCE}/api/now/table/incident"
            headers = {"Content-Type": "application/json", "Accept": "application/json"}

            if not incident_data.get("caller"):
                incident_data["caller"] = "Guest"

            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=incident_data, auth=(SN_USER, SN_PASS))
            response.raise_for_status()
            print("✅ Incident created successfully!")
            return response.json()
        except Exception as e:
            print(f"❌ Error creating incident: {e}")
            return None

    @staticmethod
    async def update_incident_state_sn(incident_number: str, new_state: str) -> Optional[Dict]:
        """Update incident state in ServiceNow"""
        try:
            print(f"🔄 Updating incident {incident_number} to state {new_state}...")
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
            
            state_map = {"new": "1", "in progress": "2", "closed": "7", "cancelled": "8"}
            mapped_state = state_map.get(new_state.lower())
            if not mapped_state:
                return {"error": f"Invalid state: {new_state}"}
            
            updates = {"state": mapped_state}
            
            async with httpx.AsyncClient() as client:
                update_resp = await client.patch(url_update, headers=headers, json=updates, auth=(SN_USER, SN_PASS))
            update_resp.raise_for_status()
            
            return {"success": True, "data": update_resp.json()}
        except Exception as e:
            print(f"❌ Error updating incident state: {e}")
            return {"error": str(e)}

    async def _handle_card_submission(self, turn_context: TurnContext):
        """Handle adaptive card submissions"""
        try:
            card_data = turn_context.activity.value
            action = card_data.get("action", "")
           
            if action == "install":
                app = card_data.get("app", "")
                version = card_data.get("version", "")
               
                if app and version:
                    await turn_context.send_activity(
                        f"🚀 Creating ServiceNow Ticket for Installation of {app.title()} version {version}..."
                    )
                   
                    software_info = get_software_info(app, version)
                    incident_description = f"Installation of {software_info['name']} v{software_info['version']}"

                    if incident_description:
                        incident_data = await self.extract_incident_data(incident_description)
                        result = await self.create_incident_direct(incident_data)
                        if result:
                            print(f"DEBUG - Full ServiceNow response: {result}")

                            # Try to extract incident number safely
                            incident_number = (
                                result.get("result", {}).get("number")
                                or result.get("number")
                                or "Unknown"
                            )

                            print(f"✅ Incident created successfully! Incident Number: {incident_number}")
                            await turn_context.send_activity(
                                f"✅ Incident created successfully! Incident Number: {incident_number}"
                            )

                            # 📝 LOG THE REQUEST
                            if incident_number != "Unknown":
                                software_name = app
                                version_name = version
                                status = "User initiated the request for the Software Installation"

                                log_success = log_software_request(
                                    incident_number,
                                    software_name,
                                    version_name,
                                    status
                                )

                                if log_success:
                                    print(f"📝 Request logged successfully for incident {incident_number}")
                                    
                                    # 🔄 SWITCH TO ADMIN MODE AND SEND APPROVAL CARD
                                    await self._switch_to_admin_mode(turn_context, {
                                        "incident_number": incident_number,
                                        "software_name": software_name,
                                        "version": version_name,
                                        "requester": "Guest"  # You can modify this to get actual user
                                    })
                                    
                                else:
                                    print(f"⚠️ Failed to log request for incident {incident_number}")
                            else:
                                print("⚠️ Cannot log request - incident number is unknown")

                        else:
                            print("❌ Failed to create incident.")
                            await turn_context.send_activity("❌ Failed to create incident.")
                else:
                    await turn_context.send_activity("⚠️ Please select a version to install.")
            
            elif action == "admin_approve":
                await self._handle_admin_approval(turn_context, card_data)
            
            elif action == "admin_reject":
                await self._handle_admin_rejection(turn_context, card_data)
            
            elif action == "submit_feedback":
                await self._handle_feedback_submission(turn_context, card_data)
            
            elif action == "skip_feedback":
                await self._handle_skip_feedback(turn_context, card_data)
                   
            elif action == "show_versions":
                selected_software = card_data.get("selected_software", [])
                print(f"DEBUG - Received card_data: {card_data}")
                print(f"DEBUG - Selected software: {selected_software}")
                print(f"DEBUG - Type: {type(selected_software)}")
               
                if not selected_software:
                    await turn_context.send_activity("⚠️ Please select at least one software to install.")
                    return
               
                software_list = []
                if isinstance(selected_software, str):
                    if "," in selected_software:
                        software_list = [s.strip() for s in selected_software.split(",")]
                    else:
                        software_list = [selected_software]
                elif isinstance(selected_software, list):
                    software_list = selected_software
                else:
                    software_list = [str(selected_software)]
               
                print(f"DEBUG - Processed software_list: {software_list}")
               
                if not software_list:
                    await turn_context.send_activity("⚠️ Please select at least one software to install.")
                    return
               
                catalog = fetch_software_by_names(software_list)
                print(f"DEBUG - Catalog found: {catalog}")
               
                if catalog:
                    found_count = len(catalog)
                    selected_count = len(software_list)
                   
                    await turn_context.send_activity(
                        f"Perfect! Found {found_count} out of {selected_count} selected software. "
                        f"Here are the installation options:"
                    )
                   
                    for app, versions in catalog.items():
                        card = build_software_card(app, versions)
                        await turn_context.send_activity(MessageFactory.attachment(card))
                       
                    found_names = [name.lower() for name in catalog.keys()]
                    missing = [name for name in software_list if name.lower() not in found_names]
                    if missing:
                        await turn_context.send_activity(f"⚠️ Couldn't find: {', '.join(missing)}")
                else:
                    await turn_context.send_activity(
                        f"⚠️ Sorry, couldn't find any of the selected software: {', '.join(software_list)}."
                    )
                   
        except Exception as e:
            print(f"Error handling card submission: {e}")
            await turn_context.send_activity(
                "⚠️ Sorry, there was an error processing your request. Please try again."
            )

    async def _switch_to_admin_mode(self, turn_context: TurnContext, approval_data: Dict[str, Any]):
        """Switch bot to admin mode and send approval card"""
        self.is_admin_mode = True
        self.pending_approval = approval_data
        
        # Send admin notification message
        await turn_context.send_activity("🔄 Switching to Admin Mode...")
        await turn_context.send_activity("👨‍💼 **ADMIN NOTIFICATION**")
        
        # Send admin approval card
        approval_card = build_admin_approval_card(approval_data)
        await turn_context.send_activity(MessageFactory.attachment(approval_card))

    async def _handle_admin_approval(self, turn_context: TurnContext, card_data: Dict[str, Any]):
        """Handle admin approval action"""
        incident_number = card_data.get("incident_number", "")
        software_name = card_data.get("software_name", "")
        version = card_data.get("version", "")

        # 1️⃣ Update ServiceNow -> In Progress
        update_result = await self.update_incident_state_sn(incident_number, "in progress")
        if update_result and update_result.get("success"):
            await turn_context.send_activity(f"✅ ServiceNow updated: Incident {incident_number} is now In Progress")
        else:
            await turn_context.send_activity(f"⚠️ Failed to update ServiceNow: {update_result}")

        await turn_context.send_activity(
            f"✅ **APPROVED by Admin**\n\n"
            f"📋 Incident: {incident_number}\n"
            f"📦 Software: {software_name} v{version}\n\n"
            f"🚀 Triggering installation in Rundeck..."
        )

        # 📝 Log admin approval BEFORE Rundeck
        log_software_request(
            incident_number,
            software_name,
            version,
            "Admin approved the software installation request"
        )

        # 2️⃣ Trigger Rundeck job
        execution_id = run_rundeck_job(software_name, version)
        if not execution_id:
            await turn_context.send_activity("❌ Failed to trigger Rundeck job. Please check configuration.")
            # Send feedback card for failed trigger
            await self._send_feedback_card(turn_context, incident_number, software_name, version, "failed")
            return

        await turn_context.send_activity(f"🔥 Rundeck Job started (Execution ID: {execution_id}). Monitoring...")

        # 3️⃣ Poll Rundeck for status
        final_status = await check_job_status(execution_id)

        # 4️⃣ Update ServiceNow & Notify based on result
        if final_status == "succeeded":
            await self.update_incident_state_sn(incident_number, "closed")
            await turn_context.send_activity(
                f"✅ Installation completed successfully via Rundeck for {software_name} {version}"
            )
            status_msg = "Rundeck job succeeded, software installed"
            installation_status = "success"
        elif final_status in ["failed", "aborted"]:
            await self.update_incident_state_sn(incident_number, "cancelled")
            await turn_context.send_activity(
                f"❌ Installation failed in Rundeck for {software_name} {version}"
            )
            status_msg = f"Rundeck job {final_status}"
            installation_status = "failed"
        else:
            await turn_context.send_activity("⚠️ Could not determine Rundeck job status.")
            status_msg = "Rundeck job error"
            installation_status = "failed"

        # 5️⃣ Log Rundeck final result
        log_software_request(incident_number, software_name, version, status_msg)

        # 6️⃣ Send feedback card to user
        await self._send_feedback_card(turn_context, incident_number, software_name, version, installation_status)

        # Reset admin mode
        self._reset_admin_mode()

    async def _handle_admin_rejection(self, turn_context: TurnContext, card_data: Dict[str, Any]):
        """Handle admin rejection action"""
        incident_number = card_data.get("incident_number", "")
        software_name = card_data.get("software_name", "")
        version = card_data.get("version", "")
        rejection_reason = card_data.get("rejection_reason", "")

        # ✅ Update incident in ServiceNow
        update_result = await self.update_incident_state_sn(incident_number, "cancelled")
        if update_result and update_result.get("success"):
            await turn_context.send_activity(f"✅ ServiceNow updated: Incident {incident_number} is now Cancelled")
        else:
            await turn_context.send_activity(f"⚠️ Failed to update ServiceNow: {update_result}")

        await turn_context.send_activity(
            f"❌ **REJECTED by Admin**\n\n"
            f"📋 Incident: {incident_number}\n"
            f"📦 Software: {software_name} v{version}\n"
            f"🚫 Reason: {rejection_reason or 'No reason provided'}\n\n"
            f"The installation request has been rejected."
        )

        # Log rejection
        status = "Admin rejected the request of Software Installation"
        log_software_request(incident_number, software_name, version, status)

        self._reset_admin_mode()

    # ✅ CORRECTED FEEDBACK METHODS - PROPERLY INDENTED AS CLASS METHODS
    async def _send_feedback_card(self, turn_context: TurnContext, incident_number: str, software_name: str, version: str, installation_status: str):
        """Send feedback card to user after installation completion"""
        await turn_context.send_activity("📝 **Please provide your feedback:**")
        
        feedback_card = build_feedback_card(incident_number, software_name, version, installation_status)
        await turn_context.send_activity(MessageFactory.attachment(feedback_card))

    async def _handle_feedback_submission(self, turn_context: TurnContext, card_data: Dict[str, Any]):
        """Handle feedback submission"""
        incident_number = card_data.get("incident_number", "")
        software_name = card_data.get("software_name", "")
        version = card_data.get("version", "")
        installation_status = card_data.get("installation_status", "")
        
        rating = card_data.get("rating", "3")
        feedback_comments = card_data.get("feedback_comments", "")

        # Log feedback to database
        feedback_logged = log_feedback(
            incident_number,
            software_name,
            version,
            rating,
            feedback_comments,
            installation_status
        )

        if feedback_logged:
            await turn_context.send_activity(
                f"🙏 Thank you for your feedback!\n\n"
                f"📋 Incident: {incident_number}\n"
                f"⭐ Rating: {rating}/5\n"
                f"📝 Your feedback has been recorded and will help us improve our service."
            )
        else:
            await turn_context.send_activity(
                "⚠️ There was an issue saving your feedback, but we appreciate you taking the time to provide it."
            )

    async def _handle_skip_feedback(self, turn_context: TurnContext, card_data: Dict[str, Any]):
        """Handle when user skips feedback"""
        incident_number = card_data.get("incident_number", "")
        
        await turn_context.send_activity(
            f"👍 Thank you! The installation process for incident {incident_number} is now complete."
        )

    def _reset_admin_mode(self):
        """Reset bot back to user mode"""
        self.is_admin_mode = False
        self.pending_approval = {}

    async def on_members_added_activity(
        self,
        members_added: ChannelAccount,
        turn_context: TurnContext
    ):
        for member_added in members_added:
            if member_added.id != turn_context.activity.recipient.id:
                welcome_message = (
                    "🤖 **Welcome to the Software Assistant Bot!**\n\n"
                    "I can help you with:\n"
                    "• 📦 **Software Installation** - Say 'install software' or 'install [app name]'\n"
                    "• 💻 **CS/IT Questions** - Ask about programming, algorithms, databases, etc.\n"
                    "• 💬 **General Chat** - Feel free to ask me anything!\n\n"
                    "Try saying something like:\n"
                    "- 'Install zoom and slack'\n"
                    "- 'What is a binary search tree?'\n"
                    "- 'Show me available software'"
                )
                await turn_context.send_activity(welcome_message)