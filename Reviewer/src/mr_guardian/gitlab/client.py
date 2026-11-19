import base64
import httpx
from urllib.parse import quote
import base64

class GitLabAPIError(Exception):

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(message)

class GitLabClient:

    def __init__(
        self,
        access_token: str,
        api_url: str = "https://gitlab.com/api/v4",
        timeout: float = 20.0
    ):

        if not access_token:
            raise ValueError("GitLab access token is missing.")

        self.api_url = api_url.rstrip("/")
        self.timeout = timeout

        self.headers = {
            "PRIVATE-TOKEN": access_token,
            "Accept": "application/json",
        }

    async def _request(self,
    method: str,
    endpoint: str,
    json_data: dict | None = None,
    ):

        url = f"{self.api_url}/{endpoint.lstrip('/')}"

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
            ) as client:

                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=json_data,
                )

                if response.is_error:
                    raise GitLabAPIError(
                        response.status_code,
                        f"GitLab API request failed: HTTP {response.status_code}"
                    )

                return response.json()

        except httpx.TimeoutException as exc:
            raise GitLabAPIError(
                0, "GitLab API request timed out."
            ) from exc

        except httpx.RequestError as exc:
            raise GitLabAPIError(
                0, "Unable to connect to GitLab."
            ) from exc

    async def get_current_user(self):
        return await self._request("GET", "/user")

    async def get_project(self, project_id: str | int):

        encoded_id = quote(str(project_id), safe="")

        return await self._request(
            "GET",
            f"/projects/{encoded_id}",
        )

    async def get_project_merge_requests(
        self,
        project_id: str | int,
        state: str = "opened",
    ):

        encoded_id = quote(str(project_id), safe="")

        return await self._request(
            "GET",
            f"/projects/{encoded_id}/merge_requests"
            f"?state={quote(state, safe='')}",
        )

    async def get_merge_request(
        self,
        project_id: str | int,
        merge_request_iid: int,
    ):

        encoded_id = quote(str(project_id), safe="")

        return await self._request(
            "GET",
            f"/projects/{encoded_id}/merge_requests/{merge_request_iid}",
        )

    async def get_merge_request_diffs(
        self,
        project_id: str | int,
        merge_request_iid: int,
    ):

        encoded_id = quote(str(project_id), safe="")

        all_diffs = []
        page = 1
        per_page = 100

        while True:

            endpoint = (
                f"/projects/{encoded_id}/merge_requests/"
                f"{merge_request_iid}/diffs"
                f"?page={page}&per_page={per_page}&unidiff=true"
            )

            diffs = await self._request("GET", endpoint)

            if not diffs:
                break

            all_diffs.extend(diffs)

            if len(diffs) < per_page:
                break

            page += 1

        return all_diffs

    async def get_repository_file(
        self,
        project_id: str | int,
        file_path: str,
        ref: str,
    ):
        """Retrieve and decode a file from a repository branch."""

        encoded_id = quote(str(project_id), safe="")
        encoded_path = quote(file_path, safe="")
        encoded_ref = quote(ref, safe="")

        file_data = await self._request(
            "GET",
            f"/projects/{encoded_id}/repository/files/"
            f"{encoded_path}?ref={encoded_ref}",
        )

        try:
            content = base64.b64decode(
                file_data["content"]
            )

            return content.decode("utf-8")

        except (KeyError, ValueError, UnicodeDecodeError) as exc:
            raise GitLabAPIError(
                0,
                f"Unable to decode text file: {file_path}",
            ) from exc

    async def get_repository_file(
    self,
    project_id: str | int,
    file_path: str,
    ref: str,
):
        encoded_id = quote(str(project_id), safe="")
        encoded_path = quote(file_path, safe="")
        encoded_ref = quote(ref, safe="")

        file_data = await self._request(
            "GET",
            f"/projects/{encoded_id}/repository/files/"
            f"{encoded_path}?ref={encoded_ref}",
        )

        try:
            return base64.b64decode(
                file_data["content"]
            ).decode("utf-8")

        except (KeyError, ValueError, UnicodeDecodeError) as error:
            raise GitLabAPIError(
                0,
                f"Unable to decode repository file: {file_path}",
            ) from error
    async def create_merge_request_note(
    self,
    project_id: str | int,
    merge_request_iid: int,
    body: str,
    ):
        encoded_id = quote(str(project_id), safe="")

        return await self._request(
            "POST",
            f"/projects/{encoded_id}/merge_requests/"
            f"{merge_request_iid}/notes",
            json_data={"body": body},
        )

    async def create_merge_request_discussion(
        self,
        project_id: str | int,
        merge_request_iid: int,
        body: str,
        position: dict[str, str | int],
    ):
        encoded_id = quote(str(project_id), safe="")

        return await self._request(
            "POST",
            f"/projects/{encoded_id}/merge_requests/"
            f"{merge_request_iid}/discussions",
            json_data={
                "body": body,
                "position": position,
            },
        )