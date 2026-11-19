import unittest
from unittest.mock import AsyncMock

from mr_guardian.review.engine import ReviewEngine
from mr_guardian.review.schemas import ReviewResult


class ReviewEngineTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = ReviewEngine()
        self.engine.llm.generate = AsyncMock(
            return_value=ReviewResult(summary="Review complete").model_dump_json()
        )

    async def test_returns_result_when_ai_has_no_findings(self):
        self.engine.static_analyzer.analyze = lambda _: []

        result = await self.engine.review_code("print('hello')", "example.py")

        self.assertEqual(result.summary, "Review complete")
        self.assertEqual(result.findings, [])

    async def test_preserves_static_analyzer_error(self):
        def fail_analysis(_):
            raise RuntimeError("static analyzer failed")

        self.engine.static_analyzer.analyze = fail_analysis

        with self.assertRaisesRegex(RuntimeError, "static analyzer failed"):
            await self.engine.review_code("print('hello')", "example.py")


if __name__ == "__main__":
    unittest.main()
