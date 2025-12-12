"""
Image Provider Router - Selects appropriate provider based on style, features, and config
"""

import json
import os
from typing import Dict, Optional, Any
from pathlib import Path
from enum import Enum
import logging

from image_provider import (
    ImageProvider, ImageStyle, ImageGenerationRequest,
    OpenAIImagesProvider, FluxProvider
)
from config import Config

# Import ComfyUI provider (optional - only if available)
try:
    from comfyui_provider import ComfyUIProvider
    COMFYUI_AVAILABLE = True
except ImportError:
    COMFYUI_AVAILABLE = False
    ComfyUIProvider = None

logger = logging.getLogger("flux_prompt")


class ImageProviderRouter:
    """Routes image generation requests to appropriate providers"""
    
    def __init__(self, config: Config, routing_config_path: str = "image_routing_config.json"):
        self.config = config
        self.routing_config_path = routing_config_path
        self.providers: Dict[str, ImageProvider] = {}
        self.routing_rules = self._load_routing_config()
        self._initialize_providers()
    
    def _load_routing_config(self) -> Dict[str, Any]:
        """Load routing configuration from JSON file"""
        config_path = Path(__file__).parent / self.routing_config_path
        
        if not config_path.exists():
            logger.warning(f"Routing config not found at {config_path}. Using defaults.")
            return self._get_default_routing_config()
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load routing config: {e}. Using defaults.")
            return self._get_default_routing_config()
    
    def _get_default_routing_config(self) -> Dict[str, Any]:
        """Default routing configuration"""
        return {
            "default_provider": "comfyui",
            "style_routing": {
                "fast_draft": {
                    "provider": "comfyui",
                    "model": "sd_xl_base_1.0.safetensors",
                    "priority": 1,
                    "note": "Using SDXL via ComfyUI for fast generation"
                },
                "photoreal": {
                    "provider": "comfyui",
                    "model": "sd_xl_base_1.0.safetensors",
                    "priority": 1
                },
                "brand_layout": {
                    "provider": "openai",
                    "priority": 1
                },
                "logo_text": {
                    "provider": "openai",
                    "priority": 1
                },
                "portrait": {
                    "provider": "comfyui",
                    "model": "sd_xl_base_1.0.safetensors",
                    "priority": 1
                },
                "product": {
                    "provider": "openai",
                    "priority": 1
                },
                "artistic": {
                    "provider": "comfyui",
                    "model": "sd_xl_base_1.0.safetensors",
                    "priority": 1
                },
                "cinematic": {
                    "provider": "comfyui",
                    "model": "sd_xl_base_1.0.safetensors",
                    "priority": 1
                }
            },
            "feature_routing": {
                "img2img": {
                    "provider": "comfyui",
                    "model": "sd_xl_base_1.0.safetensors",
                    "required": True
                },
                "inpainting": {
                    "provider": "comfyui",
                    "model": "sd_xl_base_1.0.safetensors",
                    "required": True
                },
                "negative_prompts": {
                    "provider": "comfyui",
                    "required": False
                },
                "seeds": {
                    "provider": "comfyui",
                    "required": False
                }
            },
            "fallback_chain": ["comfyui", "flux", "openai"]
        }
    
    def _initialize_providers(self):
        """Initialize available providers"""
        # OpenAI provider (always available)
        if self.config.get_openai_api_key():
            try:
                self.providers["openai"] = OpenAIImagesProvider(self.config.get_openai_api_key())
                logger.info("OpenAI Images provider initialized")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI provider: {e}")
        
        # Flux provider (if API key available)
        if self.config.get_flux_api_key():
            try:
                flux_host = self.config.get_flux_host()
                # Default model based on host - BFL pro for direct API
                # Note: BFL API uses flux-pro-1.1 endpoint, not flux1.1-pro
                default_model = "flux-pro" if flux_host == "bfl" else "flux-dev"
                flux_provider = FluxProvider(
                    api_key=self.config.get_flux_api_key(),
                    host=flux_host,
                    model=default_model
                )
                self.providers["flux"] = flux_provider
                logger.info(f"Flux provider initialized (host: {flux_host}, model: {default_model})")
            except Exception as e:
                logger.error(f"Failed to initialize Flux provider: {e}")
        
        # ComfyUI provider (if server is reachable)
        if COMFYUI_AVAILABLE:
            try:
                comfyui_server = self.config.get_comfyui_server_address()
                # Check if server is reachable
                if self._check_comfyui_server(comfyui_server):
                    comfyui_provider = ComfyUIProvider(
                        server_address=comfyui_server,
                        workflow_dir=self.config.get_comfyui_workflow_dir(),
                        temp_dir=self.config.get_comfyui_temp_dir()
                    )
                    self.providers["comfyui"] = comfyui_provider
                    logger.info(f"ComfyUI provider initialized (server: {comfyui_server})")
                else:
                    logger.warning(f"ComfyUI server not reachable at {comfyui_server}. Skipping ComfyUI provider.")
            except Exception as e:
                logger.warning(f"Failed to initialize ComfyUI provider: {e}")
    
    def _check_comfyui_server(self, server_address: str) -> bool:
        """
        Check if ComfyUI server is reachable
        
        Args:
            server_address: Server address (e.g., "127.0.0.1:8188")
            
        Returns:
            True if server is reachable, False otherwise
        """
        try:
            import urllib.request
            import urllib.error
            
            # Try multiple endpoints for better compatibility
            endpoints = [
                "/system_stats",
                "/prompt",  # Some ComfyUI versions might not have system_stats
                "/"  # Root endpoint
            ]
            
            for endpoint in endpoints:
                try:
                    url = f"http://{server_address}{endpoint}"
                    req = urllib.request.Request(url)
                    # Use HEAD request for root to avoid downloading
                    if endpoint == "/":
                        req.get_method = lambda: "HEAD"
                    urllib.request.urlopen(req, timeout=3)
                    logger.info(f"ComfyUI server reachable at {server_address} (checked {endpoint})")
                    return True
                except (urllib.error.URLError, urllib.error.HTTPError):
                    continue
            
            return False
        except Exception as e:
            logger.debug(f"ComfyUI server check failed: {e}")
            return False
    
    def select_provider(self, request: ImageGenerationRequest) -> Optional[ImageProvider]:
        """
        Select appropriate provider based on request and routing rules
        
        Args:
            request: Image generation request
            
        Returns:
            Selected provider or None if no suitable provider found
        """
        # Check for explicit provider override
        if request.provider:
            return self.providers.get(request.provider)
        
        # Check feature requirements
        feature_routing = self.routing_rules.get("feature_routing", {})
        
        if request.source_image_url and "img2img" in feature_routing:
            img2img_config = feature_routing["img2img"]
            provider_name = img2img_config.get("provider")
            if provider_name in self.providers:
                provider = self.providers[provider_name]
                if isinstance(provider, FluxProvider):
                    # Use Flux Kontext for image editing
                    kontext_model = img2img_config.get("model", "flux-kontext-pro")
                    provider.model = kontext_model
                    logger.info(f"Using {kontext_model} for image editing")
                return provider
        
        if request.mask_image_url and "inpainting" in feature_routing:
            inpainting_config = feature_routing["inpainting"]
            provider_name = inpainting_config.get("provider")
            if provider_name in self.providers:
                return self.providers[provider_name]
        
        # Check style-based routing
        if request.style:
            style_routing = self.routing_rules.get("style_routing", {})
            style_name = request.style.value
            
            if style_name in style_routing:
                style_config = style_routing[style_name]
                provider_name = style_config.get("provider")
                
                if provider_name in self.providers:
                    provider = self.providers[provider_name]
                    
                    # Update Flux model if specified
                    if isinstance(provider, FluxProvider) and "model" in style_config:
                        provider.model = style_config["model"]
                    
                    return provider
        
        # Use default provider
        default_provider = self.routing_rules.get("default_provider", "openai")
        return self.providers.get(default_provider)
    
    def generate(self, request: ImageGenerationRequest) -> Any:
        """
        Generate image using appropriate provider
        
        Args:
            request: Image generation request
            
        Returns:
            ImageGenerationResult
        """
        provider = self.select_provider(request)
        
        if not provider:
            fallback_chain = self.routing_rules.get("fallback_chain", ["openai"])
            for provider_name in fallback_chain:
                if provider_name in self.providers:
                    provider = self.providers[provider_name]
                    logger.warning(f"Using fallback provider: {provider_name}")
                    break
            
            if not provider:
                from image_provider import ImageGenerationResult
                return ImageGenerationResult(
                    success=False,
                    images=[],
                    provider="unknown",
                    model="unknown",
                    error="No available image providers"
                )
        
        logger.info(f"Using provider: {provider.provider_name} (model: {getattr(provider, 'model', 'N/A')})")
        return provider.generate(request)
    
    def get_available_providers(self) -> Dict[str, Dict[str, Any]]:
        """Get list of available providers with their capabilities"""
        available = {}
        
        for name, provider in self.providers.items():
            available[name] = {
                "provider": provider.provider_name,
                "model": getattr(provider, 'model', 'N/A'),
                "features": provider.get_supported_features(),
            }
        
        return available
    
    def save_routing_config(self):
        """Save current routing config to file"""
        config_path = Path(__file__).parent / self.routing_config_path
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.routing_rules, f, indent=2, ensure_ascii=False)
            logger.info(f"Routing config saved to {config_path}")
        except Exception as e:
            logger.error(f"Failed to save routing config: {e}")

