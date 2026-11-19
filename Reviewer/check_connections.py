import asyncio
from pathlib import Path
from dotenv import dotenv_values

from mr_guardian.gitlab.client import (
    GitLabClient,
    GitLabAPIError,
)

ENV_FILE = Path(__file__).resolve().parent / ".env"
config = dotenv_values(ENV_FILE)

async def main():
    token = config.get("GITLAB_ACCESS_TOKEN")
    project_id = config.get("GITLAB_PROJECT_ID")
    api_url = config.get(
        "GITLAB_API_URL",
        "https://gitlab.com/api/v4",
    )

    if not token:
        print("[FAIL] GitLab token not found.")
        return

    if not project_id:
        print("[FAIL] GitLab project ID not found.")
        return

    gitlab = GitLabClient(
        access_token=token.strip(),
        api_url=api_url.strip(),
    )

    # Test 1: Authentication
    try:
        print("\nTEST 1: GitLab authentication...")
        user = await gitlab.get_current_user()

        print("[PASS] Authentication successful!")
        print("Username:", user.get("username"))

    except GitLabAPIError as exc:
        print("[FAIL] Authentication failed:", exc.message)
        print("HTTP:", exc.status_code)
        return

    # Test 2: Project retrieval
    try:
        print("\nTEST 2: Project retrieval...")
        project = await gitlab.get_project(project_id.strip())

        print("[PASS] Project retrieved!")
        print("Project:", project.get("name"))
        print("Project ID:", project.get("id"))

    except GitLabAPIError as exc:
        print("[FAIL] Project retrieval failed:", exc.message)
        print("HTTP:", exc.status_code)
        return

    # Test 3: Merge Request retrieval
    try:
        print("\nTEST 3: Merge Request retrieval...")
        merge_requests = await gitlab.get_project_merge_requests(
            project_id.strip()
        )

        print("[PASS] Merge Requests retrieved!")
        print("Open Merge Requests:", len(merge_requests))

    except GitLabAPIError as exc:
        print("[FAIL] Merge Request retrieval failed:", exc.message)
        print("HTTP:", exc.status_code)


if __name__ == "__main__":
    asyncio.run(main())