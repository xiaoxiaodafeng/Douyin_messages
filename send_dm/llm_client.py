import os
from dataclasses import dataclass

import requests


DEFAULT_WORKSPACE_ID = "5074654"
DEFAULT_MODEL = "deepseek-v4-flash"
DEFAULT_SYSTEM_PROMPT = "你是一个抖音私信自动回复助手，请结合当前会话上下文，用自然、简洁、礼貌的中文直接回复对方。"
DASHSCOPE_COMPAT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL_ALIASES = {
    "DeepSeek-V4-Flash": "deepseek-v4-flash",
    "DeepSeek-V4-Pro": "deepseek-v4-pro",
}


def build_aliyun_base_url(workspace_id: str) -> str:
    return f"https://{workspace_id}.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"


def normalize_model_name(model: str) -> str:
    model = str(model).strip()
    return MODEL_ALIASES.get(model, model)


@dataclass
class LLMConfig:
    api_key: str
    base_url: str
    model: str
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
    timeout: int = 60


def resolve_llm_config(
    api_key: str | None = None,
    base_url: str | None = None,
    workspace_id: str | None = None,
    model: str | None = None,
    system_prompt: str | None = None,
    timeout: int | None = None,
) -> LLMConfig:
    workspace_id = workspace_id or os.getenv("ALIYUN_MAAS_WORKSPACE_ID") or DEFAULT_WORKSPACE_ID
    base_url = (base_url or os.getenv("ALIYUN_MAAS_BASE_URL") or build_aliyun_base_url(workspace_id)).rstrip("/")
    model = normalize_model_name(model or os.getenv("ALIYUN_MAAS_MODEL") or DEFAULT_MODEL)
    api_key = api_key or os.getenv("ALIYUN_MAAS_API_KEY")
    system_prompt = system_prompt or os.getenv("ALIYUN_MAAS_SYSTEM_PROMPT") or DEFAULT_SYSTEM_PROMPT
    timeout = int(timeout or os.getenv("ALIYUN_MAAS_TIMEOUT") or 60)

    if not api_key:
        raise RuntimeError("缺少阿里云 MaaS API Key，请通过 --api-key 或 ALIYUN_MAAS_API_KEY 提供")

    return LLMConfig(
        api_key=api_key,
        base_url=base_url,
        model=model,
        system_prompt=system_prompt,
        timeout=timeout,
    )


class OpenAICompatibleChatClient:
    def __init__(self, config: LLMConfig):
        self.config = config

    def _request(self, base_url: str, messages: list[dict]):
        return requests.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.config.model,
                "messages": messages,
            },
            timeout=self.config.timeout,
        )

    def _extract_content(self, data: dict) -> str:
        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError("模型返回为空，没有 choices")

        message = (choices[0] or {}).get("message") or {}
        content = message.get("content", "")
        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
            content = "".join(text_parts)

        content = str(content).strip()
        if not content:
            raise RuntimeError("模型返回内容为空")
        return content

    def chat(self, messages: list[dict]) -> str:
        response = self._request(self.config.base_url, messages)
        if response.status_code >= 400:
            body = response.text
            if "Workspace endpoint is invalid." in body and self.config.base_url != DASHSCOPE_COMPAT_BASE_URL:
                response = self._request(DASHSCOPE_COMPAT_BASE_URL, messages)
        response.raise_for_status()
        return self._extract_content(response.json())
