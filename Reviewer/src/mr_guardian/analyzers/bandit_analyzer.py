import json
import subprocess
import sys

class BanditAnalyzer:

    def analyze(self, file_path: str) -> list[dict]:

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "bandit",
                "-f",
                "json",
                file_path
            ],
            capture_output=True,
            text=True
        )

        if result.returncode not in (0, 1):
            raise RuntimeError(
                f"Bandit execution failed: {result.stderr}"
            )

        report = json.loads(result.stdout or "{}")

        findings = report.get("results", [])

        return [
            {
                "tool": "bandit",
                "severity": item.get(
                    "issue_severity", "LOW"
                ).lower(),
                "category": "security",
                "title": item.get("test_name", "Security issue"),
                "description": item.get("issue_text", ""),
                "file_path": item.get("filename"),
                "line_number": item.get("line_number"),
                "recommendation": (
                    f"Review and resolve Bandit rule "
                    f"{item.get('test_id')}."
                )
            }
            for item in findings
        ]