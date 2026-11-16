"""Provider-agnostic factories for chat models and embeddings.

Switching between OpenAI, Ollama and Hugging Face is purely a configuration
change; provider SDKs are imported lazily so unused ones need not be installed.
"""
from __future__ import annotations

from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel

from config import Settings
from core.exceptions import ConfigurationError


def _openai_key(settings: Settings) -> str:
    if settings.openai_api_key is None or not settings.openai_api_key.get_secret_value():
        raise ConfigurationError("OPENAI_API_KEY is not set. Add it to backend/.env.")
    return settings.openai_api_key.get_secret_value()


def build_chat_model(settings: Settings) -> BaseChatModel:
    try:
        if settings.llm_provider == "openai":
            from langchain_openai import ChatOpenAI

            return ChatOpenAI(
                model=settings.openai_chat_model,
                api_key=_openai_key(settings),
                base_url=settings.openai_base_url,
                temperature=settings.llm_temperature,
                timeout=settings.llm_timeout_seconds,
                max_retries=2,
            )
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=settings.ollama_chat_model,
            base_url=settings.ollama_base_url,
            temperature=settings.llm_temperature,
        )
    except ImportError as exc:
        raise ConfigurationError(f"Missing dependency for LLM provider: {exc}") from exc


def build_embeddings(settings: Settings) -> Embeddings:
    try:
        if settings.embedding_provider == "openai":
            from langchain_openai import OpenAIEmbeddings

            return OpenAIEmbeddings(
                model=settings.openai_embedding_model,
                api_key=_openai_key(settings),
                base_url=settings.openai_base_url,
            )
        if settings.embedding_provider == "ollama":
            from langchain_ollama import OllamaEmbeddings

            return OllamaEmbeddings(
                model=settings.ollama_embedding_model, base_url=settings.ollama_base_url
            )
        from langchain_huggingface import HuggingFaceEmbeddings

        return HuggingFaceEmbeddings(model_name=settings.hf_embedding_model)
    except ImportError as exc:
        raise ConfigurationError(f"Missing dependency for embeddings: {exc}") from exc
