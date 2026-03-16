"""
Google Gemini LLM Provider.
High-quality AI inference using Google's Generative AI API.
"""
import httpx
import logging
from typing import Dict, Any, List, Optional
from app.config import settings
from app.services.llm_base import LLMProvider

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """
    Google Gemini LLM provider for high-quality AI inference.
    Supports gemini-1.5-flash, gemini-1.5-pro, and gemini-2.0-flash models.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL
        
        if not self.api_key:
            logger.warning("⚠️ GEMINI_API_KEY not found in settings. Some AI features may be disabled.")

    def _get_base_url(self) -> str:
        """Get the API URL for the configured model."""
        return f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    def _convert_messages_to_gemini_format(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Convert OpenAI-style messages to Gemini format.
        
        OpenAI format: [{"role": "user", "content": "..."}]
        Gemini format: {"contents": [{"role": "user", "parts": [{"text": "..."}]}]}
        """
        contents = []
        system_instruction = None
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # Handle system messages separately (Gemini uses systemInstruction)
            if role == "system":
                system_instruction = content
                continue
            
            # Map OpenAI roles to Gemini roles
            gemini_role = "user" if role == "user" else "model"
            
            # Handle multi-modal content (list of parts)
            if isinstance(content, list):
                parts = []
                for part in content:
                    if isinstance(part, dict):
                        if part.get("type") == "text":
                            parts.append({"text": part.get("text", "")})
                        elif part.get("type") == "image_url":
                            image_url = part.get("image_url", {}).get("url", "")
                            if image_url.startswith("data:"):
                                # Extract mime type and base64 data
                                # Format: data:image/jpeg;base64,.....
                                try:
                                    header, base64_data = image_url.split(",", 1)
                                    mime_type = header.split(";")[0].split(":")[1]
                                    parts.append({
                                        "inline_data": {
                                            "mime_type": mime_type,
                                            "data": base64_data
                                        }
                                    })
                                except Exception as e:
                                    logger.error(f"Failed to parse image data format: {e}")
                            else:
                                logger.warning("Only base64 data URI supported for Gemini images currently.")
                contents.append({
                    "role": gemini_role,
                    "parts": parts
                })
            else:
                # Standard text content
                contents.append({
                    "role": gemini_role,
                    "parts": [{"text": str(content)}]
                })
        
        return {
            "contents": contents,
            "systemInstruction": {"parts": [{"text": system_instruction}]} if system_instruction else None
        }

    async def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.1,
        max_tokens: int = 4096,
        response_format: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Execute a chat completion request to Google Gemini API.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum output tokens
            response_format: Optional format spec (e.g., {"type": "json_object"})
            
        Returns:
            Response dict in OpenAI-compatible format for drop-in replacement
        """
        if not self.api_key:
            raise ValueError("GEMINI API Key is missing. Please configure it in the .env file.")

        url = f"{self._get_base_url()}?key={self.api_key}"
        
        # Convert messages to Gemini format
        gemini_payload = self._convert_messages_to_gemini_format(messages)
        
        # Build generation config
        generation_config = {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        }
        
        # Handle JSON response format
        if response_format and "json" in response_format.get("type", "").lower():
            generation_config["responseMimeType"] = "application/json"
            # Ensure prompt mentions JSON if not already
            if gemini_payload["contents"]:
                last_content = gemini_payload["contents"][-1]
                if last_content["parts"]:
                    text = last_content["parts"][-1].get("text", "")
                    if "json" not in text.lower():
                        last_content["parts"][-1]["text"] = text + "\nRespond in valid JSON format."
        
        payload = {
            "contents": gemini_payload["contents"],
            "generationConfig": generation_config
        }
        
        # Add system instruction if present
        if gemini_payload.get("systemInstruction"):
            payload["systemInstruction"] = gemini_payload["systemInstruction"]

        headers = {
            "Content-Type": "application/json"
        }

        for attempt in range(3):
            async with httpx.AsyncClient(timeout=60.0) as client:
                try:
                    response = await client.post(url, headers=headers, json=payload)
                    response.raise_for_status()
                    
                    gemini_response = response.json()
                    
                    # Convert Gemini response to OpenAI-compatible format
                    return self._convert_to_openai_format(gemini_response)
                    
                except httpx.HTTPStatusError as e:
                    error_detail = e.response.text if hasattr(e.response, 'text') else str(e)
                    logger.error(f"❌ Gemini API Error: {e.response.status_code} - {error_detail}")
                    
                    # Don't retry client errors (4xx), only server errors (5xx)
                    if 400 <= e.response.status_code < 500:
                        raise
                        
                except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.NetworkError) as e:
                    logger.warning(f"⚠️ Gemini Network Error (Attempt {attempt+1}/3): {e}")
                    if attempt == 2:
                        raise
                        
                except Exception as e:
                    logger.error(f"❌ Unexpected Error during Gemini inference: {e}")
                    raise

    def _convert_to_openai_format(self, gemini_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Gemini API response to OpenAI-compatible format.
        This allows drop-in replacement without changing existing code.
        """
        try:
            # Extract text from Gemini response
            candidates = gemini_response.get("candidates", [])
            if not candidates:
                return {
                    "choices": [{
                        "message": {
                            "content": '{"error": "No response generated"}'
                        }
                    }]
                }
            
            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            
            text = ""
            for part in parts:
                if "text" in part:
                    text += part["text"]
            
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": text
                    },
                    "finish_reason": candidates[0].get("finishReason", "stop")
                }],
                "model": self.model,
                "usage": gemini_response.get("usageMetadata", {})
            }
            
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {e}")
            return {
                "choices": [{
                    "message": {
                        "content": f'{{"error": "Failed to parse response: {str(e)}"}}'
                    }
                }]
            }


# Global provider instance
gemini_provider = GeminiProvider()
