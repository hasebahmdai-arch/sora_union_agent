import json
import logging
from typing import Any
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("shopeasy.agent")


class ToolLogger(BaseCallbackHandler):
    def __init__(self):
        self.tools_used: list[str] = []

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        tool_name = serialized.get("name", "unknown_tool")
        self.tools_used.append(tool_name)
        inputs = kwargs.get("inputs") or input_str
        logger.info("tool start  %-28s  input=%s", tool_name, _truncate(inputs))

    def on_tool_end(
        self,
        output: Any,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        logger.info("tool end    %s", _truncate(str(output)))

    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        logger.error("tool error  %s", error)

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        **kwargs: Any,
    ) -> None:
        model = serialized.get("kwargs", {}).get("model", "gemini")
        logger.info("LLM  %-10s  ...", model)

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        token_usage = getattr(
            getattr(response, "llm_output", None), "get", lambda *_: None
        )("token_usage")
        if token_usage:
            logger.info("LLM  done  tokens=%s", token_usage)
        else:
            logger.info("LLM  done")


def _truncate(value: Any, max_len: int = 120) -> str:
    text = json.dumps(value) if not isinstance(value, str) else value
    return text[:max_len] + "..." if len(text) > max_len else text
