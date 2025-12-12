"""
Example usage of the Image Generator system

This demonstrates how to use the image generation API in your application.
"""

from image_generator import ImageGenerator
from image_provider import ImageStyle
from config import Config

def example_basic_generation():
    """Basic image generation example"""
    # Initialize
    generator = ImageGenerator()
    
    # Generate a simple image
    result = generator.generate(
        prompt="A beautiful sunset over mountains, cinematic lighting",
        style=ImageStyle.CINEMATIC,
        width=1024,
        height=1024
    )
    
    if result.success:
        print(f"Generated image using {result.provider} ({result.model})")
        print(f"Image URL: {result.get_image_url()}")
    else:
        print(f"Error: {result.error}")


def example_flux_prompt_generation():
    """Generate from an optimized Flux prompt"""
    generator = ImageGenerator()
    
    # Use a pre-optimized Flux prompt
    flux_prompt = "A young detective from the 1940s, Pulp fiction style illustration, Dutch tilt, City street in the 1940s at night, chiaroscuro, film noire, cinematic lighting, dramatic shadows, high detail, professional illustration, 8k, masterpiece"
    
    result = generator.generate_from_flux_prompt(
        flux_prompt=flux_prompt,
        style="photoreal",
        width=1024,
        height=1024,
        seed=42  # For reproducibility
    )
    
    if result.success:
        print(f"Success! Generated {len(result.images)} image(s)")
        for idx, img in enumerate(result.images):
            print(f"  Image {idx + 1}: {img.get('url', 'N/A')}")


def example_style_presets():
    """Example using different style presets"""
    generator = ImageGenerator()
    
    styles_to_test = [
        (ImageStyle.FAST_DRAFT, "Quick sketch of a cat"),
        (ImageStyle.PHOTOREAL, "Professional portrait of a business person"),
        (ImageStyle.PRODUCT, "Modern smartphone on white background"),
        (ImageStyle.LOGO_TEXT, "Tech company logo with text 'INNOVATE'"),
    ]
    
    for style, prompt in styles_to_test:
        print(f"\nGenerating {style.value}: {prompt}")
        result = generator.generate(
            prompt=prompt,
            style=style,
            num_images=1
        )
        
        if result.success:
            print(f"  ✓ Success - Provider: {result.provider}, Model: {result.model}")
        else:
            print(f"  ✗ Failed: {result.error}")


def example_provider_info():
    """Show available providers and their capabilities"""
    generator = ImageGenerator()
    
    providers = generator.get_available_providers()
    
    print("Available Image Providers:")
    print("=" * 50)
    
    for name, info in providers.items():
        print(f"\n{name.upper()}:")
        print(f"  Provider: {info['provider']}")
        print(f"  Model: {info['model']}")
        print(f"  Features:")
        for feature, supported in info['features'].items():
            status = "✓" if supported else "✗"
            print(f"    {status} {feature}")


def example_with_negative_prompt():
    """Example using negative prompts"""
    generator = ImageGenerator()
    
    result = generator.generate(
        prompt="Beautiful landscape with mountains and lake",
        style=ImageStyle.PHOTOREAL,
        negative_prompt="people, buildings, cars, text, watermark",
        width=1024,
        height=1024
    )
    
    if result.success:
        print("Generated image with negative prompt filtering")
        print(f"Image: {result.get_image_url()}")


if __name__ == "__main__":
    print("Image Generation Examples")
    print("=" * 50)
    
    # Uncomment the example you want to run:
    
    # example_basic_generation()
    # example_flux_prompt_generation()
    # example_style_presets()
    # example_provider_info()
    # example_with_negative_prompt()
    
    print("\nTo run examples, uncomment the desired function in the main block.")

