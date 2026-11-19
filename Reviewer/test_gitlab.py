import asyncio
from pathlib import Path
from dotenv import dotenv_values

from mr_guardian.gitlab.client import (
    GitLabClient,
    GitLabAPIError,
)

config = dotenv_values(Path(__file__).resolve().parent / ".env")

async def main():
    token = config.get("GITLAB_ACCESS_TOKEN")
    project_id = config.get("GITLAB_PROJECT_ID")
    mr_iid = 1

    if not token or not project_id:
        print("Missing GitLab configuration.")
        return

    gitlab = GitLabClient(
        access_token=token.strip(),
        api_url=config.get(
            "GITLAB_API_URL",
            "https://gitlab.com/api/v4",
        ).strip(),
    )

    try:
        print("\nFetching Merge Request...")

        mr = await gitlab.get_merge_request(
            project_id,
            mr_iid,
        )

        print("\n[PASS] Merge Request retrieved")
        print("Title:", mr.get("title"))
        print("State:", mr.get("state"))
        print("Source:", mr.get("source_branch"))
        print("Target:", mr.get("target_branch"))
        print("Author:", mr.get("author", {}).get("username"))

        print("\nFetching code diffs...")

        diffs = await gitlab.get_merge_request_diffs(
            project_id,
            mr_iid,
        )

        print("\n[PASS] Diff retrieval completed")
        print("Changed files:", len(diffs))

        for item in diffs:
            print("\n" + "=" * 50)
            print("File:", item.get("new_path"))
            print("New file:", item.get("new_file"))
            print("Deleted:", item.get("deleted_file"))
            print("Diff:")
            print(item.get("diff", "[No diff available]"))

            if item.get("collapsed"):
                print("[WARNING] Diff is collapsed by GitLab.")

            if item.get("too_large"):
                print("[WARNING] Diff is too large to retrieve.")

    except GitLabAPIError as exc:
        print("\n[FAIL]", exc.message)
        print("HTTP status:", exc.status_code)

    except Exception as exc:
        print("\n[ERROR]", type(exc).__name__, repr(exc))

if __name__ == "__main__":
    asyncio.run(main())