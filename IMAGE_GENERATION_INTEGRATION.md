# Image Generation Integration Guide

This document explains how to integrate the image generation system into your Flux Generator app.

## Overview

The image generation system provides:
- **Pluggable provider architecture** - Easily swap between OpenAI, Flux, and other providers
- **Smart routing** - Automatically selects the best provider based on style and features
- **Style presets** - Pre-configured styles for different use cases
- **Caching** - Avoid regenerating the same images
- **Template system** - Enhance prompts with style-specific templates

## Quick Start

### 1. Install Dependencies

Based on your chosen Flux host, install one of:

```bash
# For Fal.ai (recommended)
pip install fal-client

# OR for Together.ai
pip install together

# OR for Replicate
pip install replicate
```

### 2. Update Environment Variables

Add to your `.env` file:

```env
# Required - already exists
OPENAI_API_KEY=your_openai_key

# Optional - for Flux image generation
FLUX_API_KEY=your_flux_api_key
FLUX_HOST=fal  # Options: fal, together, replicate

# Optional - for video generation (future)
LTX_API_KEY=your_ltx_key
```

### 3. Basic Usage in Your Code

```python
from image_generator import ImageGenerator
from image_provider import ImageStyle

# Initialize
generator = ImageGenerator()

# Generate an image
result = generator.generate(
    prompt="A beautiful sunset over mountains",
    style=ImageStyle.CINEMATIC,
    width=1024,
    height=1024
)

if result.success:
    image_url = result.get_image_url()
    # Use image_url in your Streamlit app
else:
    print(f"Error: {result.error}")
```

## Integration with Streamlit

### Adding to web_app.py

```python
from image_generator import ImageGenerator
from image_provider import ImageStyle

# In initialize_components():
if 'image_generator' not in st.session_state:
    st.session_state.image_generator = ImageGenerator()

# In your UI:
def generate_image_tab():
    st.header("🎨 Generate Image")
    
    prompt = st.text_area("Enter your prompt", height=100)
    
    style = st.selectbox(
        "Image Style",
        options=["fast_draft", "photoreal", "brand_layout", "portrait", 
                 "product", "logo_text", "artistic", "cinematic"]
    )
    
    if st.button("Generate Image"):
        with st.spinner("Generating image..."):
            result = st.session_state.image_generator.generate(
                prompt=prompt,
                style=style,
                width=1024,
                height=1024
            )
            
            if result.success:
                st.success(f"Generated using {result.provider}")
                st.image(result.get_image_url())
            else:
                st.error(f"Generation failed: {result.error}")
```

## Available Styles

- **fast_draft**: Quick, lower quality (Flux schnell)
- **photoreal**: High-quality photorealistic (Flux pro)
- **brand_layout**: Brand/marketing visuals (OpenAI)
- **portrait**: Portrait photography (Flux dev)
- **product**: Product photography (OpenAI)
- **logo_text**: Logos and text (OpenAI)
- **artistic**: Artistic styles (Flux dev)
- **cinematic**: Cinematic quality (Flux pro)

## Provider Routing

The system automatically routes requests to the best provider:

- **Fast drafts** → Flux schnell (fastest, cheapest)
- **Photoreal** → Flux pro (highest quality)
- **Brand/Logo/Text** → OpenAI (best prompt fidelity)
- **Portrait/Artistic** → Flux dev (balanced)
- **Img2img** → Flux (only provider with img2img support)
- **Inpainting** → Flux (only provider with inpainting)

### Customizing Routing

Edit `image_routing_config.json` to change routing rules without code changes:

```json
{
  "style_routing": {
    "photoreal": {
      "provider": "flux",
      "model": "flux-pro",
      "priority": 1
    }
  }
}
```

## Advanced Features

### Using Seeds for Reproducibility

```python
result = generator.generate(
    prompt="A cat wearing sunglasses",
    seed=42,  # Same seed = same image
    style=ImageStyle.PHOTOREAL
)
```

### Negative Prompts

```python
result = generator.generate(
    prompt="Beautiful landscape",
    negative_prompt="people, buildings, text, watermark",
    style=ImageStyle.PHOTOREAL
)
```

### Generating from Flux Prompts

If you've already optimized a prompt using your prompt generator:

```python
# Get optimized prompt from PromptGenerator
optimized_prompt = st.session_state.prompt_generator.optimize_prompt_with_openai(params)

# Generate image directly
result = st.session_state.image_generator.generate_from_flux_prompt(
    flux_prompt=optimized_prompt,
    style="photoreal"
)
```

### Image-to-Image (Future)

```python
result = generator.generate(
    prompt="Make this more cinematic",
    source_image_url="https://example.com/image.jpg",
    strength=0.7,  # How much to change (0.0-1.0)
    style=ImageStyle.CINEMATIC
)
```

## Provider Capabilities

| Feature | OpenAI | Flux (Fal) | Flux (Together) | Flux (Replicate) |
|---------|--------|------------|-----------------|------------------|
| Text-to-Image | ✓ | ✓ | ✓ | ✓ |
| Image-to-Image | ✗ | ✓ | ✗ | ✓ |
| Inpainting | ✗ | ✓ | ✗ | ✗ |
| Negative Prompts | ✗ | ✓ | ✓ | ✓ |
| Seeds | ✗ | ✓ | ✓ | ✓ |
| Upscaling | ✗ | ✓ | ✗ | ✗ |

## Cost Considerations

- **OpenAI DALL-E 3**: ~$0.04 per image (HD)
- **Flux schnell**: Very cheap, fast (~$0.001 per image)
- **Flux dev**: Moderate cost (~$0.01 per image)
- **Flux pro**: Higher cost, best quality (~$0.05 per image)

**Recommendation**: Use Flux schnell for drafts, Flux pro for final images.

## Error Handling

The system includes automatic fallbacks:

1. If requested provider fails → Falls back to next provider in chain
2. If style routing fails → Uses default provider (OpenAI)
3. If all providers fail → Returns error in result

Always check `result.success` before using images.

## Caching

Images are automatically cached based on:
- Prompt
- Negative prompt
- Dimensions
- Seed
- Style

To disable caching:
```python
result = generator.generate(..., use_cache=False)
```

## Next Steps

1. **Phase 1** (Current): Basic image generation with OpenAI and Flux
2. **Phase 2**: Add img2img and inpainting UI
3. **Phase 3**: Add video generation with LTX
4. **Phase 4**: Add upscaling and advanced features

## Troubleshooting

**"No available image providers"**
- Check your `.env` file has API keys
- Verify API keys are valid
- Check provider SDKs are installed

**"Flux client not initialized"**
- Install the provider SDK: `pip install fal-client`
- Or use a different Flux host

**"Generation failed"**
- Check API key permissions
- Verify you have credits/quota
- Review error message in `result.error`

## Example Integration

See `image_generation_example.py` for complete examples.

