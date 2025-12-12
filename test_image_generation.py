"""
Quick test script to verify image generation setup
Run this to test your API keys and image generation
"""

import sys
from config import Config
from image_generator import ImageGenerator
from image_provider import ImageStyle

def test_configuration():
    """Test that API keys are loaded correctly"""
    print("=" * 60)
    print("Testing Configuration...")
    print("=" * 60)
    
    try:
        config = Config()
        
        print("\n[OK] Config loaded successfully")
        print(f"  OpenAI API Key: {'[OK] Set' if config.get_openai_api_key() else '[X] Missing'}")
        print(f"  BFL API Key: {'[OK] Set' if config.get_black_forest_labs_api_key() else '[X] Missing (Optional)'}")
        print(f"  Flux Host: {config.get_flux_host()}")
        
        # Validate OpenAI key
        print("\nValidating OpenAI API key...")
        is_valid, error = config.validate_api_key()
        if is_valid:
            print("  [OK] OpenAI API key is valid")
        else:
            print(f"  [X] OpenAI API key validation failed: {error}")
            return False
        
        return True
        
    except Exception as e:
        print(f"\n[X] Configuration error: {e}")
        return False


def test_providers():
    """Test available image providers"""
    print("\n" + "=" * 60)
    print("Testing Image Providers...")
    print("=" * 60)
    
    try:
        generator = ImageGenerator()
        providers = generator.get_available_providers()
        
        if not providers:
            print("\n[X] No image providers available")
            print("  Make sure you have at least one API key configured")
            return False
        
        print(f"\n[OK] Found {len(providers)} available provider(s):")
        for name, info in providers.items():
            print(f"\n  {name.upper()}:")
            print(f"    Provider: {info['provider']}")
            print(f"    Model: {info['model']}")
            print(f"    Features:")
            for feature, supported in info['features'].items():
                status = "[OK]" if supported else "[X]"
                print(f"      {status} {feature}")
        
        return True
        
    except Exception as e:
        print(f"\n[X] Provider test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_image_generation():
    """Test actual image generation (optional - costs credits)"""
    print("\n" + "=" * 60)
    print("Image Generation Test (Optional)")
    print("=" * 60)
    print("\n[!] WARNING: This will use API credits!")
    response = input("Do you want to test image generation? (y/n): ").strip().lower()
    
    if response != 'y':
        print("Skipping image generation test...")
        return True
    
    try:
        generator = ImageGenerator()
        
        print("\nGenerating test image...")
        print("Prompt: 'A simple test image - red apple on white background'")
        print("Style: Fast Draft")
        
        result = generator.generate(
            prompt="A simple test image - red apple on white background",
            style=ImageStyle.FAST_DRAFT,
            width=1024,
            height=1024,
            num_images=1
        )
        
        if result.success:
            print("\n[OK] Image generated successfully!")
            print(f"  Provider: {result.provider}")
            print(f"  Model: {result.model}")
            print(f"  Images: {len(result.images)}")
            
            if result.get_image_url(0):
                print(f"  Image URL: {result.get_image_url(0)}")
                print("\n  [OK] You can open this URL in a browser to see the image")
            else:
                print("  [!] No image URL returned (check result metadata)")
            
            return True
        else:
            print(f"\n[X] Image generation failed: {result.error}")
            return False
            
    except Exception as e:
        print(f"\n[X] Generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Flux Generator - Image Generation Setup Test")
    print("=" * 60)
    
    # Test 1: Configuration
    if not test_configuration():
        print("\n" + "=" * 60)
        print("[X] Configuration test failed. Please check your .env file.")
        print("=" * 60)
        sys.exit(1)
    
    # Test 2: Providers
    if not test_providers():
        print("\n" + "=" * 60)
        print("[!] Provider test failed. Image generation may not work.")
        print("=" * 60)
        sys.exit(1)
    
    # Test 3: Image generation (optional)
    test_image_generation()
    
    print("\n" + "=" * 60)
    print("[OK] Setup test completed!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Your configuration is working [OK]")
    print("  2. Integrate image generation into your Streamlit app")
    print("  3. See IMAGE_GENERATION_INTEGRATION.md for examples")
    print()


if __name__ == "__main__":
    main()

