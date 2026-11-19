import asyncio
from mr_guardian.review.engine import ReviewEngine

async def main():

    engine = ReviewEngine()

    code = """
def get_user(username):
    query = "SELECT * FROM users WHERE name='" + username + "'"
    return query
"""

    result = await engine.review_code(
        code=code,
        file_path="users.py"
    )

    print("\n========== MR GUARDIAN ==========")

    print("\nSummary:")
    print(result.summary)

    print("\nFindings:")

    for finding in result.findings:

        print("\nSeverity:", finding.severity.upper())
        print("Category:", finding.category)
        print("Title:", finding.title)
        print("File:", finding.file_path)
        print("Line:", finding.line_number)
        print("Description:", finding.description)
        print("Recommendation:", finding.recommendation)

    print("\nTotal findings:", len(result.findings))

if __name__ == "__main__":
    asyncio.run(main())