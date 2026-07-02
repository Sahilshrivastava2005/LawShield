from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from .base import BaseLLMProvider
from config.settings import settings

class OpenAIProvider(BaseLLMProvider):
    def get_model(self, streaming: bool = False):
        return ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model="gpt-4o-mini",
            streaming=streaming,
            temperature=0.7
        )

class GeminiProvider(BaseLLMProvider):
    def get_model(self, streaming: bool = False):
        return ChatGoogleGenerativeAI(
            api_key=settings.GEMINI_API_KEY,
            model="gemini-2.5-flash",
            streaming=streaming,
            temperature=0.7
        )

class AnthropicProvider(BaseLLMProvider):
    def get_model(self, streaming: bool = False):
        return ChatAnthropic(
            api_key=settings.ANTHROPIC_API_KEY,
            model="claude-3-haiku-20240307",
            streaming=streaming,
            temperature=0.7
        )

def get_llm_provider(provider_name: str = None) -> BaseLLMProvider:
    provider = provider_name or settings.DEFAULT_LLM_PROVIDER
    if provider == "openai":
        return OpenAIProvider()
    elif provider == "gemini":
        return GeminiProvider()
    elif provider == "anthropic":
        return AnthropicProvider()
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
