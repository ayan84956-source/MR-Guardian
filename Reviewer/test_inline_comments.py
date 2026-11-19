import unittest

from mr_guardian.api.main import _added_lines_from_diff
from mr_guardian.gitlab.client import GitLabClient


class AddedLinesFromDiffTests(unittest.TestCase):
    def test_returns_only_added_new_file_line_numbers(self):
        diff = (
            "@@ -1,3 +1,4 @@\n"
            " context\n"
            "+added at line two\n"
            "-removed line\n"
            "+added at line three\n"
            " context\n"
        )

        self.assertEqual(_added_lines_from_diff(diff), {2, 3})

    def test_handles_multiple_hunks(self):
        diff = (
            "@@ -1,2 +1,2 @@\n"
            " first\n"
            " second\n"
            "@@ -10,2 +10,3 @@\n"
            " context\n"
            "+added\n"
            " context\n"
        )

        self.assertEqual(_added_lines_from_diff(diff), {11})


class MergeRequestDiscussionTests(unittest.IsolatedAsyncioTestCase):
    async def test_posts_discussion_with_diff_position(self):
        client = GitLabClient(access_token="test-token")
        requested = {}

        async def fake_request(method, endpoint, json_data=None):
            requested.update(
                method=method,
                endpoint=endpoint,
                json_data=json_data,
            )
            return {"id": 123}

        client._request = fake_request
        position = {
            "position_type": "text",
            "base_sha": "base",
            "start_sha": "start",
            "head_sha": "head",
            "old_path": "src/file.py",
            "new_path": "src/file.py",
            "new_line": 5,
        }

        result = await client.create_merge_request_discussion(
            project_id="group/project",
            merge_request_iid=7,
            body="Review finding",
            position=position,
        )

        self.assertEqual(result, {"id": 123})
        self.assertEqual(requested["method"], "POST")
        self.assertEqual(
            requested["endpoint"],
            "/projects/group%2Fproject/merge_requests/7/discussions",
        )
        self.assertEqual(
            requested["json_data"],
            {"body": "Review finding", "position": position},
        )


if __name__ == "__main__":
    unittest.main()
