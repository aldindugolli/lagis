# LAGIS - Unified LLM Access Layer
# All LLM access MUST go through this wrapper

import json
import requests
from typing import Dict, Any, List, Optional


class LLMEngine:
    """Single source of truth for all LLM interactions"""
    
    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.timeout = 120  # Increased for complex prompts
        self.reasoning_model = "llama3.1:8b"
        self.summarization_model = "llama3.1:8b"
        self.embedding_model = "nomic-embed-text"
    
    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        system: Optional[str] = None
    ) -> str:
        """Generate text from LLM"""
        model = model or self.summarization_model
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens}
        }
        if system:
            payload["system"] = system
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()["response"]
        except requests.exceptions.Timeout:
            return "Error: Request timed out"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        model: Optional[str] = None,
        temperature: float = 0.3,
        system: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate structured JSON output"""
        model = model or self.reasoning_model
        
        # Get required fields from schema for simpler prompt
        required = schema.get("required", [])
        props = schema.get("properties", {})
        
        # Build simple JSON format
        format_parts = []
        for field in required:
            field_type = props.get(field, {}).get("type", "string")
            if field_type == "array":
                format_parts.append(f'"{field}": []')
            elif field_type == "number":
                format_parts.append(f'"{field}": 0')
            else:
                format_parts.append(f'"{field}": "..."')
        json_format = "{" + ", ".join(format_parts) + "}"
        
        full_prompt = f"""{prompt}

Return ONLY valid JSON. Format: {json_format}

JSON:"""

        for attempt in range(3):
            try:
                result = self.generate(
                    prompt=full_prompt,
                    model=model,
                    temperature=temperature,
                    max_tokens=512,
                    system=system
                )
                if result.startswith("Error:"):
                    if attempt == 2:
                        return {"error": result}
                    continue
                json_start = result.find('{')
                json_end = result.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    return json.loads(result[json_start:json_end])
            except (json.JSONDecodeError, Exception) as e:
                if attempt == 2:
                    return {"error": f"Failed: {str(e)}"}
        return {"error": "Max attempts exceeded"}
    
    def embed(self, text: str) -> List[float]:
        """Generate embeddings"""
        response = requests.post(
            f"{self.base_url}/api/embeddings",
            json={"model": self.embedding_model, "prompt": text},
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()["embedding"]


_llm_engine: Optional[LLMEngine] = None


def get_llm() -> LLMEngine:
    global _llm_engine
    if _llm_engine is None:
        _llm_engine = LLMEngine()
    return _llm_engine
