import hmac
import logging
import re
from datetime import datetime, timezone
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from mr_guardian.core.config import settings
from mr_guardian.gitlab.client import GitLabAPIError, GitLabClient
from mr_guardian.review.engine import ReviewEngine
from mr_guardian.review.report_generator import ReportGenerator
from mr_guardian.review.schemas import ReviewResult

logger = logging.getLogger(__name__)

app = FastAPI(
    title="MR Guardian",
    description="AI-Powered GitLab Merge Request Review System",
    version="0.1.0",
)

class CodeReviewRequest(BaseModel):
    code: str = Field(min_length=1)
    file_path: str = "unknown"

review_engine = ReviewEngine()
report_generator = ReportGenerator()


def _added_lines_from_diff(diff: str) -> set[int]:
    added_lines = set()
    new_line_number = None

    for line in diff.splitlines():
        if line.startswith("@@"):
            match = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
            new_line_number = int(match.group(1)) if match else None
            continue

        if new_line_number is None or line.startswith("\\"):
            continue

        if line.startswith("+"):
            added_lines.add(new_line_number)
            new_line_number += 1
        elif line.startswith("-"):
            continue
        elif line.startswith(" "):
            new_line_number += 1

    return added_lines

async def process_gitlab_merge_request(
    project_id: str,
    merge_request_iid: int,
):
    """Fetch and review every supported file in a GitLab MR."""

    print(f"[MR GUARDIAN] Starting review for MR !{merge_request_iid}")
    gitlab = GitLabClient(
        access_token=settings.gitlab_access_token,
        api_url=settings.gitlab_api_url,
    )

    try:
        mr = await gitlab.get_merge_request(
            project_id,
            merge_request_iid,
        )

        print(f"[MR GUARDIAN] MR fetched: {mr.get('title')}")

        diffs = await gitlab.get_merge_request_diffs(
            project_id,
            merge_request_iid,
        )
        diff_refs = mr.get("diff_refs") or {}
        reviews = []

        print(f"[MR GUARDIAN] Files changed: {len(diffs)}")

        for item in diffs:
            file_path = item.get("new_path") or item.get("old_path")

            if not file_path or item.get("deleted_file"):
                continue

            try:
                print(f"[MR GUARDIAN] Reviewing file: {file_path}")
                code = await gitlab.get_repository_file(
                    project_id=project_id,
                    file_path=file_path,
                    ref=mr["source_branch"],
                )
                result = await review_engine.review_code(
                    code=code,
                    file_path=file_path,
                )

                added_lines = _added_lines_from_diff(item.get("diff", ""))
                for finding in result.findings:
                    line_number = finding.line_number
                    if not line_number or line_number not in added_lines:
                        continue

                    if not all(
                        diff_refs.get(key)
                        for key in ("base_sha", "start_sha", "head_sha")
                    ):
                        logger.warning(
                            "Cannot create inline comment for %s:%s in MR !%s: "
                            "GitLab diff references are unavailable.",
                            file_path,
                            line_number,
                            merge_request_iid,
                        )
                        continue

                    position = {
                        "position_type": "text",
                        "base_sha": diff_refs["base_sha"],
                        "start_sha": diff_refs["start_sha"],
                        "head_sha": diff_refs["head_sha"],
                        "old_path": item.get("old_path") or file_path,
                        "new_path": item.get("new_path") or file_path,
                        "new_line": line_number,
                    }
                    comment = (
                        f"**[{finding.severity.upper()}] {finding.title}**\n\n"
                        f"{finding.description}\n\n"
                        f"**Recommendation:** {finding.recommendation}"
                    )

                    try:
                        await gitlab.create_merge_request_discussion(
                            project_id=project_id,
                            merge_request_iid=merge_request_iid,
                            body=comment,
                            position=position,
                        )
                        logger.info(
                            "Posted inline comment for MR !%s at %s:%s",
                            merge_request_iid,
                            file_path,
                            line_number,
                        )
                    except GitLabAPIError as error:
                        logger.warning(
                            "Could not post inline comment for MR !%s at %s:%s: %s",
                            merge_request_iid,
                            file_path,
                            line_number,
                            error.message,
                        )

                reviews.append(
                    {
                        "file_path": file_path,
                        "result": result,
                    }
                )

                print(f"[MR GUARDIAN] Review completed: {file_path}")
                print(f"[MR GUARDIAN] Risk: {result.overall_risk}")
                print(f"[MR GUARDIAN] Findings: {len(result.findings)}")
                logger.info(
                    "Reviewed MR !%s file %s: %s",
                    merge_request_iid,
                    file_path,
                    result.review_status,
                )

            except (GitLabAPIError, UnicodeDecodeError) as error:
                logger.warning(
                    "Could not review %s in MR !%s: %s",
                    file_path,
                    merge_request_iid,
                    error,
                )

        if reviews:
            report_lines = [
                "## 🤖 MR Guardian - AI Code Review",
                "",
                f"**Merge Request:** !{merge_request_iid}",
                f"**Files reviewed:** {len(reviews)}",
                "",
            ]

            for review in reviews:
                result = review["result"]
                report_lines.extend(
                    [
                        f"### File: `{review['file_path']}`",
                        "",
                        f"**Risk:** {result.overall_risk.upper()}",
                        f"**Status:** {result.review_status}",
                        "",
                        result.summary,
                        "",
                    ]
                )

                if result.findings:
                    report_lines.append("#### Findings")

                    for finding in result.findings:
                        report_lines.extend(
                            [
                                f"- **[{finding.severity.upper()}] {finding.title}**",
                                f"  - Category: {finding.category}",
                                f"  - Description: {finding.description}",
                                f"  - Recommendation: {finding.recommendation}",
                                "",
                            ]
                        )
                else:
                    report_lines.extend(
                        [
                            "No issues found in this file.",
                            "",
                        ]
                    )

            report_body = "\n".join(report_lines)
            note = await gitlab.create_merge_request_note(
                project_id=project_id,
                merge_request_iid=merge_request_iid,
                body=report_body,
            )
            print(
                f"[MR GUARDIAN] Review published to GitLab. Note ID: {note.get('id')}"
            )

    except Exception:
        logger.exception(
            "Automatic review failed for MR !%s",
            merge_request_iid,
        )


@app.get("/")
def home():
    return {
        "application": "MR Guardian",
        "message": "Welcome to MR Guardian",
        "status": "Running",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "application": "MR Guardian",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/review", response_model=ReviewResult)
async def review_code(request: CodeReviewRequest):

    try:
        result = await review_engine.review_code(
            code=request.code,
            file_path=request.file_path,
        )

        return result

    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=f"Code review failed: {error!s}",
        ) from error


@app.post("/review/report", response_class=PlainTextResponse)
async def review_code_report(request: CodeReviewRequest):

    try:
        result = await review_engine.review_code(
            code=request.code,
            file_path=request.file_path,
        )

        report = report_generator.generate_markdown(result)

        return PlainTextResponse(
            content=report,
            media_type="text/markdown",
        )

    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=f"Report generation failed: {error!s}",
        ) from error


@app.post("/gitlab/merge-requests/{merge_request_iid}/review")
async def review_gitlab_merge_request(merge_request_iid: int):

    if not settings.gitlab_access_token:
        raise HTTPException(
            status_code=503, detail="GitLab access token is not configured."
        )

    if not settings.gitlab_project_id:
        raise HTTPException(
            status_code=503, detail="GitLab project ID is not configured."
        )

    gitlab = GitLabClient(
        access_token=settings.gitlab_access_token,
        api_url=settings.gitlab_api_url,
    )

    try:
        mr = await gitlab.get_merge_request(
            settings.gitlab_project_id,
            merge_request_iid,
        )

        diffs = await gitlab.get_merge_request_diffs(
            settings.gitlab_project_id,
            merge_request_iid,
        )

        reviews = []
        skipped_files = []

        for item in diffs:
            file_path = item.get("new_path") or item.get("old_path")

            if not file_path:
                continue

            if item.get("deleted_file"):
                skipped_files.append(
                    {
                        "file_path": file_path,
                        "reason": "File was deleted.",
                    }
                )
                continue

            if item.get("collapsed") or item.get("too_large"):
                skipped_files.append(
                    {
                        "file_path": file_path,
                        "reason": "GitLab did not provide a complete diff.",
                    }
                )

            try:
                code = await gitlab.get_repository_file(
                    project_id=settings.gitlab_project_id,
                    file_path=file_path,
                    ref=mr["source_branch"],
                )

                result = await review_engine.review_code(
                    code=code,
                    file_path=file_path,
                )

                reviews.append(
                    {
                        "file_path": file_path,
                        "review": result.model_dump(),
                    }
                )

            except GitLabAPIError as error:
                if error.status_code in (404, 413):
                    skipped_files.append(
                        {
                            "file_path": file_path,
                            "reason": error.message,
                        }
                    )
                    continue

                raise

        return {
            "merge_request": {
                "iid": mr.get("iid"),
                "title": mr.get("title"),
                "state": mr.get("state"),
                "source_branch": mr.get("source_branch"),
                "target_branch": mr.get("target_branch"),
                "web_url": mr.get("web_url"),
            },
            "files_changed": len(diffs),
            "files_reviewed": len(reviews),
            "files_skipped": skipped_files,
            "reviews": reviews,
        }

    except GitLabAPIError as error:
        status_code = 404 if error.status_code == 404 else 502

        raise HTTPException(
            status_code=status_code,
            detail=error.message,
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=f"GitLab Merge Request review failed: {error!s}",
        ) from error


@app.post("/webhooks/gitlab")
async def gitlab_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
):
    if not settings.gitlab_webhook_secret:
        raise HTTPException(
            status_code=503,
            detail="GitLab webhook secret is not configured.",
        )

    if not settings.gitlab_access_token or not settings.gitlab_project_id:
        raise HTTPException(
            status_code=503,
            detail="GitLab integration is not configured.",
        )

    received_token = request.headers.get("X-Gitlab-Token", "")

    if not hmac.compare_digest(
        received_token,
        settings.gitlab_webhook_secret,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid webhook secret.",
        )

    event_type = request.headers.get("X-Gitlab-Event", "")

    if event_type != "Merge Request Hook":
        return {"status": "ignored", "reason": "Not a merge request event."}

    payload = await request.json()

    project = payload.get("project", {})
    attributes = payload.get("object_attributes", {})

    if str(project.get("id")) != str(settings.gitlab_project_id):
        raise HTTPException(
            status_code=403,
            detail="Webhook project does not match configured project.",
        )

    action = attributes.get("action")
    merge_request_iid = attributes.get("iid")

    if action not in {"open", "update", "reopen"}:
        return {
            "status": "ignored",
            "reason": f"MR action '{action}' does not trigger a review.",
        }

    if not merge_request_iid:
        raise HTTPException(
            status_code=400,
            detail="Merge Request IID is missing.",
        )

    background_tasks.add_task(
        process_gitlab_merge_request,
        str(settings.gitlab_project_id),
        int(merge_request_iid),
    )

    return {
        "status": "accepted",
        "message": "MR review queued.",
        "merge_request_iid": merge_request_iid,
        "action": action,
    }
