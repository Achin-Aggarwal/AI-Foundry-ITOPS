import requests
import asyncio

RUNDECK_URL = "http://localhost:4440"
API_TOKEN = "YyqzgvF0MDXflPjtv3DFYhXd3n4rAEoO"
JOB_ID = "358fa11d-0bf1-4213-bfec-b86b0420fee2"


def run_rundeck_job(app_name, version=None):
    """Trigger a Rundeck job with user-specified application name and version."""
    url = f"{RUNDECK_URL}/api/45/job/{JOB_ID}/run"
    headers = {
        "X-Rundeck-Auth-Token": API_TOKEN,
        "Accept": "application/json"
    }

    payload = {"options": {"app": app_name}}
    if version:
        payload["options"]["version"] = version

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        data = response.json()
        return data["id"]  # Execution ID
    else:
        print("❌ Rundeck trigger failed:", response.status_code, response.text)
        return None


async def check_job_status(execution_id):
    """Poll Rundeck until job finishes. Returns final status."""
    url = f"{RUNDECK_URL}/api/45/execution/{execution_id}"
    headers = {
        "X-Rundeck-Auth-Token": API_TOKEN,
        "Accept": "application/json"
    }

    while True:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            status = response.json()["status"]
            print(f"📊 Rundeck Job Status: {status}")
            if status in ["succeeded", "failed", "aborted"]:
                return status
        else:
            return "error"
        await asyncio.sleep(5)
