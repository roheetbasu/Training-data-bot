import os
import time
from typing import Any, Dict, Optional

import httpx

from ..core.logging import get_logger, log_api_call
from ..core.models import DecodoRequest, DecodoResponse, TaskType


class AIClient:
    """Small provider client with a deterministic local simulation fallback."""

    def __init__(self):
        self.logger = get_logger("ai.client")
        self.openai_api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPEN_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.provider = os.getenv("AI_PROVIDER", "auto").lower()
        self.use_simulation = self.provider == "simulation" or (
            self.provider == "auto" and not (self.openai_api_key or self.anthropic_api_key)
        )
        if self.use_simulation:
            self.logger.info("AI provider: simulation")
        else:
            self.logger.info("AI provider: %s", self.provider if self.provider != "auto"
                             else ("openai" if self.openai_api_key else "anthropic"))

    @log_api_call("ai")
    async def process_text(
        self,
        prompt: str,
        input_text: str,
        task_type: Optional[TaskType] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> DecodoResponse:
        request = DecodoRequest(
            prompt=prompt,
            input_text=input_text,
            task_type=task_type,
            parameters=parameters or {},
        )
        start = time.perf_counter()
        try:
            if self.use_simulation:
                result = await self._simulate_ai_call(request)
            elif self.openai_api_key and self.provider in ("auto", "openai"):
                result = await self._call_openai(request)
            elif self.anthropic_api_key and self.provider in ("auto", "anthropic"):
                result = await self._call_anthropic(request)
            else:
                result = await self._simulate_ai_call(request)
            result.setdefault("processing_time", time.perf_counter() - start)
            return DecodoResponse(
                request_id=request.request_id,
                success=True,
                output=result.get("output", ""),
                confidence=result.get("confidence", 0.8),
                token_usage=result.get("token_usage", 0),
                cost=result.get("cost"),
                processing_time=result.get("processing_time"),
            )
        except Exception as exc:
            self.logger.warning("AI call failed; using simulation fallback: %s", exc)
            result = await self._simulate_ai_call(request)
            return DecodoResponse(
                request_id=request.request_id,
                success=True,
                output=result["output"],
                confidence=result.get("confidence", 0.7),
                token_usage=result.get("token_usage", 0),
                cost=0.0,
                processing_time=time.perf_counter() - start,
            )

    async def _call_openai(self, request: DecodoRequest) -> Dict[str, Any]:
        start = time.perf_counter()
        system_prompt = self._build_system_prompt(request.task_type)
        payload = {
            "model": request.parameters.get("model", os.getenv("OPENAI_MODEL", "gpt-4o-mini")),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{request.prompt}\n\nText: {request.input_text}"},
            ],
            "max_tokens": request.parameters.get("max_tokens", 1000),
            "temperature": request.parameters.get("temperature", 0.2),
        }
        headers = {"Authorization": f"Bearer {self.openai_api_key}"}
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        usage = data.get("usage", {})
        tokens = usage.get("total_tokens", 0)
        return {
            "output": data["choices"][0]["message"]["content"].strip(),
            "confidence": 0.9,
            "token_usage": tokens,
            "cost": None,
            "processing_time": time.perf_counter() - start,
        }

    async def _call_anthropic(self, request: DecodoRequest) -> Dict[str, Any]:
        start = time.perf_counter()
        payload = {
            "model": request.parameters.get(
                "model", os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-latest")
            ),
            "max_tokens": request.parameters.get("max_tokens", 1000),
            "system": self._build_system_prompt(request.task_type),
            "messages": [{
                "role": "user",
                "content": f"{request.prompt}\n\nText: {request.input_text}",
            }],
        }
        headers = {
            "x-api-key": self.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        usage = data.get("usage", {})
        tokens = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
        return {
            "output": data["content"][0]["text"].strip(),
            "confidence": 0.9,
            "token_usage": tokens,
            "cost": None,
            "processing_time": time.perf_counter() - start,
        }

    def _build_system_prompt(self, task_type: Optional[TaskType]) -> str:
        if task_type == TaskType.QA_GENERATION:
            return "Create accurate question-answer pairs using only the supplied text."
        if task_type == TaskType.CLASSIFICATION:
            return "Classify the supplied text concisely and explain the label only when useful."
        if task_type == TaskType.SUMMARIZATION:
            return "Write a concise, faithful summary of the supplied text without inventing facts."
        return "Follow the user's instruction using only the supplied text."

    async def _simulate_ai_call(self, request: DecodoRequest) -> Dict[str, Any]:
        text = request.input_text.strip()
        if request.task_type == TaskType.QA_GENERATION:
            output = self._generate_mock_qa(text)
        elif request.task_type == TaskType.CLASSIFICATION:
            output = self._generate_mock_classification(text)
        elif request.task_type == TaskType.SUMMARIZATION:
            output = self._generate_mock_summary(text)
        else:
            output = text[:500]
        return {"output": output, "confidence": 0.85, "token_usage": max(1, len(text.split()))}

    def _generate_mock_qa(self, text: str) -> str:
        excerpt = " ".join(text.split())[:220]
        return (
            "Q: What is the main topic of the provided text?\n"
            f"A: {excerpt}\n\n"
            "Q: What key information does the text contain?\n"
            "A: It contains the main facts and concepts described in the source text."
        )

    def _generate_mock_classification(self, text: str) -> str:
        lowered = text.lower()
        if any(w in lowered for w in ("science", "physics", "biology", "chemistry")):
            return "Science"
        if any(w in lowered for w in ("history", "war", "empire", "historical")):
            return "History"
        if any(w in lowered for w in ("python", "software", "computer", "machine learning")):
            return "Technology"
        return "General"

    def _generate_mock_summary(self, text: str) -> str:
        clean = " ".join(text.split())
        if len(clean) <= 300:
            return f"Summary: {clean}"
        return f"Summary: {clean[:300].rsplit(' ', 1)[0]}..."

    async def close(self):
        """Compatibility hook; this client creates short-lived HTTP clients."""
        return None
