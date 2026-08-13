import asyncio
from typing import Dict, Any, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
import json
import os

from ..core.config import settings
from ..core.models import DecodoRequest, DecodoResponse, TaskType
from ..core.exceptions import DecodoAPIError, Authentication
from ..core.logging import get_logger, log_api_call


class AIClient:
    
    def __init__(self):
        
        self.logger = get_logger("ai.client")
        
        # Try to use OpenAI
        self.openai_api_key = os.getenv("OPEN_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        
        # Default to simulation if no AI API keys are available
        self.use_simulation = not (self.openai_api_key or self.anthropic_api_key)
        
        if self.use_simulation:
            self.logger.info("No AI API keys found, Using Simulation mode for development")
            
        else:
            self.logger.info("AI Client initialized with real api access ") 
    
    @retry(
        stop = stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    @long_api_call("ai")
    async def process_text(
        self,
        prompt: str,
        input_text: str,
        task_type: Optional[TaskType] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> DecodoResponse:
        """  Processing text using AI/ML services  """
        request = DecodoRequest(
            prompt= prompt,
            input_text = input_text,
            task_type = task_type,
            parameters = parameters or {}
        )
        
        try: 
            if self.use_simulation:
                response =  await self._simulate_ai_call(request)
            else:
                # Try to call real AI API call
                if self.openai_api_key:
                    response = await self._call_openai(request)
                elif self.anthropic_api_key:
                    response = await self._call_anthropic(request)
                else:
                    response =  await self._simulate_ai_call(request)
                
            return DecodoResponse(
                request_id = request.request_id,
                success=True,
                output=response["output"],
                confidence=response.get("confidence"),
                token_usage = response.get("token_usage", 0),
                cost = response.get("cost"),
                processing_time = response.get("processing_time")
            )
            
        except Exception as e:
            self.logger.error(f"AI processsing failed; {e}")
            # Fallback to simulation
            response = await self._simulate_ai_call(request)
            return DecodoResponse(
                request_id=request.request_id,
                success=True,
                output=response["output"],
                confidence=response.get("confidence", 0.7),
                token_usage=response.get("token_usage", 0),
                cost=response.get("cost"),
                processing_time=response.get("processing_time")
            )
        
    
    async def _call_openai(self, request: DecodoResponse) -> Dict[str, Any]:
        """ Call OpenAI API for text generation. """
        import time
        start_time = time.time()
        
        headers ={
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content_type" : "application/json"
        }
        
        # Build prompt based on task type
        system_prompt = self._build_system_prompt(request.task_type)
        user_prompt = f"{request.prompt}\n\n Text: {request.input_text}"
        
        payload = {
            "model" : "gpt-3.5-turbo",
            "messages" : [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens" : request.parameters.get("max_tokens", 1000)
            temperature : request.parameters.get("temperature", 0.7)
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30.0
            )
            
            response.raise_for_status()
            
            data = response.json()
            output = data["choices"][0]["message"]["content"]
            token_usage = data.get("usage", {}).get("total_token", 0)
            
            return {
                "output" : output,
                "confidence" : 0.9,
                "token_usage" : token_usage,
                "cost" : token_usage * 0.002/ 1000, # Rough estimate
                "processing_time" : time.time() - start_time 
            } 
            