# ComfyUI Integration Setup Guide

This guide will help you set up and use the ComfyUI integration with your Flux Generator application.

## Prerequisites

1. **ComfyUI Installation**: ComfyUI must be installed and running
   - Your installation is at: `E:\StabilityMatrix-win-x64\Data\Packages\ComfyUI`
   - ComfyUI server should be accessible at `127.0.0.1:8188` (default)

2. **Python Dependencies**: Install required packages
   ```bash
   pip install websocket-client requests
   ```

3. **ComfyUI Server Running**: Start ComfyUI server before using the integration
   - Navigate to your ComfyUI directory
   - Run: `python main.py` or use your StabilityMatrix launcher

## Configuration

### 1. Environment Variables

Add these optional variables to your `.env` file (or use defaults):

```env
# ComfyUI Configuration (Optional - defaults shown)
COMFYUI_SERVER_ADDRESS=127.0.0.1:8188
COMFYUI_WORKFLOW_DIR=workflows/comfyui
COMFYUI_TEMP_DIR=temp_uploads
```

### 2. Create Workflow Files

You need to create workflow JSON files in the `workflows/comfyui/` directory:

#### Required Files:
- **`t2i_flux.json`** - Text-to-Image workflow
- **`i2i_flux.json`** - Image-to-Image workflow

#### How to Create Workflows:

1. **Start ComfyUI Server**
   - Make sure ComfyUI is running at `127.0.0.1:8188`

2. **Build Your Workflow**
   - Open ComfyUI in your browser (http://127.0.0.1:8188)
   - Build a workflow with these essential nodes:
     - **Model Loader** (e.g., CheckpointLoaderSimple)
     - **CLIPTextEncode** nodes (for positive and negative prompts)
     - **KSampler** (for generation parameters)
     - **EmptyLatentImage** (for T2I) or **LoadImage** (for I2I)
     - **VAEDecode** and **SaveImage** nodes

3. **Export Workflow**
   - Click the gear icon (⚙️) to enable Dev Mode Options
   - Click **"Save (API format)"** button
   - Save the JSON file to `workflows/comfyui/` with the appropriate name

4. **Example Workflows**
   - See `workflows/comfyui/t2i_flux.json.example` for a T2I template
   - See `workflows/comfyui/i2i_flux.json.example` for an I2I template
   - Copy and rename these files (remove `.example` extension) as starting points

## Workflow Requirements

Your workflows must include these node types for automatic parameter injection:

### Text-to-Image (T2I) Workflow:
- ✅ `CLIPTextEncode` - For positive prompt (will be updated)
- ✅ `CLIPTextEncode` - For negative prompt (will be updated)
- ✅ `KSampler` - For generation parameters (seed, steps, CFG, denoise)
- ✅ `EmptyLatentImage` - For image dimensions (width, height)

### Image-to-Image (I2I) Workflow:
- ✅ `LoadImage` - For input image (will be updated with uploaded filename)
- ✅ `CLIPTextEncode` - For prompts
- ✅ `KSampler` - For generation parameters (denoise will be set)
- ✅ `VAEEncode` or `VAEEncodeForInpaint` - To encode input image

### Optional Nodes:
- `AnySwitch` or `Primitive` - For mode switching (T2I/I2I)
- `Qwen2-VL-Instruct` - Custom node for VLM prompt refinement
- `FluxGuidance` - Custom node for Flux guidance control

## Testing the Integration

### 1. Verify ComfyUI Server
```bash
# Check if server is running
curl http://127.0.0.1:8188/system_stats
```

### 2. Test in Application
1. Start your Flux Generator application
2. Check logs for: `ComfyUI provider initialized (server: 127.0.0.1:8188)`
3. If you see a warning about server not reachable, ensure ComfyUI is running

### 3. Generate an Image
1. Go to "Generate Images" tab
2. Enter a prompt
3. Select a style (or leave default)
4. Click generate
5. The system will automatically use ComfyUI if:
   - Server is reachable
   - Workflow files exist
   - Provider is selected (or auto-selected)

## Troubleshooting

### Server Not Reachable
**Error**: `ComfyUI server not reachable at 127.0.0.1:8188`

**Solutions**:
- Ensure ComfyUI server is running
- Check if server is on a different port
- Verify firewall isn't blocking the connection
- Update `COMFYUI_SERVER_ADDRESS` in `.env` if needed

### Workflow File Not Found
**Error**: `Workflow file not found: workflows/comfyui/t2i_flux.json`

**Solutions**:
- Create the workflow files as described above
- Ensure files are named exactly: `t2i_flux.json` and `i2i_flux.json`
- Check file permissions

### Node Not Found in Workflow
**Error**: Workflow executes but parameters aren't updated

**Solutions**:
- Ensure your workflow includes the required node types
- Check node class types match exactly (case-sensitive)
- Verify workflow is in API format (not UI format)

### Image Upload Failed
**Error**: `Failed to upload input image`

**Solutions**:
- Check ComfyUI input folder permissions
- Ensure temp_uploads directory exists
- Verify image format is supported (PNG, JPG, etc.)

## Advanced Configuration

### Custom Workflow Selection
You can modify the provider to use different workflows based on style or other parameters. Edit `comfyui_provider.py`:

```python
def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
    # Custom workflow selection logic
    if request.style == ImageStyle.PHOTOREAL:
        workflow_path = self.workflow_dir / "photoreal_workflow.json"
    else:
        workflow_path = self.default_t2i_workflow
```

### Custom Node Support
To add support for additional custom nodes:

1. Add node finding logic in `find_node_by_class_type()` method
2. Add parameter injection in `_inject_parameters()` method
3. Document the node structure in workflow README

## Integration with Provider Router

ComfyUI is automatically integrated into the provider router. It will be:
- ✅ Available if server is reachable
- ✅ Selectable via provider override
- ✅ Used for features like img2img if configured in routing rules

## Next Steps

1. ✅ Install dependencies (`websocket-client`, `requests`)
2. ✅ Start ComfyUI server
3. ✅ Create workflow JSON files
4. ✅ Test image generation
5. ✅ Customize workflows as needed

## Support

For issues or questions:
- Check application logs in `logs/app.log`
- Review ComfyUI server logs
- Verify workflow JSON format matches API format
- Test workflow directly in ComfyUI UI first

