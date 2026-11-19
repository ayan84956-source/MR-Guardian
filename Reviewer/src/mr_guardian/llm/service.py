from mr_guardian.core.config import settings
from mr_guardian.llm.ollama import OllamaProvider

class LLMService:
    def __init__(self):

       if settings.llm_provider =="ollama":
           self.provider = OllamaProvider()
       else:
          raise ValueError(
                f"Unsupported LLM provider: {settings.llm_provider}"
            )

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.2,
    ) -> str:

        return await self.provider.generate(
            prompt=prompt,
            system=system,
            temperature=temperature,
        )