import asyncio
from mr_guardian.llm.service import LLMService

async def main():
    llm = LLMService()

    result = await llm.generate(
        system="You are an expert software code reviewer.",
        prompt="""
        Review this code:

        def get_user(username):
            query = "SELECT * FROM users WHERE name='" + username + "'"
            return query

        Identify the security vulnerability.
        """
    )

    print("\nMR Guardian Review:")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())