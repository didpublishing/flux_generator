"""
Image Generator Service - High-level interface for image generation
Handles prompt templates, caching, and result management
"""

import hashlib
import json
import os
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from datetime import datetime
import logging

from image_provider import (
    ImageGenerationRequest, ImageGenerationResult, ImageStyle
)
from image_provider_router import ImageProviderRouter
from config import Config

logger = logging.getLogger("flux_prompt")

# Import ImageVault for automatic saving
try:
    from image_vault import ImageVault
    VAULT_AVAILABLE = True
except ImportError:
    VAULT_AVAILABLE = False
    logger.warning("ImageVault not available")


class ImageGenerator:
    """High-level image generation service with templates and caching"""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.router = ImageProviderRouter(self.config)
        self.cache_dir = Path("cache/images")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Image Vault for automatic saving
        if VAULT_AVAILABLE:
            try:
                self.vault = ImageVault()
                logger.info("Image Vault initialized")
            except Exception as e:
                logger.warning(f"Image Vault not available: {e}")
                self.vault = None
        else:
            self.vault = None
        
        # Prompt templates for different styles
        self.prompt_templates = {
            ImageStyle.PRODUCT: "E-commerce product photo on seamless white, soft studio light, crisp details, professional photography, {prompt}",
            ImageStyle.PORTRAIT: "Natural light portrait, shallow depth of field, realistic skin, 50mm lens, professional photography, {prompt}",
            ImageStyle.LOGO_TEXT: "Minimal vector logo, high legibility typography, flat design, SVG look, clean background, {prompt}",
            ImageStyle.BRAND_LAYOUT: "Brand visual design, clean layout, professional composition, marketing material, {prompt}",
            ImageStyle.PHOTOREAL: "Photorealistic, highly detailed, professional photography, 8k resolution, {prompt}",
            ImageStyle.CINEMATIC: "Cinematic lighting, dramatic composition, film photography, cinematic quality, {prompt}",
        }
        
        # Default negative prompts
        self.default_negative_prompts = {
            "general": "blurry, low quality, distorted, watermark, text, signature, bad anatomy, extra limbs",
            "photoreal": "cartoon, illustration, painting, drawing, anime, 3d render",
            "product": "cluttered background, shadows, reflections, busy composition",
        }
    
    def generate(
        self,
        prompt: str,
        style: Optional[Union[str, ImageStyle]] = None,
        width: int = 1024,
        height: int = 1024,
        seed: Optional[int] = None,
        num_images: int = 1,
        negative_prompt: Optional[str] = None,
        source_image_url: Optional[str] = None,
        mask_image_url: Optional[str] = None,
        strength: Optional[float] = None,
        use_cache: bool = True,
        **kwargs
    ) -> ImageGenerationResult:
        """
        Generate image(s) from prompt
        
        Args:
            prompt: Image generation prompt
            style: Image style (string or ImageStyle enum)
            width: Image width in pixels
            height: Image height in pixels
            seed: Random seed for reproducibility
            num_images: Number of images to generate
            negative_prompt: Negative prompt (what to avoid)
            source_image_url: Source image URL for img2img
            mask_image_url: Mask image URL for inpainting
            strength: Strength for img2img (0.0-1.0)
            use_cache: Whether to use cached results
            **kwargs: Additional provider-specific parameters
            
        Returns:
            ImageGenerationResult
        """
        # Convert string style to enum
        if isinstance(style, str):
            try:
                style = ImageStyle(style)
            except ValueError:
                logger.warning(f"Unknown style: {style}. Using None.")
                style = None
        
        # Apply prompt template
        final_prompt = self._apply_template(prompt, style)
        
        # Build negative prompt
        final_negative = self._build_negative_prompt(negative_prompt, style)
        
        # Check cache
        if use_cache and not source_image_url and not mask_image_url:
            cache_key = self._generate_cache_key(final_prompt, final_negative, width, height, seed, style)
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                logger.info("Returning cached image")
                return cached_result
        
        # Create request
        request = ImageGenerationRequest(
            prompt=final_prompt,
            negative_prompt=final_negative,
            width=width,
            height=height,
            seed=seed,
            num_images=num_images,
            style=style,
            source_image_url=source_image_url,
            mask_image_url=mask_image_url,
            strength=strength,
            provider=kwargs.get("provider"),
            **{k: v for k, v in kwargs.items() if k != "provider" and k != "model"}
        )
        
        # Handle model override for Flux provider
        if "model" in kwargs and request.source_image_url:
            # Force Flux Kontext for image editing
            request.provider = request.provider or "flux"
        
        # Generate
        result = self.router.generate(request)
        
        # Cache result if successful
        if use_cache and result.success and not source_image_url and not mask_image_url:
            self._save_to_cache(cache_key, result)
        
        # Automatically save to vault if successful
        if result.success and self.vault and result.get_image_url(0):
            try:
                source_type = "edited" if (source_image_url or mask_image_url) else "generated"
                vault_prompt = prompt if not source_image_url else f"Edit: {prompt}"
                self.vault.save_image(
                    image_url=result.get_image_url(0),
                    prompt=vault_prompt,
                    provider=result.provider,
                    model=result.model,
                    style=style.value if style else None,
                    metadata={
                        "width": width,
                        "height": height,
                        "seed": seed,
                        "negative_prompt": negative_prompt,
                        "strength": strength,
                        **(result.metadata or {})
                    },
                    source_type=source_type
                )
                logger.info(f"Image automatically saved to vault (provider: {result.provider})")
            except Exception as e:
                logger.warning(f"Failed to auto-save image to vault: {e}")
        
        return result
    
    def _apply_template(self, prompt: str, style: Optional[ImageStyle]) -> str:
        """Apply prompt template based on style"""
        if style and style in self.prompt_templates:
            template = self.prompt_templates[style]
            return template.format(prompt=prompt)
        return prompt
    
    def _build_negative_prompt(self, user_negative: Optional[str], style: Optional[ImageStyle]) -> Optional[str]:
        """Build negative prompt from defaults and user input"""
        negatives = []
        
        # Add general negative
        negatives.append(self.default_negative_prompts["general"])
        
        # Add style-specific negatives
        if style == ImageStyle.PHOTOREAL:
            negatives.append(self.default_negative_prompts["photoreal"])
        elif style == ImageStyle.PRODUCT:
            negatives.append(self.default_negative_prompts["product"])
        
        # Add user negative
        if user_negative:
            negatives.append(user_negative)
        
        return ", ".join(negatives) if negatives else None
    
    def _generate_cache_key(
        self,
        prompt: str,
        negative_prompt: Optional[str],
        width: int,
        height: int,
        seed: Optional[int],
        style: Optional[ImageStyle]
    ) -> str:
        """Generate cache key from parameters"""
        cache_string = f"{prompt}|{negative_prompt}|{width}x{height}|{seed}|{style}"
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[ImageGenerationResult]:
        """Get result from cache"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Reconstruct result (simplified - may need image URL fetching)
            return ImageGenerationResult(
                success=data["success"],
                images=data["images"],
                provider=data["provider"],
                model=data["model"],
                error=data.get("error"),
                metadata=data.get("metadata"),
            )
        except Exception as e:
            logger.warning(f"Failed to load from cache: {e}")
            return None
    
    def _save_to_cache(self, cache_key: str, result: ImageGenerationResult):
        """Save result to cache"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            data = {
                "success": result.success,
                "images": result.images,
                "provider": result.provider,
                "model": result.model,
                "error": result.error,
                "metadata": result.metadata,
                "cached_at": datetime.now().isoformat(),
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Failed to save to cache: {e}")
    
    def get_available_styles(self) -> List[str]:
        """Get list of available image styles"""
        return [style.value for style in ImageStyle]
    
    def get_available_providers(self) -> Dict[str, Any]:
        """Get available providers and their capabilities"""
        return self.router.get_available_providers()
    
    def generate_from_flux_prompt(self, flux_prompt: str, style: Optional[str] = None, **kwargs) -> ImageGenerationResult:
        """
        Generate image directly from a Flux-optimized prompt
        
        Args:
            flux_prompt: Pre-optimized Flux prompt
            style: Optional style override
            **kwargs: Additional generation parameters
            
        Returns:
            ImageGenerationResult
        """
        # Don't apply templates since prompt is already optimized
        style_enum = ImageStyle(style) if style else None
        
        request = ImageGenerationRequest(
            prompt=flux_prompt,
            width=kwargs.get("width", 1024),
            height=kwargs.get("height", 1024),
            seed=kwargs.get("seed"),
            num_images=kwargs.get("num_images", 1),
            style=style_enum,
            negative_prompt=kwargs.get("negative_prompt"),
        )
        
        return self.router.generate(request)

