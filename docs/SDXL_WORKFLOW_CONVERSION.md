# SDXL Workflow Conversion Guide

## Current Status

✅ **Your workflow is compatible with SDXL** - The current workflow using standard `CLIPTextEncode` nodes will work with SDXL models.

## Do You Need to Convert?

### Short Answer: **No, but it's recommended for better results**

The current workflow uses:
- `CLIPTextEncode` (standard) - ✅ Works with SDXL
- `CheckpointLoaderSimple` - ✅ Works with SDXL
- `KSampler` - ✅ Works with SDXL
- `VAEDecode` - ✅ Works with SDXL

### Why Convert to SDXL-Specific Nodes?

SDXL-specific nodes provide:
1. **Better prompt handling** - SDXL uses dual CLIP encoders (base + refiner)
2. **Optimized performance** - Better memory usage and speed
3. **Advanced features** - Separate base/refiner prompts, aspect ratio handling

## Conversion Options

### Option 1: Keep Current Workflow (Recommended for Now)
✅ **Pros:**
- Already working
- Simple and compatible
- No changes needed

❌ **Cons:**
- Not optimized for SDXL
- May not use SDXL's full potential

### Option 2: Convert to SDXL-Specific Nodes (Better Results)

#### SDXL-Specific Nodes Available:
- `CLIPTextEncodeSDXL` - Optimized for SDXL base model
- `CLIPTextEncodeSDXLRefiner` - For refiner model (if using 2-pass)
- `SDXLEmptyLatentImage` - Optimized latent image generation

#### Example SDXL Workflow Structure:

```json
{
  "3": {
    "class_type": "KSampler",
    "inputs": {
      "cfg": 7.0,
      "denoise": 1.0,
      "latent_image": ["5", 0],
      "model": ["4", 0],
      "negative": ["7", 0],
      "positive": ["6", 0],
      "sampler_name": "euler",
      "scheduler": "normal",
      "seed": 12345,
      "steps": 28
    }
  },
  "4": {
    "class_type": "CheckpointLoaderSimple",
    "inputs": {
      "ckpt_name": "sd_xl_base_1.0.safetensors"
    }
  },
  "5": {
    "class_type": "EmptyLatentImage",
    "inputs": {
      "batch_size": 1,
      "height": 1024,
      "width": 1024
    }
  },
  "6": {
    "class_type": "CLIPTextEncodeSDXL",
    "inputs": {
      "clip": ["4", 1],
      "text_g": "masterpiece best quality, beautiful landscape",
      "text_l": "masterpiece best quality, beautiful landscape"
    }
  },
  "7": {
    "class_type": "CLIPTextEncodeSDXL",
    "inputs": {
      "clip": ["4", 1],
      "text_g": "blurry, low quality, distorted",
      "text_l": "blurry, low quality, distorted"
    }
  },
  "8": {
    "class_type": "VAEDecode",
    "inputs": {
      "samples": ["3", 0],
      "vae": ["4", 2]
    }
  },
  "9": {
    "class_type": "SaveImage",
    "inputs": {
      "filename_prefix": "ComfyUI",
      "images": ["8", 0]
    }
  }
}
```

## How to Convert

### Method 1: Rebuild in ComfyUI (Recommended)

1. **Open ComfyUI** in your browser (http://127.0.0.1:8188)
2. **Load SDXL model** - Make sure `sd_xl_base_1.0.safetensors` is selected
3. **Build workflow** with SDXL-specific nodes:
   - Use `CLIPTextEncodeSDXL` instead of `CLIPTextEncode`
   - Keep other nodes the same
4. **Export as API format**:
   - Enable Dev Mode Options (gear icon)
   - Click "Save (API format)"
   - Save to `workflows/comfyui/t2i_flux.json`

### Method 2: Manual Edit (Advanced)

Edit the JSON file directly:
1. Replace `CLIPTextEncode` with `CLIPTextEncodeSDXL`
2. Update inputs to use `text_g` and `text_l` instead of `text`
3. Test the workflow

## Provider Code Updates

✅ **Already Updated** - The provider code now supports both:
- Standard `CLIPTextEncode` nodes
- SDXL-specific `CLIPTextEncodeSDXL` and `CLIPTextEncodeSDXLRefiner` nodes

The code automatically detects and handles both types.

## Testing

After conversion, test with:

```bash
python test_comfyui_sdxl.py
```

Or test in the web app by generating an image.

## Recommendation

**For now: Keep the current workflow** - It works and is simpler.

**Later: Convert to SDXL nodes** - When you want to optimize for better SDXL results or use advanced features like separate base/refiner prompts.

## Notes

- SDXL models work fine with standard nodes
- SDXL-specific nodes are optimizations, not requirements
- The current workflow will generate good SDXL images
- Conversion is optional for better performance/features

