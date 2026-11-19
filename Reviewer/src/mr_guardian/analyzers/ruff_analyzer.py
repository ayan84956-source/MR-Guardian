import json
import subprocess
import sys

class RuffAnalyzer:

    def analyze(self, file_path: str) -> list[dict]:

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "ruff",
                "check",
                file_path,
                "--output-format=json"
            ],
            capture_output=True,
            text=True
        )

        if result.returncode not in (0, 1):
            raise RuntimeError(
                f"Ruff execution failed: {result.stderr}"
            )

        findings = json.loads(result.stdout or "[]")

        return [
            {
                "tool": "ruff",
                "severity": "low",
                "category": "best_practice",
                "title": item.get("message", "Code quality issue"),
                "description": item.get("message", ""),
                "file_path": item.get("filename"),
                "line_number": item.get("location", {}).get("row"),
                "recommendation": (
                    f"Review Ruff rule {item.get('code')}."
                )
            }
            for item in findings
        ]