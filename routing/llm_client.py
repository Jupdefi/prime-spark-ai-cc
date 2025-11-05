"""
LLM Client with Intelligent Routing
Routes LLM requests through the intelligent router
"""
import httpx
from typing import Optional, Dict, Any, AsyncIterator
from routing.router import router, ComputeLocation
from memory.memory_manager import memory
from tenacity import retry, stop_after_attempt, wait_exponential


class LLMClient:
    """
    LLM client with intelligent edge-cloud routing.

    Features:
    - Automatic edge/cloud routing
    - Response caching
    - Retry logic with fallback
    - Streaming support
    """

    def __init__(self):
        self.router = router
        self.memory = memory

    def _generate_cache_key(self, model: str, prompt: str) -> str:
        """Generate cache key for LLM response"""
        import hashlib
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]
        return f"llm:{model}:{prompt_hash}"

    async def generate(
        self,
        prompt: str,
        model: str = "llama3.2:latest",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        use_cache: bool = True,
        power_mode: str = "on-grid"
    ) -> Dict[str, Any]:
        """
        Generate LLM response with intelligent routing.

        Args:
            prompt: Input prompt
            model: Model name
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            use_cache: Whether to use response cache
            power_mode: Current power mode

        Returns:
            Dict with response and metadata
        """
        # Check cache first
        cache_key = self._generate_cache_key(model, prompt)
        if use_cache:
            cached_response = await self.memory.get(cache_key)
            if cached_response:
                return {
                    "response": cached_response["response"],
                    "model": cached_response["model"],
                    "location": cached_response["location"],
                    "cached": True,
                    "latency_ms": 0
                }

        # Route request
        route_decision = await self.router.route_request(
            request_type="llm",
            power_mode=power_mode
        )

        # Make request to selected endpoint
        try:
            response = await self._make_request(
                endpoint=route_decision.endpoint,
                model=model,
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )

            # Cache successful response
            if use_cache and response.get("response"):
                cache_data = {
                    "response": response["response"],
                    "model": model,
                    "location": route_decision.location.value
                }
                await self.memory.set(cache_key, cache_data, ttl=3600)

            return {
                "response": response.get("response", ""),
                "model": model,
                "location": route_decision.location.value,
                "reason": route_decision.reason,
                "latency_ms": route_decision.latency_ms,
                "cached": False
            }

        except Exception as e:
            return {
                "error": str(e),
                "location": route_decision.location.value,
                "reason": route_decision.reason
            }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def _make_request(
        self,
        endpoint: str,
        model: str,
        prompt: str,
        temperature: float,
        max_tokens: Optional[int]
    ) -> Dict[str, Any]:
        """Make request to Ollama endpoint with retry logic"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "model": model,
                "prompt": prompt,
                "temperature": temperature,
                "stream": False
            }

            if max_tokens:
                payload["options"] = {"num_predict": max_tokens}

            response = await client.post(
                f"{endpoint}/api/generate",
                json=payload
            )
            response.raise_for_status()

            data = response.json()
            return {
                "response": data.get("response", ""),
                "model": data.get("model", model),
                "eval_count": data.get("eval_count", 0),
                "eval_duration": data.get("eval_duration", 0)
            }

    async def generate_stream(
        self,
        prompt: str,
        model: str = "llama3.2:latest",
        temperature: float = 0.7,
        power_mode: str = "on-grid"
    ) -> AsyncIterator[str]:
        """
        Generate LLM response with streaming.

        Args:
            prompt: Input prompt
            model: Model name
            temperature: Sampling temperature
            power_mode: Current power mode

        Yields:
            Response tokens as they're generated
        """
        # Route request
        route_decision = await self.router.route_request(
            request_type="llm",
            power_mode=power_mode
        )

        # Stream from selected endpoint
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {
                "model": model,
                "prompt": prompt,
                "temperature": temperature,
                "stream": True
            }

            async with client.stream(
                "POST",
                f"{route_decision.endpoint}/api/generate",
                json=payload
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line:
                        import json
                        try:
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
                        except json.JSONDecodeError:
                            continue

    async def list_models(
        self,
        location: Optional[ComputeLocation] = None
    ) -> Dict[str, Any]:
        """
        List available models.

        Args:
            location: Specific location to query, or None for all

        Returns:
            Dict with models from each location
        """
        if location:
            health = await self.router.get_endpoint_health(location)
            if health.is_healthy:
                return await self._list_models_from_endpoint(health.endpoint)
            return {"error": f"Location {location.value} is not healthy"}

        # Query all locations
        edge_health = await self.router.get_endpoint_health(ComputeLocation.EDGE_LOCAL)
        cloud_health = await self.router.get_endpoint_health(ComputeLocation.CLOUD_CORE4)

        result = {}

        if edge_health.is_healthy:
            result["edge"] = await self._list_models_from_endpoint(edge_health.endpoint)

        if cloud_health.is_healthy:
            result["cloud"] = await self._list_models_from_endpoint(cloud_health.endpoint)

        return result

    async def _list_models_from_endpoint(self, endpoint: str) -> Dict[str, Any]:
        """List models from a specific endpoint"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{endpoint}/api/tags")
                response.raise_for_status()
                data = response.json()
                return {
                    "models": [m["name"] for m in data.get("models", [])],
                    "endpoint": endpoint
                }
        except Exception as e:
            return {"error": str(e)}


# Global LLM client instance
llm_client = LLMClient()
