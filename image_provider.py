"""
Image Generation Provider Interface and Implementations
Supports OpenAI Images, Flux (via multiple hosts), and LTX
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import logging
import base64
from io import BytesIO
from PIL import Image

logger = logging.getLogger("flux_prompt")


class ImageStyle(Enum):
    """Image generation style presets"""
    FAST_DRAFT = "fast_draft"
    PHOTOREAL = "photoreal"
    BRAND_LAYOUT = "brand_layout"
    PORTRAIT = "portrait"
    PRODUCT = "product"
    LOGO_TEXT = "logo_text"
    ARTISTIC = "artistic"
    CINEMATIC = "cinematic"


@dataclass
class ImageGenerationRequest:
    """Standardized image generation request"""
    prompt: str
    negative_prompt: Optional[str] = None
    width: int = 1024
    height: int = 1024
    seed: Optional[int] = None
    steps: Optional[int] = None
    guidance_scale: Optional[float] = None
    style: Optional[ImageStyle] = None
    source_image_url: Optional[str] = None  # For img2img
    mask_image_url: Optional[str] = None  # For inpainting
    strength: Optional[float] = None  # For img2img (0.0-1.0)
    num_images: int = 1
    provider: Optional[str] = None  # Override provider selection


@dataclass
class ImageGenerationResult:
    """Standardized image generation result"""
    success: bool
    images: List[Dict[str, Any]]  # [{"url": str, "bytes": bytes, "seed": int}]
    provider: str
    model: str
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def get_image_bytes(self, index: int = 0) -> Optional[bytes]:
        """Get image bytes from result"""
        if index < len(self.images):
            img_data = self.images[index]
            if "bytes" in img_data:
                return img_data["bytes"]
            elif "url" in img_data:
                # Would need to fetch from URL
                return None
        return None
    
    def get_image_url(self, index: int = 0) -> Optional[str]:
        """Get image URL from result"""
        if index < len(self.images):
            img_data = self.images[index]
            return img_data.get("url")
        return None


class ImageProvider(ABC):
    """Base interface for image generation providers"""
    
    @abstractmethod
    def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        """Generate image(s) from request"""
        pass
    
    @abstractmethod
    def get_supported_features(self) -> Dict[str, bool]:
        """Return supported features (img2img, inpainting, upscaling, etc.)"""
        pass
    
    @abstractmethod
    def get_default_parameters(self, style: Optional[ImageStyle] = None) -> Dict[str, Any]:
        """Get default parameters for a given style"""
        pass


class OpenAIImagesProvider(ImageProvider):
    """OpenAI Images API provider (DALL-E 3)"""
    
    def __init__(self, api_key: str):
        import openai
        self.client = openai.OpenAI(api_key=api_key)
        self.provider_name = "openai"
        self.model = "dall-e-3"
    
    def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        """Generate image using OpenAI DALL-E 3"""
        try:
            # OpenAI DALL-E 3 constraints
            if request.width != 1024 or request.height != 1024:
                logger.warning("DALL-E 3 only supports 1024x1024. Adjusting...")
                request.width = 1024
                request.height = 1024
            
            # Map style to quality/size
            quality = "standard"
            size = "1024x1024"
            
            if request.style == ImageStyle.PHOTOREAL or request.style == ImageStyle.BRAND_LAYOUT:
                quality = "hd"
            
            # Generate
            response = self.client.images.generate(
                model=self.model,
                prompt=request.prompt,
                n=1,  # DALL-E 3 only supports n=1
                size=size,
                quality=quality,
            )
            
            images = []
            for idx, image_data in enumerate(response.data):
                img_dict = {
                    "url": image_data.url,
                    "revised_prompt": getattr(image_data, 'revised_prompt', None),
                }
                images.append(img_dict)
            
            return ImageGenerationResult(
                success=True,
                images=images,
                provider=self.provider_name,
                model=self.model,
                metadata={
                    "created": getattr(response, 'created', None),
                    "quality": quality,
                }
            )
            
        except Exception as e:
            logger.error(f"OpenAI image generation failed: {e}")
            return ImageGenerationResult(
                success=False,
                images=[],
                provider=self.provider_name,
                model=self.model,
                error=str(e)
            )
    
    def get_supported_features(self) -> Dict[str, bool]:
        return {
            "img2img": False,
            "inpainting": False,
            "upscaling": False,
            "variations": True,
            "seeds": False,
            "negative_prompts": False,
            "control_net": False,
        }
    
    def get_default_parameters(self, style: Optional[ImageStyle] = None) -> Dict[str, Any]:
        defaults = {
            "width": 1024,
            "height": 1024,
            "quality": "standard",
        }
        
        if style == ImageStyle.PHOTOREAL or style == ImageStyle.BRAND_LAYOUT:
            defaults["quality"] = "hd"
        
        return defaults


class FluxProvider(ImageProvider):
    """Flux provider via various hosts (Fal.ai, Together, Fireworks, etc.)"""
    
    def __init__(self, api_key: str, host: str = "fal", model: str = "flux-schnell"):
        """
        Initialize Flux provider
        
        Args:
            api_key: API key for the host
            host: Host provider (bfl, fal, together, fireworks, replicate)
                  bfl = Black Forest Labs direct API (recommended)
            model: Flux model variant (flux-schnell, flux-dev, flux-pro, flux1.1-pro)
        """
        self.api_key = api_key
        self.host = host.lower()
        self.model = model
        self.provider_name = f"flux_{host}"
        self._init_client()
    
    def _init_client(self):
        """Initialize client based on host"""
        if self.host == "bfl":
            # Black Forest Labs direct API - uses requests library (no special client needed)
            try:
                import requests
                self.client = requests
                logger.info("Black Forest Labs direct API initialized")
            except ImportError:
                logger.error("requests library required for BFL API. Install with: pip install requests")
                self.client = None
        elif self.host == "fal":
            try:
                import fal_client
                self.client = fal_client
                self.client.set_credentials(key1=self.api_key)
            except ImportError:
                logger.error("fal_client not installed. Install with: pip install fal-client")
                self.client = None
        elif self.host == "together":
            try:
                import together
                self.client = together
                together.api_key = self.api_key
            except ImportError:
                logger.error("together not installed. Install with: pip install together")
                self.client = None
        elif self.host == "replicate":
            try:
                import replicate
                self.client = replicate
                replicate.Client(api_token=self.api_key)
            except ImportError:
                logger.error("replicate not installed. Install with: pip install replicate")
                self.client = None
        else:
            self.client = None
            logger.warning(f"Unsupported Flux host: {self.host}")
    
    def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        """Generate image using Flux"""
        if self.client is None:
            return ImageGenerationResult(
                success=False,
                images=[],
                provider=self.provider_name,
                model=self.model,
                error=f"Flux client not initialized for host: {self.host}"
            )
        
        try:
            if self.host == "bfl":
                return self._generate_bfl(request)
            elif self.host == "fal":
                return self._generate_fal(request)
            elif self.host == "together":
                return self._generate_together(request)
            elif self.host == "replicate":
                return self._generate_replicate(request)
            else:
                raise ValueError(f"Unsupported host: {self.host}")
                
        except Exception as e:
            logger.error(f"Flux image generation failed: {e}")
            return ImageGenerationResult(
                success=False,
                images=[],
                provider=self.provider_name,
                model=self.model,
                error=str(e)
            )
    
    def _generate_bfl(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        """Generate via Black Forest Labs direct API"""
        import requests
        import time
        
        # Map model names to BFL API endpoints
        # BFL API available endpoints: flux-pro, flux-pro-1.1, flux-dev, flux-kontext-pro, flux-kontext-max
        # Note: schnell is not available via BFL API (local deployment only)
        model_map = {
            "flux-schnell": "flux-dev",  # Fallback to dev since schnell not available via API
            "flux1.1-schnell": "flux-dev",
            "flux-dev": "flux-dev",
            "flux1.1-dev": "flux-dev",
            "flux-pro": "flux-pro",  # Try base flux-pro first
            "flux1.1-pro": "flux-pro",
            "flux-kontext": "flux-kontext-pro",  # Kontext for image editing
            "flux-kontext-pro": "flux-kontext-pro",
            "flux-kontext-max": "flux-kontext-max",
        }
        
        # Use mapped model name or default to flux-pro
        bfl_model = model_map.get(self.model, "flux-pro")
        # BFL API endpoint format
        api_url = f"https://api.bfl.ai/{bfl_model}"
        
        # Prepare request payload
        payload = {
            "prompt": request.prompt,
            "num_images": request.num_images,
        }
        
        # Add optional parameters
        if request.negative_prompt:
            payload["negative_prompt"] = request.negative_prompt
        
        if request.width and request.height:
            # BFL supports specific aspect ratios
            payload["aspect_ratio"] = self._get_bfl_aspect_ratio(request.width, request.height)
        
        if request.seed is not None:
            payload["seed"] = request.seed
        
        if request.steps:
            payload["num_inference_steps"] = request.steps
        
        if request.guidance_scale:
            payload["guidance_scale"] = request.guidance_scale
        
        # Handle img2img (image-to-image)
        # BFL API Flux Kontext requires the source image parameter
        if request.source_image_url:
            # BFL API Flux Kontext expects the image parameter
            # Try multiple parameter names as BFL API documentation may vary
            if request.source_image_url.startswith("data:image"):
                # Extract base64 from data URL: data:image/png;base64,<base64>
                base64_data = request.source_image_url.split(",")[1] if "," in request.source_image_url else None
                if base64_data:
                    # Try both "image" (most common) and "inputImage" parameter names
                    payload["image"] = base64_data
                    payload["inputImage"] = base64_data  # Some APIs use this
                    logger.info(f"Using base64 'image' and 'inputImage' parameters for Flux Kontext (size: {len(base64_data)} chars)")
                else:
                    logger.warning("Could not extract base64 from data URL")
            else:
                # For URLs, try multiple parameter names
                payload["image_url"] = request.source_image_url
                payload["inputImage"] = request.source_image_url
                payload["image"] = request.source_image_url
                logger.info(f"Using 'image_url', 'inputImage', and 'image' parameters for Flux Kontext: {request.source_image_url[:50]}...")
            
            # Strength parameter (how much to change, 0.0-1.0)
            if request.strength is not None:
                payload["strength"] = request.strength
            else:
                payload["strength"] = 0.7  # Default strength
            
            logger.info(f"Flux Kontext img2img: Image provided, strength={payload.get('strength', 0.7)}")
            
            # Debug: Log payload structure (without full base64 data)
            payload_keys = list(payload.keys())
            has_image = "image" in payload or "image_url" in payload or "inputImage" in payload
            logger.debug(f"Payload keys: {payload_keys}, Has image parameter: {has_image}")
        
        # Prepare headers
        headers = {
            "accept": "application/json",
            "x-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        try:
            # Step 1: Submit generation request
            # Try the primary endpoint first
            response = self.client.post(api_url, headers=headers, json=payload)
            
            # If 404, try alternative endpoint formats
            if response.status_code == 404:
                # Try alternative endpoint formats based on model
                alternatives = []
                if "kontext" in bfl_model.lower():
                    # Flux Kontext models
                    alternatives = [
                        "https://api.bfl.ai/flux-kontext-pro",
                        "https://api.bfl.ai/flux-kontext-max",
                        "https://api.bfl.ai/v1/flux-kontext-pro",
                    ]
                elif "pro" in bfl_model.lower() and "kontext" not in bfl_model.lower():
                    # Regular Flux Pro models
                    alternatives = [
                        "https://api.bfl.ai/flux-pro-1.1",
                        "https://api.bfl.ai/flux-pro",
                        "https://api.bfl.ai/v1/flux-pro-1.1",
                    ]
                elif "dev" in bfl_model.lower():
                    # Flux Dev models
                    alternatives = [
                        "https://api.bfl.ai/flux-dev",
                        "https://api.bfl.ai/v1/flux-dev",
                    ]
                
                success = False
                for alt_url in alternatives:
                    if alt_url != api_url:
                        try:
                            logger.info(f"Trying alternative endpoint: {alt_url}")
                            alt_response = self.client.post(alt_url, headers=headers, json=payload)
                            if alt_response.status_code in [200, 201, 202]:  # Success codes
                                response = alt_response
                                api_url = alt_url
                                success = True
                                logger.info(f"Successfully connected to: {alt_url}")
                                break
                        except Exception as e:
                            logger.debug(f"Alternative endpoint failed: {alt_url}, error: {e}")
                            continue
                
                if not success:
                    # If all alternatives failed, raise the original 404
                    response.raise_for_status()
            
            response.raise_for_status()
            
            # Log successful submission
            submission_data = response.json()
            logger.info(f"BFL API request submitted successfully. Response keys: {list(submission_data.keys())}")
            
            # If image was provided, verify it was accepted
            if request.source_image_url:
                logger.info("Source image was included in the request")
            polling_url = submission_data.get("polling_url")
            
            if not polling_url:
                raise ValueError("No polling_url received from BFL API")
            
            # Step 2: Poll for results
            max_attempts = 120  # 60 seconds max (0.5s * 120)
            attempt = 0
            
            while attempt < max_attempts:
                time.sleep(0.5)  # Poll every 0.5 seconds
                attempt += 1
                
                result_response = self.client.get(
                    polling_url,
                    headers={"accept": "application/json", "x-key": self.api_key}
                )
                result_response.raise_for_status()
                result_data = result_response.json()
                
                status = result_data.get("status")
                
                if status == "Ready":
                    # Extract image URLs
                    result_obj = result_data.get("result", {})
                    images = []
                    
                    # Handle single image or multiple images
                    sample = result_obj.get("sample")
                    if sample:
                        if isinstance(sample, list):
                            images = [{"url": url} for url in sample]
                        else:
                            images = [{"url": sample}]
                    
                    return ImageGenerationResult(
                        success=True,
                        images=images,
                        provider=self.provider_name,
                        model=self.model,
                        metadata={
                            "bfl_polling_url": polling_url,
                            "bfl_status": status,
                        }
                    )
                
                elif status in ["Error", "Failed"]:
                    error_msg = result_data.get("error", "Generation failed")
                    logger.error(f"BFL generation failed: {error_msg}")
                    return ImageGenerationResult(
                        success=False,
                        images=[],
                        provider=self.provider_name,
                        model=self.model,
                        error=f"BFL API error: {error_msg}"
                    )
                
                # Continue polling if status is "Processing" or similar
                if attempt >= max_attempts:
                    return ImageGenerationResult(
                        success=False,
                        images=[],
                        provider=self.provider_name,
                        model=self.model,
                        error="BFL API timeout - generation took too long"
                    )
            
            return ImageGenerationResult(
                success=False,
                images=[],
                provider=self.provider_name,
                model=self.model,
                error="BFL API polling exceeded maximum attempts"
            )
            
        except requests.exceptions.RequestException as e:
            logger.error(f"BFL API request failed: {e}")
            return ImageGenerationResult(
                success=False,
                images=[],
                provider=self.provider_name,
                model=self.model,
                error=f"BFL API request error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"BFL generation failed: {e}")
            return ImageGenerationResult(
                success=False,
                images=[],
                provider=self.provider_name,
                model=self.model,
                error=str(e)
            )
    
    def _get_bfl_aspect_ratio(self, width: int, height: int) -> str:
        """Convert width/height to BFL aspect ratio string"""
        # BFL supports common aspect ratios
        ratio = width / height
        
        if abs(ratio - 1.0) < 0.1:
            return "1:1"
        elif abs(ratio - 16/9) < 0.1:
            return "16:9"
        elif abs(ratio - 9/16) < 0.1:
            return "9:16"
        elif abs(ratio - 4/3) < 0.1:
            return "4:3"
        elif abs(ratio - 3/4) < 0.1:
            return "3:4"
        elif abs(ratio - 21/9) < 0.1:
            return "21:9"
        else:
            # Default to 1:1 if ratio doesn't match
            return "1:1"
    
    def _generate_fal(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        """Generate via Fal.ai"""
        import fal_client
        
        # Build prompt with negative prompt
        full_prompt = request.prompt
        if request.negative_prompt:
            full_prompt = f"{request.prompt} --neg {request.negative_prompt}"
        
        # Map model names
        model_map = {
            "flux-schnell": "fal-ai/flux/schnell",
            "flux-dev": "fal-ai/flux/dev",
            "flux-pro": "fal-ai/flux/pro",
        }
        fal_model = model_map.get(self.model, f"fal-ai/flux/{self.model}")
        
        # Prepare parameters
        params = {
            "prompt": full_prompt,
            "image_size": f"{request.width}x{request.height}",
            "num_inference_steps": request.steps or 28,
            "guidance_scale": request.guidance_scale or 3.5,
        }
        
        if request.seed is not None:
            params["seed"] = request.seed
        
        # Handle img2img
        if request.source_image_url:
            params["image_url"] = request.source_image_url
            params["strength"] = request.strength or 0.8
        
        # Generate
        result = fal_client.run(fal_model, arguments=params)
        
        # Parse result
        images = []
        if "images" in result:
            for img in result["images"]:
                images.append({"url": img.get("url"), "content_type": img.get("content_type")})
        elif "image" in result:
            images.append({"url": result["image"].get("url")})
        
        return ImageGenerationResult(
            success=True,
            images=images,
            provider=self.provider_name,
            model=self.model,
            metadata={"fal_result": result}
        )
    
    def _generate_together(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        """Generate via Together.ai"""
        import together
        
        # Together API for Flux
        model_name = f"black-forest-labs/{self.model}"
        
        # Prepare parameters
        params = {
            "prompt": request.prompt,
            "width": request.width,
            "height": request.height,
            "steps": request.steps or 28,
            "cfg_scale": request.guidance_scale or 3.5,
        }
        
        if request.negative_prompt:
            params["negative_prompt"] = request.negative_prompt
        
        if request.seed is not None:
            params["seed"] = request.seed
        
        # Generate via Together API
        # Note: Together API structure may vary - this is a template
        try:
            response = together.Images.generate(
                model=model_name,
                prompt=request.prompt,
                **params
            )
            
            # Parse response (structure may vary)
            images = []
            if "output" in response and "choices" in response["output"]:
                for choice in response["output"]["choices"]:
                    if "image_base64" in choice:
                        images.append({"url": choice["image_base64"]})
            elif "images" in response:
                images = [{"url": url} for url in response["images"]]
        except Exception as e:
            logger.error(f"Together API call failed: {e}")
            raise
        
        return ImageGenerationResult(
            success=True,
            images=images,
            provider=self.provider_name,
            model=self.model,
            metadata={"together_response": response}
        )
    
    def _generate_replicate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        """Generate via Replicate"""
        import replicate
        
        # Replicate model names
        model_map = {
            "flux-schnell": "black-forest-labs/flux-schnell",
            "flux-dev": "black-forest-labs/flux-dev",
            "flux-pro": "black-forest-labs/flux-pro",
        }
        replicate_model = model_map.get(self.model, f"black-forest-labs/{self.model}")
        
        # Prepare parameters
        params = {
            "prompt": request.prompt,
            "width": request.width,
            "height": request.height,
            "num_outputs": request.num_images,
        }
        
        if request.negative_prompt:
            params["negative_prompt"] = request.negative_prompt
        
        if request.seed is not None:
            params["seed"] = request.seed
        
        if request.steps:
            params["num_inference_steps"] = request.steps
        
        if request.guidance_scale:
            params["guidance_scale"] = request.guidance_scale
        
        # Generate
        output = replicate.run(replicate_model, input=params)
        
        images = []
        if isinstance(output, list):
            for url in output:
                images.append({"url": url})
        else:
            images.append({"url": output})
        
        return ImageGenerationResult(
            success=True,
            images=images,
            provider=self.provider_name,
            model=self.model,
            metadata={"replicate_output": output}
        )
    
    def get_supported_features(self) -> Dict[str, bool]:
        """Flux supports many features depending on host"""
        base_features = {
            "img2img": True,
            "inpainting": self.host in ["fal", "replicate"],
            "upscaling": self.host in ["fal"],
            "variations": True,
            "seeds": True,
            "negative_prompts": True,
            "control_net": self.host in ["fal"],
        }
        return base_features
    
    def get_default_parameters(self, style: Optional[ImageStyle] = None) -> Dict[str, Any]:
        """Get default parameters based on style"""
        defaults = {
            "width": 1024,
            "height": 1024,
            "steps": 28,
            "guidance_scale": 3.5,
        }
        
        if style == ImageStyle.FAST_DRAFT:
            defaults["steps"] = 4
            defaults["guidance_scale"] = 1.0
        elif style == ImageStyle.PHOTOREAL:
            defaults["steps"] = 50
            defaults["guidance_scale"] = 7.0
        
        return defaults

