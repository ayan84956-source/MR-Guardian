import asyncio
from mr_guardian.llm.service import LLMService
from mr_guardian.review.prompts import REVIEW_SYSTEM_PROMPT
from mr_guardian.review.schemas import ReviewResult
from mr_guardian.review.schemas import (
    ReviewResult,
    clean_json_response
)

async def main():
    llm = LLMService()

    code = """
def get_user(username):
    query = "SELECT * FROM users WHERE name='" + username + "'"
    return query
"""

    prompt = f"""
Review the following Python code.

File: users.py

{code}

Return the review in the required JSON format.
"""

    response = await llm.generate(
        prompt=prompt,
        system=REVIEW_SYSTEM_PROMPT,
        temperature=0.1
    )

    try:
        cleaned_response = clean_json_response(response)
        review = ReviewResult.model_validate_json(cleaned_response)

        print("\n========== MR GUARDIAN REVIEW ==========")
        print("Summary:", review.summary)

        for finding in review.findings:
            print("\nSeverity:", finding.severity.upper())
            print("Category:", finding.category)
            print("Title:", finding.title)
            print("Description:", finding.description)
            print("Recommendation:", finding.recommendation)

        print("\nTotal findings:", len(review.findings))

    except Exception as error:
        print("Could not validate AI response:", error)
        print("Raw response:", response)


if __name__ == "__main__":
    asyncio.run(main())