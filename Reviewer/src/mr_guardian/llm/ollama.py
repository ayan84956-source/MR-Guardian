import httpx
from mr_guardian.core.config import settings

class OllamaProvider:
    def __init__(self):
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model

    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.2,
    ) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system or "",
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }

        timeout_config = httpx.Timeout(
            connect=10.0,
            read=600.0,
            write=30.0,
            pool=30.0,
        )

        try:
            async with httpx.AsyncClient(timeout=timeout_config) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                )
                response.raise_for_status()
                result = response.json()
        except httpx.ConnectError as exc:
            raise RuntimeError("Cannot connect to Ollama server") from exc
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Ollama request failed with status {exc.response.status_code}: "
                f"{exc.response.text}"
            ) from exc
        except (KeyError, ValueError) as exc:
            raise RuntimeError("Ollama returned an invalid response") from exc

        if not isinstance(result, dict) or not isinstance(result.get("response"), str):
            raise RuntimeError("Ollama returned an invalid response")

        return result["response"]        