from collections import Counter
from mr_guardian.review.schemas import (
    ReviewFinding,
    ReviewResult
)

class FindingManager:

    SEVERITY_ORDER = {
        "critical": 4,
        "high": 3,
        "medium": 2,
        "low": 1
    }

    def normalize_severity(self, severity: str) -> str:

        severity = severity.lower()

        if severity not in self.SEVERITY_ORDER:
            return "low"

        return severity

    def get_issue_group(self, finding: ReviewFinding) -> str:

        text = (
            finding.title + " " + finding.description
        ).lower()

        if (
            "sql" in text
            and (
                "injection" in text
                or "b608" in text
                or "hardcoded_sql_expressions" in text
            )
        ):
            return "sql_injection"

        return finding.title.lower().strip()

    def deduplicate(
        self,
        findings: list[ReviewFinding]
    ) -> list[ReviewFinding]:

        unique = []

        for finding in findings:

            duplicate_index = None
            issue_group = self.get_issue_group(finding)

            for index, existing in enumerate(unique):

                same_file = (
                    existing.file_path == finding.file_path
                )

                same_group = (
                    self.get_issue_group(existing) == issue_group
                )

                line_difference = (
                    abs(existing.line_number - finding.line_number)
                    if existing.line_number is not None
                    and finding.line_number is not None
                    else 0
                )

                if (
                    same_file
                    and same_group
                    and line_difference <= 2
                ):
                    duplicate_index = index
                    break

            if duplicate_index is None:
                unique.append(finding)

            else:
                existing = unique[duplicate_index]

                if (
                    self.SEVERITY_ORDER[finding.severity]
                    > self.SEVERITY_ORDER[existing.severity]
                ):
                    unique[duplicate_index] = finding

        return unique

    def calculate_risk(self, findings: list[ReviewFinding]) -> str:

        if not findings:
            return "none"

        return max(
            findings,
            key=lambda item: self.SEVERITY_ORDER[item.severity]
        ).severity

    def get_statistics(
        self,
        findings: list[ReviewFinding]
    ) -> dict:

        severity_counts = Counter(
            finding.severity for finding in findings
        )

        source_counts = Counter(
            finding.source for finding in findings
        )

        category_counts = Counter(
            finding.category for finding in findings
        )

        return {
            "total_findings": len(findings),
            "critical": severity_counts["critical"],
            "high": severity_counts["high"],
            "medium": severity_counts["medium"],
            "low": severity_counts["low"],
            "ai_findings": source_counts["ai"],
            "ruff_findings": source_counts["ruff"],
            "bandit_findings": source_counts["bandit"],
            "security_issues": category_counts["security"],
            "code_quality_issues": (
                category_counts["best_practice"]
                + category_counts["maintainability"]
            )
        }

    def process(
        self,
        findings: list[ReviewFinding]
    ) -> dict:

        unique_findings = self.deduplicate(findings)

        risk = self.calculate_risk(unique_findings)

        if risk in ("critical", "high"):
            status = "action_required"
        elif risk == "medium":
            status = "review_recommended"
        else:
            status = "passed"

        return {
            "findings": unique_findings,
            "overall_risk": risk,
            "review_status": status,
            "statistics": self.get_statistics(unique_findings)
        }