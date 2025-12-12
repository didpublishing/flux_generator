# Image Generation Options - Current Setup

## Overview

Your image generation system now supports multiple providers with intelligent routing based on your needs.

## Your Current Configuration

✅ **OpenAI API** - Available (for prompt generation and DALL-E 3 images)  
✅ **Black Forest Labs API** - Available (Official Flux API - RECOMMENDED)  
❌ **LTX API** - Not configured (video generation not yet implemented)

## Available Image Providers

### 1. Black Forest Labs (BFL) - Official Flux API ⭐ RECOMMENDED

**Status**: ✅ Ready to use  
**Why Use It**: 
- Direct access to Flux models from the creators
- Best feature support (img2img, inpainting, high-res, etc.)
- Official API with reliable support
- No third-party dependencies (just uses `requests`)

**Models Available**:
- `flux1.1-pro` - Highest quality, best for final images
- `flux1.1-dev` - Balanced quality/speed
- `flux1.1-schnell` - Fastest, for quick drafts

**Setup**: 
Add to your `.env`:
```env
BLACK_FOREST_LABS_API_KEY=your_key_here
```

Get your API key: https://dashboard.bfl.ai/

### 2. OpenAI DALL-E 3

**Status**: ✅ Available  
**Best For**:
- Marketing visuals
- Brand layouts
- Product shots
- Text/logos in images
- Quick ideation

**Limitations**:
- No negative prompts
- No seeds (less reproducible)
- Fixed 1024x1024 resolution
- No img2img or inpainting

### 3. Third-Party Flux Hosts (Alternative)

If you don't have BFL API key, you can use:
- **Fal.ai** - Good feature support
- **Together.ai** - Cost-effective
- **Replicate** - Easy to use
- **Fireworks** - Fast performance

## Image Generation Capabilities

### Supported Features by Provider

| Feature | OpenAI | BFL (Direct) | Fal.ai | Together | Replicate |
|---------|--------|--------------|--------|----------|-----------|
| Text-to-Image | ✅ | ✅ | ✅ | ✅ | ✅ |
| Image-to-Image | ❌ | ✅ | ✅ | ❌ | ✅ |
| Inpainting | ❌ | ✅ | ✅ | ❌ | ❌ |
| Negative Prompts | ❌ | ✅ | ✅ | ✅ | ✅ |
| Seeds | ❌ | ✅ | ✅ | ✅ | ✅ |
| Custom Sizes | ❌ | ✅ | ✅ | ✅ | ✅ |
| Upscaling | ❌ | ✅ | ✅ | ❌ | ❌ |

## Automatic Provider Routing

The system automatically selects the best provider based on:

### Style-Based Routing

- **Fast Draft** → Flux schnell (BFL or host)
- **Photoreal** → Flux pro (BFL or host)  
- **Brand/Logo** → OpenAI (best prompt fidelity)
- **Portrait** → Flux dev (BFL or host)
- **Cinematic** → Flux pro (BFL or host)
- **Artistic** → Flux dev (BFL or host)

### Feature-Based Routing

- **Img2img requests** → Flux (BFL or Fal.ai)
- **Inpainting** → Flux (BFL or Fal.ai)
- **Negative prompts needed** → Flux (any host)
- **Seed required** → Flux (any host)

## Quick Start Guide

### 1. Update Your .env File

```env
# Required for prompt generation
OPENAI_API_KEY=sk-your_key_here

# Recommended for image generation
BLACK_FOREST_LABS_API_KEY=your_bfl_key_here
```

### 2. Test Image Generation

```python
from image_generator import ImageGenerator
from image_provider import ImageStyle

generator = ImageGenerator()

result = generator.generate(
    prompt="A cinematic sunset over mountains",
    style=ImageStyle.CINEMATIC,
    width=1024,
    height=1024
)

if result.success:
    print(f"Generated using: {result.provider}")
    print(f"Image URL: {result.get_image_url()}")
```

## Recommended Workflow

1. **Generate Prompts** → Use your existing prompt generator (OpenAI)
2. **Create Drafts** → Use Flux schnell for quick iterations
3. **Final Images** → Use Flux pro for highest quality
4. **Brand/Marketing** → Use OpenAI DALL-E 3 for layouts

## Cost Considerations

- **OpenAI DALL-E 3**: ~$0.04 per HD image
- **BFL Flux schnell**: Very cheap (~$0.001 per image)
- **BFL Flux dev**: Moderate (~$0.01 per image)
- **BFL Flux pro**: Higher cost (~$0.05 per image), best quality

**Recommendation**: Use Flux schnell for testing, Flux pro for final outputs.

## Next Steps

1. ✅ Add `BLACK_FOREST_LABS_API_KEY` to your `.env` file
2. ✅ Test image generation with a simple prompt
3. 🔄 Integrate into Streamlit UI (when ready)
4. 🔄 Add img2img UI (future enhancement)

## Troubleshooting

**"No available image providers"**
- Check `.env` has `BLACK_FOREST_LABS_API_KEY` or `FLUX_API_KEY`
- Verify API keys are valid
- Check API credits/quota

**"BFL API request error"**
- Verify API key from https://dashboard.bfl.ai/
- Check you have credits
- Review error details in logs

**"Generation timeout"**
- BFL API uses polling - images may take 10-60 seconds
- Check network connectivity
- Try a simpler prompt for faster generation

## Summary

✅ **You're all set!** Just add your Black Forest Labs API key to `.env` and you can start generating images.

The system will automatically:
- Use BFL API when available (best features)
- Route to appropriate model (pro/dev/schnell)
- Fall back to OpenAI if needed
- Handle all the polling and error checking

Ready to generate images! 🎨

