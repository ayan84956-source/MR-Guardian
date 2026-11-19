from mr_guardian.review.schemas import (
    ReviewFinding,
    ReviewResult
)

from mr_guardian.review.report_generator import ReportGenerator


def main():

    findings = [

        ReviewFinding(
            severity="high",
            category="security",
            title="SQL Injection Vulnerability",
            description="User input is directly concatenated into SQL.",
            file_path="users.py",
            line_number=2,
            recommendation="Use parameterized SQL queries.",
            source="ai"
        ),

        ReviewFinding(
            severity="medium",
            category="security",
            title="Hardcoded SQL Expressions",
            description="Potential SQL injection through string construction.",
            file_path="users.py",
            line_number=2,
            recommendation="Review Bandit rule B608.",
            source="bandit"
        )
    ]

    review = ReviewResult(
        summary="The code contains a potential SQL injection vulnerability.",
        findings=findings,
        overall_risk="high",
        review_status="action_required",
        statistics={
            "total_findings": 2,
            "critical": 0,
            "high": 1,
            "medium": 1,
            "low": 0,
            "ai_findings": 1,
            "ruff_findings": 0,
            "bandit_findings": 1,
            "security_issues": 2,
            "code_quality_issues": 0
        }
    )

    generator = ReportGenerator()

    report = generator.generate_markdown(review)

    print(report)

    with open(
        "mr_guardian_report.md",
        "w",
        encoding="utf-8"
    ) as file:

        file.write(report)

    print("\nReport saved as mr_guardian_report.md")

if __name__ == "__main__":
    main()