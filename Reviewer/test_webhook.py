import httpx
from mr_guardian.core.config import settings

url = "https://ethics-evaluated-bone-declare.trycloudflare.com/webhooks/gitlab"

payload = {
    "object_kind": "merge_request",
    "event_type": "merge_request",
    "project": {
        "id": int(settings.gitlab_project_id)
    },
    "object_attributes": {
        "iid": 1,
        "action": "open",
        "state": "opened"
    }
}

headers = {
    "X-Gitlab-Token": settings.gitlab_webhook_secret,
    "X-Gitlab-Event": "Merge Request Hook",
}

response = httpx.post(
    url,
    json=payload,
    headers=headers,
    timeout=30
)

print("Status:", response.status_code)
print("Response:", response.json())
