# ComfyUI Workflow Templates

This directory contains ComfyUI workflow JSON files that define how images are generated.

## Required Workflows

### `t2i_flux.json` - Text-to-Image Workflow
This workflow is used for standard text-to-image generation. It should include:
- Model loader (e.g., Flux model)
- CLIPTextEncode nodes for positive and negative prompts
- KSampler node for generation parameters
- EmptyLatentImage node for dimensions
- VAEDecode and SaveImage nodes

### `i2i_flux.json` - Image-to-Image Workflow
This workflow is used for image-to-image transformations. It should include:
- LoadImage node for input image
- CLIPTextEncode nodes for prompts
- KSampler node with denoise control
- VAEDecode and SaveImage nodes

## Creating Workflows

1. Open ComfyUI in your browser
2. Build your workflow in the UI
3. Enable **Dev Mode Options** (gear icon in ComfyUI)
4. Click **"Save (API format)"** to export the workflow
5. Save the JSON file to this directory with the appropriate name

## Workflow Format

Workflows must be in API format (not UI format). The API format is a dictionary where:
- Keys are node IDs (strings)
- Values are node definitions with `class_type` and `inputs`

## Example Node Structure

```json
{
  "3": {
    "class_type": "KSampler",
    "inputs": {
      "seed": 12345,
      "steps": 28,
      "cfg": 3.5,
      "denoise": 1.0
    }
  }
}
```

## Node Types Supported

The provider automatically finds and updates these node types:
- `CLIPTextEncode` - Positive and negative prompts
- `KSampler` - Generation parameters (seed, steps, CFG, denoise)
- `EmptyLatentImage` - Image dimensions (T2I)
- `LoadImage` - Input image filename (I2I)
- `AnySwitch` / `Primitive` - Mode switching (T2I/I2I)

## Custom Nodes

The provider also supports custom nodes:
- `Qwen2-VL-Instruct` - VLM prompt refinement
- `FluxGuidance` - Flux guidance control

If your workflow uses custom nodes, ensure they are installed in ComfyUI.

## Testing

After creating a workflow, test it by:
1. Ensuring ComfyUI server is running
2. Using the image generation feature in the app
3. Checking logs for any errors

