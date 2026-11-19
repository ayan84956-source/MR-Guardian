
import asyncio

from mr_guardian.llm.ollama import OllamaProvider


async def main():
    provider = OllamaProvider()

    print("Testing MR Guardian Ollama integration...")
    print("Model:", provider.model)

    result = await provider.generate(
        prompt="Identify the vulnerability in this code: "
               "query = \"SELECT * FROM users WHERE name='\" + username"
    )

    print("\nAI Review Result:")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
