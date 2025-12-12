"""
ComfyUI Image Generation Provider
Supports dynamic workflow JSON manipulation and execution via ComfyUI API
"""

import json
import os
import uuid
import time
import urllib.request
import urllib.parse
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from io import BytesIO
import logging

try:
    import websocket
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False

from PIL import Image
import requests

from image_provider import ImageProvider, ImageGenerationRequest, ImageGenerationResult, ImageStyle

logger = logging.getLogger("flux_prompt")


class ComfyUIProvider(ImageProvider):
    """ComfyUI provider for local ComfyUI installation"""
    
    def __init__(
        self,
        server_address: str = "127.0.0.1:8188",
        workflow_dir: str = "workflows/comfyui",
        temp_dir: str = "temp_uploads",
        client_id: Optional[str] = None
    ):
        """
        Initialize ComfyUI provider
        
        Args:
            server_address: ComfyUI server address (default: 127.0.0.1:8188)
            workflow_dir: Directory containing workflow JSON files
            temp_dir: Directory for temporary image uploads
            client_id: Client ID for WebSocket connection (auto-generated if None)
        """
        self.server_address = server_address
        self.workflow_dir = Path(workflow_dir)
        self.temp_dir = Path(temp_dir)
        self.client_id = client_id or str(uuid.uuid4())
        self.provider_name = "comfyui"
        self.model = "comfyui-local"
        
        # Create directories if they don't exist
        self.workflow_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Default workflow paths
        self.default_t2i_workflow = self.workflow_dir / "t2i_flux.json"
        self.default_i2i_workflow = self.workflow_dir / "i2i_flux.json"
        
        # Cache available models
        self.available_models = None
        
        # Validate workflows on initialization
        self._validate_workflows()
        
        logger.info(f"ComfyUI provider initialized (server: {server_address})")
    
    def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        """
        Generate image using ComfyUI
        
        Args:
            request: Image generation request
            
        Returns:
            ImageGenerationResult
        """
        try:
            # Determine workflow type
            is_i2i = request.source_image_url is not None
            workflow_path = self.default_i2i_workflow if is_i2i else self.default_t2i_workflow
            
            # Check if workflow exists
            if not workflow_path.exists():
                return ImageGenerationResult(
                    success=False,
                    images=[],
                    provider=self.provider_name,
                    model=self.model,
                    error=f"Workflow file not found: {workflow_path}. Please create workflow JSON files."
                )
            
            # Validate workflow model before execution
            is_valid, error_msg = self.validate_workflow_model(str(workflow_path))
            if not is_valid:
                return ImageGenerationResult(
                    success=False,
                    images=[],
                    provider=self.provider_name,
                    model=self.model,
                    error=error_msg or "Workflow validation failed"
                )
            
            # Execute workflow
            return self.execute_comfy_workflow(
                workflow_file_path=str(workflow_path),
                pos_prompt=request.prompt,
                neg_prompt=request.negative_prompt or "",
                seed=request.seed,
                steps=request.steps or 28,
                cfg=request.guidance_scale or 3.5,
                width=request.width,
                height=request.height,
                input_image_path=request.source_image_url,
                denoise_weight=request.strength or 0.7 if request.strength else None,
                mode_switch_value="I2I" if is_i2i else "T2I"
            )
            
        except Exception as e:
            logger.error(f"ComfyUI generation failed: {e}", exc_info=True)
            return ImageGenerationResult(
                success=False,
                images=[],
                provider=self.provider_name,
                model=self.model,
                error=str(e)
            )
    
    def execute_comfy_workflow(
        self,
        workflow_file_path: str,
        pos_prompt: str,
        neg_prompt: str = "",
        seed: Optional[int] = None,
        steps: int = 28,
        cfg: float = 3.5,
        width: int = 1024,
        height: int = 1024,
        input_image_path: Optional[str] = None,
        denoise_weight: Optional[float] = None,
        mode_switch_value: str = "T2I"
    ) -> ImageGenerationResult:
        """
        Execute a ComfyUI workflow with dynamic parameter injection
        
        Args:
            workflow_file_path: Path to workflow JSON file
            pos_prompt: Positive prompt
            neg_prompt: Negative prompt
            seed: Random seed
            steps: Number of steps
            cfg: CFG scale
            width: Image width
            height: Image height
            input_image_path: Path to input image for I2I (optional)
            denoise_weight: Denoise strength for I2I (0.0-1.0)
            mode_switch_value: Mode switch value ("T2I" or "I2I")
            
        Returns:
            ImageGenerationResult
        """
        try:
            # Load workflow JSON
            with open(workflow_file_path, 'r', encoding='utf-8') as f:
                workflow_json = json.load(f)
            
            # Handle image upload for I2I
            uploaded_filename = None
            if input_image_path:
                uploaded_filename = self.upload_image(input_image_path)
                if not uploaded_filename:
                    raise ValueError(f"Failed to upload input image: {input_image_path}")
            
            # Find and update nodes
            self._inject_parameters(
                workflow_json,
                pos_prompt=pos_prompt,
                neg_prompt=neg_prompt,
                seed=seed,
                steps=steps,
                cfg=cfg,
                width=width,
                height=height,
                uploaded_filename=uploaded_filename,
                denoise_weight=denoise_weight,
                mode_switch_value=mode_switch_value
            )
            
            # Queue prompt
            prompt_id = str(uuid.uuid4())
            self.queue_prompt(workflow_json, prompt_id)
            
            # Wait for completion and retrieve images
            images = self.wait_for_completion(prompt_id)
            
            if not images:
                return ImageGenerationResult(
                    success=False,
                    images=[],
                    provider=self.provider_name,
                    model=self.model,
                    error="No images generated or timeout occurred"
                )
            
            # Format images for result
            image_results = []
            for img_data in images:
                image_results.append({
                    "bytes": img_data,
                    "url": None  # ComfyUI returns binary data
                })
            
            return ImageGenerationResult(
                success=True,
                images=image_results,
                provider=self.provider_name,
                model=self.model,
                metadata={
                    "prompt_id": prompt_id,
                    "workflow": workflow_file_path,
                    "width": width,
                    "height": height,
                    "steps": steps,
                    "cfg": cfg,
                    "seed": seed
                }
            )
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)
            return ImageGenerationResult(
                success=False,
                images=[],
                provider=self.provider_name,
                model=self.model,
                error=str(e)
            )
    
    def _inject_parameters(
        self,
        workflow_json: Dict[str, Any],
        pos_prompt: str,
        neg_prompt: str = "",
        seed: Optional[int] = None,
        steps: int = 28,
        cfg: float = 3.5,
        width: int = 1024,
        height: int = 1024,
        uploaded_filename: Optional[str] = None,
        denoise_weight: Optional[float] = None,
        mode_switch_value: str = "T2I"
    ):
        """
        Inject parameters into workflow JSON
        
        Args:
            workflow_json: Workflow JSON dictionary
            pos_prompt: Positive prompt
            neg_prompt: Negative prompt
            seed: Random seed
            steps: Number of steps
            cfg: CFG scale
            width: Image width
            height: Image height
            uploaded_filename: Uploaded image filename (for I2I)
            denoise_weight: Denoise strength (for I2I)
            mode_switch_value: Mode switch value
        """
        # Find CLIPTextEncode nodes (positive and negative prompts)
        # Support both standard CLIPTextEncode and SDXL-specific nodes
        text_encode_types = ["CLIPTextEncodeSDXL", "CLIPTextEncodeSDXLRefiner", "CLIPTextEncode"]
        
        pos_text_node = None
        for encode_type in text_encode_types:
            pos_text_node = self.find_node_by_class_type(workflow_json, encode_type)
            if pos_text_node:
                break
        
        if pos_text_node:
            # Find the first text encode node for positive prompt
            # (ComfyUI workflows typically have positive before negative)
            if "text" in workflow_json[pos_text_node]["inputs"]:
                workflow_json[pos_text_node]["inputs"]["text"] = pos_prompt
            elif "text_g" in workflow_json[pos_text_node]["inputs"]:
                # SDXL nodes may have text_g (base) and text_l (refiner) inputs
                workflow_json[pos_text_node]["inputs"]["text_g"] = pos_prompt
                if "text_l" in workflow_json[pos_text_node]["inputs"]:
                    workflow_json[pos_text_node]["inputs"]["text_l"] = pos_prompt
        
        # Find second text encode node for negative prompt
        pos_node_id = pos_text_node
        neg_text_node = None
        for node_id, node_data in workflow_json.items():
            node_type = node_data.get("class_type")
            if (node_type in text_encode_types and node_id != pos_node_id):
                neg_text_node = node_id
                break
        
        if neg_text_node and neg_prompt:
            if "text" in workflow_json[neg_text_node]["inputs"]:
                workflow_json[neg_text_node]["inputs"]["text"] = neg_prompt
            elif "text_g" in workflow_json[neg_text_node]["inputs"]:
                workflow_json[neg_text_node]["inputs"]["text_g"] = neg_prompt
                if "text_l" in workflow_json[neg_text_node]["inputs"]:
                    workflow_json[neg_text_node]["inputs"]["text_l"] = neg_prompt
        
        # Find KSampler node
        sampler_node = self.find_node_by_class_type(workflow_json, "KSampler")
        if sampler_node:
            if seed is not None:
                workflow_json[sampler_node]["inputs"]["seed"] = seed
            workflow_json[sampler_node]["inputs"]["steps"] = steps
            workflow_json[sampler_node]["inputs"]["cfg"] = cfg
            
            # Set denoise for I2I
            if denoise_weight is not None:
                workflow_json[sampler_node]["inputs"]["denoise"] = denoise_weight
        
        # Find EmptyLatentImage node (for T2I) and update dimensions
        # Support both standard EmptyLatentImage and SD3-specific EmptySD3LatentImage
        latent_node = self.find_node_by_class_type(workflow_json, "EmptyLatentImage")
        if not latent_node:
            latent_node = self.find_node_by_class_type(workflow_json, "EmptySD3LatentImage")
        if latent_node:
            workflow_json[latent_node]["inputs"]["width"] = width
            workflow_json[latent_node]["inputs"]["height"] = height
        
        # Find LoadImage node (for I2I) and update with uploaded image
        if uploaded_filename:
            load_image_node = self.find_node_by_class_type(workflow_json, "LoadImage")
            if load_image_node:
                # Update the image input - can be "image" or "filename" depending on workflow
                if "image" in workflow_json[load_image_node]["inputs"]:
                    workflow_json[load_image_node]["inputs"]["image"] = uploaded_filename
                elif "filename" in workflow_json[load_image_node]["inputs"]:
                    workflow_json[load_image_node]["inputs"]["filename"] = uploaded_filename
        
        # Find mode switch node (AnySwitch, Primitive, etc.)
        switch_node = self.find_node_by_class_type(workflow_json, "AnySwitch")
        if not switch_node:
            switch_node = self.find_node_by_class_type(workflow_json, "Primitive")
        
        if switch_node:
            # Update switch value based on mode
            if "value" in workflow_json[switch_node]["inputs"]:
                workflow_json[switch_node]["inputs"]["value"] = mode_switch_value
            elif "text" in workflow_json[switch_node]["inputs"]:
                workflow_json[switch_node]["inputs"]["text"] = mode_switch_value
            elif "select" in workflow_json[switch_node]["inputs"]:
                workflow_json[switch_node]["inputs"]["select"] = mode_switch_value
        
        # Custom node support: Qwen VLM node
        qwen_node = self.find_node_by_class_type(workflow_json, "Qwen2-VL-Instruct")
        if qwen_node:
            # Update Qwen query input if needed
            if "query" in workflow_json[qwen_node]["inputs"]:
                workflow_json[qwen_node]["inputs"]["query"] = pos_prompt
        
        # Custom node support: FluxGuidance node
        flux_guidance_node = self.find_node_by_class_type(workflow_json, "FluxGuidance")
        if flux_guidance_node:
            # FluxGuidance nodes typically have a "guidance" parameter
            if "guidance" in workflow_json[flux_guidance_node]["inputs"]:
                # Use CFG as guidance value
                workflow_json[flux_guidance_node]["inputs"]["guidance"] = cfg
    
    def find_node_by_class_type(self, workflow_json: Dict[str, Any], class_type: str) -> Optional[str]:
        """
        Find node ID by class type
        
        Args:
            workflow_json: Workflow JSON dictionary
            class_type: Class type to search for (e.g., "KSampler", "CLIPTextEncode")
            
        Returns:
            Node ID (string key) or None if not found
        """
        for node_id, node_data in workflow_json.items():
            if node_data.get("class_type") == class_type:
                return node_id
        return None
    
    def queue_prompt(self, prompt: Dict[str, Any], prompt_id: str):
        """
        Queue a prompt for execution
        
        Args:
            prompt: Workflow JSON dictionary
            prompt_id: Unique prompt ID
        """
        p = {"prompt": prompt, "client_id": self.client_id, "prompt_id": prompt_id}
        data = json.dumps(p).encode('utf-8')
        req = urllib.request.Request(
            f"http://{self.server_address}/prompt",
            data=data,
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req).read()
    
    def get_history(self, prompt_id: str) -> Dict[str, Any]:
        """
        Get execution history for a prompt
        
        Args:
            prompt_id: Prompt ID
            
        Returns:
            History dictionary
        """
        with urllib.request.urlopen(f"http://{self.server_address}/history/{prompt_id}") as response:
            return json.loads(response.read())
    
    def get_image(self, filename: str, subfolder: str = "", folder_type: str = "output") -> bytes:
        """
        Get image data from ComfyUI server
        
        Args:
            filename: Image filename
            subfolder: Subfolder name
            folder_type: Folder type (input, output, temp)
            
        Returns:
            Image bytes
        """
        data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        url_values = urllib.parse.urlencode(data)
        with urllib.request.urlopen(f"http://{self.server_address}/view?{url_values}") as response:
            return response.read()
    
    def upload_image(self, input_path: str) -> Optional[str]:
        """
        Upload an image to ComfyUI server
        
        Args:
            input_path: Path to image file (local file path or URL)
            
        Returns:
            Filename on server or None if failed
        """
        try:
            # Handle URL or file path
            if input_path.startswith("http://") or input_path.startswith("https://"):
                # Download image first
                response = requests.get(input_path)
                response.raise_for_status()
                img = Image.open(BytesIO(response.content))
                temp_path = self.temp_dir / f"upload_{uuid.uuid4().hex[:8]}.png"
                img.save(temp_path)
                input_path = str(temp_path)
            elif input_path.startswith("data:image"):
                # Handle base64 data URL
                import base64
                header, data = input_path.split(",", 1)
                img_data = base64.b64decode(data)
                img = Image.open(BytesIO(img_data))
                temp_path = self.temp_dir / f"upload_{uuid.uuid4().hex[:8]}.png"
                img.save(temp_path)
                input_path = str(temp_path)
            
            # Extract filename
            filename = os.path.basename(input_path)
            
            # Upload to ComfyUI
            with open(input_path, 'rb') as f:
                files = {'image': (filename, f, 'image/png')}
                data = {'overwrite': 'true'}
                response = requests.post(
                    f"http://{self.server_address}/upload/image",
                    files=files,
                    data=data
                )
                response.raise_for_status()
                result = response.json()
                return result.get("name", filename)
                
        except Exception as e:
            logger.error(f"Failed to upload image: {e}", exc_info=True)
            return None
    
    def wait_for_completion(self, prompt_id: str, timeout: int = 300) -> List[bytes]:
        """
        Wait for workflow execution to complete and retrieve images
        
        Args:
            prompt_id: Prompt ID
            timeout: Timeout in seconds (default: 300)
            
        Returns:
            List of image bytes
        """
        start_time = time.time()
        
        # Try WebSocket method first (more efficient)
        if WEBSOCKET_AVAILABLE:
            try:
                return self._wait_for_completion_websocket(prompt_id, timeout)
            except Exception as e:
                logger.warning(f"WebSocket method failed, falling back to polling: {e}")
        
        # Fallback to polling method
        while time.time() - start_time < timeout:
            time.sleep(0.5)  # Poll every 0.5 seconds
            
            try:
                history = self.get_history(prompt_id)
                
                if prompt_id in history:
                    prompt_data = history[prompt_id]
                    
                    # Check if execution completed
                    if "status" in prompt_data:
                        if prompt_data["status"] == "error":
                            error_msg = prompt_data.get("error", "Unknown error")
                            raise Exception(f"ComfyUI execution error: {error_msg}")
                    
                    # Extract images from outputs
                    if "outputs" in prompt_data:
                        images = []
                        for node_id, node_output in prompt_data["outputs"].items():
                            if "images" in node_output:
                                for image_info in node_output["images"]:
                                    img_data = self.get_image(
                                        image_info["filename"],
                                        image_info.get("subfolder", ""),
                                        image_info.get("type", "output")
                                    )
                                    images.append(img_data)
                        
                        if images:
                            return images
            
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    # Prompt not found yet, continue waiting
                    continue
                else:
                    raise
            except Exception as e:
                logger.debug(f"Polling error (will retry): {e}")
                continue
        
        raise TimeoutError(f"Workflow execution timed out after {timeout} seconds")
    
    def _wait_for_completion_websocket(self, prompt_id: str, timeout: int = 300) -> List[bytes]:
        """
        Wait for completion using WebSocket (more efficient)
        
        Args:
            prompt_id: Prompt ID
            timeout: Timeout in seconds
            
        Returns:
            List of image bytes
        """
        if not WEBSOCKET_AVAILABLE:
            raise ImportError("websocket-client not available")
        
        ws = websocket.WebSocket()
        try:
            ws.connect(f"ws://{self.server_address}/ws?clientId={self.client_id}")
            
            start_time = time.time()
            while time.time() - start_time < timeout:
                out = ws.recv(timeout=timeout)
                
                if isinstance(out, str):
                    message = json.loads(out)
                    if message.get('type') == 'executing':
                        data = message.get('data', {})
                        if data.get('node') is None and data.get('prompt_id') == prompt_id:
                            # Execution completed
                            break
                else:
                    # Binary data (previews), skip
                    continue
            
            # Retrieve images from history
            history = self.get_history(prompt_id)
            images = []
            
            if prompt_id in history:
                prompt_data = history[prompt_id]
                if "outputs" in prompt_data:
                    for node_id, node_output in prompt_data["outputs"].items():
                        if "images" in node_output:
                            for image_info in node_output["images"]:
                                img_data = self.get_image(
                                    image_info["filename"],
                                    image_info.get("subfolder", ""),
                                    image_info.get("type", "output")
                                )
                                images.append(img_data)
            
            return images
            
        finally:
            try:
                ws.close()
            except:
                pass
    
    def get_supported_features(self) -> Dict[str, bool]:
        """Return supported features"""
        return {
            "img2img": True,
            "inpainting": True,  # Depends on workflow
            "upscaling": True,  # Depends on workflow
            "variations": True,
            "seeds": True,
            "negative_prompts": True,
            "control_net": True,  # Depends on workflow
            "custom_nodes": True,
        }
    
    def get_default_parameters(self, style: Optional[ImageStyle] = None) -> Dict[str, Any]:
        """Get default parameters based on style"""
        defaults = {
            "width": 1024,
            "height": 1024,
            "steps": 28,
            "guidance_scale": 3.5,
        }
        
        if style == ImageStyle.FAST_DRAFT:
            defaults["steps"] = 20
            defaults["guidance_scale"] = 3.0
        elif style == ImageStyle.PHOTOREAL:
            defaults["steps"] = 50
            defaults["guidance_scale"] = 7.0
        
        return defaults
    
    def get_available_models(self) -> List[str]:
        """
        Get list of available models from ComfyUI
        Supports both CheckpointLoaderSimple and UNETLoader nodes
        
        Returns:
            List of model filenames
        """
        if self.available_models is not None:
            return self.available_models
        
        models = []
        
        try:
            with urllib.request.urlopen(f"http://{self.server_address}/object_info", timeout=5) as response:
                object_info = json.loads(response.read())
            
            # Extract checkpoint models from CheckpointLoaderSimple node
            checkpoint_loader = object_info.get("CheckpointLoaderSimple", {})
            if checkpoint_loader:
                input_spec = checkpoint_loader.get("input", {})
                required = input_spec.get("required", {})
                ckpt_name = required.get("ckpt_name", [])
                
                # Handle different response formats
                if isinstance(ckpt_name, list) and len(ckpt_name) > 0:
                    if isinstance(ckpt_name[0], list):
                        # Format: [["model1.safetensors", "model2.safetensors"], {...}]
                        models.extend(ckpt_name[0])
                    else:
                        # Format: ["model1.safetensors", "model2.safetensors"]
                        models.extend(ckpt_name)
            
            # Extract UNET models from UNETLoader node (for Flux/HiDream workflows)
            unet_loader = object_info.get("UNETLoader", {})
            if unet_loader:
                input_spec = unet_loader.get("input", {})
                required = input_spec.get("required", {})
                unet_name = required.get("unet_name", [])
                
                if isinstance(unet_name, list) and len(unet_name) > 0:
                    if isinstance(unet_name[0], list):
                        models.extend(unet_name[0])
                    else:
                        models.extend(unet_name)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_models = []
            for model in models:
                if model not in seen:
                    seen.add(model)
                    unique_models.append(model)
            
            self.available_models = unique_models
            logger.info(f"Found {len(unique_models)} available models: {', '.join(unique_models)}")
            return unique_models
            
        except Exception as e:
            logger.warning(f"Failed to get available models from ComfyUI: {e}")
            return []
    
    def _validate_workflows(self):
        """
        Validate that workflow files reference models that exist in ComfyUI
        """
        available_models = self.get_available_models()
        
        if not available_models:
            logger.warning("Could not retrieve available models from ComfyUI. Skipping workflow validation.")
            return
        
        workflows_to_check = [
            (self.default_t2i_workflow, "T2I"),
            (self.default_i2i_workflow, "I2I")
        ]
        
        for workflow_path, workflow_type in workflows_to_check:
            if not workflow_path.exists():
                continue
            
            try:
                with open(workflow_path, 'r', encoding='utf-8') as f:
                    workflow_json = json.load(f)
                
                # Find CheckpointLoaderSimple node
                checkpoint_node = self.find_node_by_class_type(workflow_json, "CheckpointLoaderSimple")
                model_name = None
                
                if checkpoint_node:
                    model_name = workflow_json[checkpoint_node]["inputs"].get("ckpt_name", "")
                else:
                    # Check for UNETLoader node (for Flux/HiDream workflows)
                    unet_node = self.find_node_by_class_type(workflow_json, "UNETLoader")
                    if unet_node:
                        model_name = workflow_json[unet_node]["inputs"].get("unet_name", "")
                
                if model_name:
                    if model_name not in available_models:
                        logger.error(
                            f"{workflow_type} workflow references model '{model_name}' which is not available. "
                            f"Available models: {', '.join(available_models)}"
                        )
                    else:
                        logger.debug(f"{workflow_type} workflow validated: using model '{model_name}'")
                        
            except Exception as e:
                logger.warning(f"Failed to validate {workflow_type} workflow {workflow_path}: {e}")
    
    def validate_workflow_model(self, workflow_file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that a workflow file references an available model
        
        Args:
            workflow_file_path: Path to workflow JSON file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        available_models = self.get_available_models()
        
        if not available_models:
            return True, None  # Can't validate, assume OK
        
        try:
            with open(workflow_file_path, 'r', encoding='utf-8') as f:
                workflow_json = json.load(f)
            
            model_name = None
            
            # Check for CheckpointLoaderSimple node
            checkpoint_node = self.find_node_by_class_type(workflow_json, "CheckpointLoaderSimple")
            if checkpoint_node:
                model_name = workflow_json[checkpoint_node]["inputs"].get("ckpt_name", "")
            else:
                # Check for UNETLoader node (for Flux/HiDream workflows)
                unet_node = self.find_node_by_class_type(workflow_json, "UNETLoader")
                if unet_node:
                    model_name = workflow_json[unet_node]["inputs"].get("unet_name", "")
            
            if model_name and model_name not in available_models:
                return False, (
                    f"Workflow references model '{model_name}' which is not available. "
                    f"Available models: {', '.join(available_models)}"
                )
            
            return True, None
            
        except Exception as e:
            return False, f"Failed to validate workflow: {e}"

