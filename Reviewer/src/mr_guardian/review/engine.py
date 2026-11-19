import tempfile
from pathlib import Path
from mr_guardian.llm.service import LLMService
from mr_guardian.review.prompts import REVIEW_SYSTEM_PROMPT
from mr_guardian.review.schemas import (
    ReviewResult,
    ReviewFinding,
    clean_json_response
)
from mr_guardian.analyzers.engine import StaticAnalysisEngine
from mr_guardian.review.finding_manager import FindingManager

class ReviewEngine:

    def __init__(self):
        self.llm = LLMService()
        self.static_analyzer = StaticAnalysisEngine()
        self.finding_manager = FindingManager()

    async def review_code(
        self,
        code: str,
        file_path: str = "unknown"
    ) -> ReviewResult:

        prompt = f"""
Review the following source code.

File: {file_path}

Code:
{code}

Return the review in the required JSON format.
"""
        response = await self.llm.generate(
            prompt=prompt,
            system=REVIEW_SYSTEM_PROMPT,
            temperature=0.1
        )

        cleaned_response = clean_json_response(response)

        ai_review = ReviewResult.model_validate_json(
            cleaned_response
        )

        suffix = Path(file_path).suffix or ".py"

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=suffix,
            encoding="utf-8",
            delete=False
        ) as temp_file:

            temp_file.write(code)
            temp_path = temp_file.name
        
        try:
            static_findings = self.static_analyzer.analyze(temp_path)
        finally:
            Path(temp_path).unlink(missing_ok=True)

        validated_static_findings = []
        for finding in static_findings:
            finding["file_path"] = file_path
            finding["source"] = finding.pop("tool")
            validated_static_findings.append(
                ReviewFinding.model_validate(finding)
            )

        for finding in ai_review.findings:
            finding.source = "ai"

        combined_findings = ai_review.findings + validated_static_findings
        processed = self.finding_manager.process(combined_findings)
        return ReviewResult(
            summary=ai_review.summary,
            findings=processed["findings"],
            overall_risk=processed["overall_risk"],
            review_status=processed["review_status"],
            statistics=processed["statistics"],
        )