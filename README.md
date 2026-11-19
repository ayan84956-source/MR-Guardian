# MR-Guardian

MR-Guardian is an AI-assisted GitLab merge request reviewer. It fetches changed files from a GitLab project, analyzes the code with an Ollama model, and reports potential bugs, security concerns, and code-quality issues. Reviews can be requested through the API or triggered automatically by GitLab merge request webhooks.

## Features

- Analyze code snippets or complete GitLab merge requests.
- Return structured review results or Markdown reports.
- On webhook-triggered reviews, post findings on added lines as inline discussions and publish a summary note to the merge request.
- Expose health and service status endpoints.
- Use Ruff and Bandit as part of the project's development toolset.

## Requirements

- Python 3.10 or newer
- [Ollama](https://ollama.com/) running locally or at a reachable URL
- A GitLab access token and project ID for GitLab integration

The default model is `qwen2.5-coder:latest`. Make sure the model is available to your Ollama instance before starting the service.

## Setup

The application lives in the `Reviewer` directory. From the repository root:

```bash
cd Reviewer
python -m venv .venv
```

Activate the virtual environment, then install dependencies:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

python -m pip install -r requirements.txt
```

Pull the default Ollama model if you do not already have it:

```bash
ollama pull qwen2.5-coder:latest
```

Create a `.env` file in `Reviewer/` for the settings you need. For example:

```dotenv
# Ollama (these are the defaults)
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5-coder:latest

# Required for GitLab merge request reviews and webhooks
GITLAB_ACCESS_TOKEN=your-gitlab-access-token
GITLAB_PROJECT_ID=your-gitlab-project-id
GITLAB_WEBHOOK_SECRET=replace-with-a-long-random-secret

# Optional; defaults to GitLab.com
GITLAB_API_URL=https://gitlab.com/api/v4
```

Keep `.env` and all access tokens and webhook secrets private; do not commit real credentials.

## Run the API

From the `Reviewer/` directory, with the virtual environment activated:

```bash
PYTHONPATH=src uvicorn mr_guardian.api.main:app --reload
```

On Windows PowerShell, set the source path before starting Uvicorn:

```powershell
$env:PYTHONPATH = "src"
uvicorn mr_guardian.api.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`. Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

## API endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Service welcome and status |
| `GET` | `/health` | Health check |
| `POST` | `/review` | Review code and return structured results |
| `POST` | `/review/report` | Review code and return a Markdown report |
| `POST` | `/gitlab/merge-requests/{merge_request_iid}/review` | Review a merge request in the configured GitLab project |
| `POST` | `/webhooks/gitlab` | Receive GitLab merge request webhook events |

Example request to review a code snippet:

```bash
curl -X POST http://127.0.0.1:8000/review \
  -H 'Content-Type: application/json' \
  -d '{"file_path":"example.py","code":"print(\"Hello, world!\")"}'
```

For the GitLab review endpoint, configure `GITLAB_ACCESS_TOKEN` and `GITLAB_PROJECT_ID` first. The webhook endpoint accepts GitLab merge request events for the configured project and queues reviews for opened, updated, or reopened merge requests.

## GitLab webhook setup

In your GitLab project, add a webhook pointing to:

```text
https://<your-service-host>/webhooks/gitlab
```

Enable **Merge request events** and set the webhook secret to the same value as `GITLAB_WEBHOOK_SECRET`. The application validates the secret and configured project ID before queuing a review.

For local testing with a Cloudflare Quick Tunnel on Windows, see [`Reviewer/CLOUDFLARE.md`](Reviewer/CLOUDFLARE.md). Quick Tunnels create temporary public URLs and are intended only for development/testing. **The API's review endpoints do not require authentication. Do not expose this service publicly or use it with sensitive or production workloads without putting appropriate authentication and access controls in front of it.**

## Project layout

```text
Reviewer/
├── requirements.txt
├── run_cloudflare_tunnel.ps1
└── src/mr_guardian/
    ├── analyzers/
    ├── api/
    ├── core/
    ├── gitlab/
    ├── llm/
    └── review/
```

## License

No license has been specified for this repository yet.
