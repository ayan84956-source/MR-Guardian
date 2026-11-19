# Cloudflare Tunnel

This project can be exposed for testing through a Cloudflare Quick Tunnel. The tunnel
connects to Uvicorn on `127.0.0.1:8000`; the API does not need to listen on a public
interface or have an inbound firewall port opened.

## Start a temporary tunnel on Windows

1. Install [cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/)
   (or run `winget install --id Cloudflare.cloudflared` in PowerShell).
2. Ensure the project virtual environment exists and dependencies are installed:

   ```powershell
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

3. Configure the GitLab values required by the app in the ignored `.env` file,
   including `GITLAB_ACCESS_TOKEN`, `GITLAB_PROJECT_ID`, and
   `GITLAB_WEBHOOK_SECRET`.
4. Run from the project directory:

   ```powershell
   .\run_cloudflare_tunnel.ps1
   ```

   If PowerShell blocks the script, allow it for the current terminal only:

   ```powershell
   Set-ExecutionPolicy -Scope Process Bypass
   .\run_cloudflare_tunnel.ps1
   ```

The script starts Uvicorn bound to localhost, waits for `/health`, and then starts
`cloudflared`. Keep the terminal open. Stop with Ctrl+C; the script stops the local
API as well. Quick Tunnel URLs are temporary and change each time the tunnel starts.

## Configure the GitLab webhook

Copy the `https://...trycloudflare.com` URL printed by `cloudflared`, then set the
GitLab webhook URL to:

```text
https://...trycloudflare.com/webhooks/gitlab
```

In GitLab, enable **Merge request events** and set the webhook secret to exactly the
same value as `GITLAB_WEBHOOK_SECRET` in `.env`. Use GitLab's **Test** action while
the tunnel is running. When an MR is reviewed, findings located on added lines are
posted as inline discussions; the complete review is also posted as a summary note.

## Security and production

Quick Tunnels are for development/testing, not a stable production endpoint. This
application's review routes do not require authentication, so anyone who obtains the
temporary URL can call them. Do not use a Quick Tunnel with sensitive or production
workloads.

For a stable hostname, create a named Tunnel in the Cloudflare dashboard and route
your DNS hostname to the local service at `http://127.0.0.1:8000`. Configure and
test Cloudflare Access or equivalent authentication before exposing review routes,
and use the stable hostname in GitLab's webhook URL. Named Tunnel credentials and
webhook secrets belong in local secret storage; do not commit them to the project.
