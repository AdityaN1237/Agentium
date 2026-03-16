import torch
from transformers import AutoProcessor, AutoModelForCausalLM
from PIL import Image
import io
import logging
from typing import Dict, Any, Union

logger = logging.getLogger(__name__)

class LocalVisionService:
    """
    Local Vision Service using Microsoft Florence-2-large.
    Provides Dense Captioning and OCR without external APIs.
    """
    
    _instance = None
    
    def __init__(self, model_id: str = "microsoft/Florence-2-large"):
        self.model_id = model_id
        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        # Fallback to CPU if MPS has issues with some ops (Florence usually fine on MPS)
        self.model = None
        self.processor = None
        self._load_model()

    def _load_model(self):
        """Load model and processor into memory."""
        try:
            logger.info(f"🔄 Loading Local Vision Model ({self.model_id}) on {self.device}...")
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id, 
                trust_remote_code=True,
                torch_dtype=torch.float16 if self.device == "mps" else torch.float32
            ).to(self.device)
            
            self.processor = AutoProcessor.from_pretrained(
                self.model_id, 
                trust_remote_code=True
            )
            logger.info("✅ Local Vision Model Loaded Successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to load Local Vision Model: {e}")
            raise

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = LocalVisionService()
        return cls._instance

    def analyze_image(self, image_bytes: bytes) -> str:
        """
        Analyze image to get dense captions and text (OCR).
        """
        if not self.model or not self.processor:
            return "[Error: Vision Model not loaded]"

        try:
            image = Image.open(io.BytesIO(image_bytes))
            if image.mode != "RGB":
                image = image.convert("RGB")

            # 1. OCR (Extract Text)
            ocr_text = self._run_task(image, "<OCR>")
            
            # 2. Dense Captioning (Describe Content)
            caption = self._run_task(image, "<MORE_DETAILED_CAPTION>") # or <DENSE_CAPTION>

            return f"**Image Text:**\n{ocr_text}\n\n**Visual Description:**\n{caption}"

        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            return f"[Error analyzing image: {str(e)}]"

    def _run_task(self, image: Image.Image, task_prompt: str) -> str:
        """Run a specific Florence-2 task."""
        inputs = self.processor(text=task_prompt, images=image, return_tensors="pt").to(self.device, torch.float16 if self.device == "mps" else torch.float32)
        
        generated_ids = self.model.generate(
            input_ids=inputs["input_ids"],
            pixel_values=inputs["pixel_values"],
            max_new_tokens=1024,
            do_sample=False,
            num_beams=3,
        )
        
        generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
        parsed_answer = self.processor.post_process_generation(
            generated_text, 
            task=task_prompt, 
            image_size=(image.width, image.height)
        )
        
        # Florence return format varies by task
        if isinstance(parsed_answer, dict):
            # For OCR it returns {'<OCR>': 'text...'}
            return parsed_answer.get(task_prompt, str(parsed_answer))
        return str(parsed_answer)

# Global helper
def get_local_vision() -> LocalVisionService:
    return LocalVisionService.get_instance()
