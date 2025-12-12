"""
Test script for ComfyUI SDXL model integration
Run this to test SDXL image generation via ComfyUI
"""

import sys
from config import Config
from image_generator import ImageGenerator
from image_provider import ImageStyle

def test_comfyui_connection():
    """Test ComfyUI server connection and provider initialization"""
    print("=" * 60)
    print("Testing ComfyUI Connection...")
    print("=" * 60)
    
    try:
        config = Config()
        comfyui_server = config.get_comfyui_server_address()
        print(f"\n[INFO] ComfyUI Server: {comfyui_server}")
        
        # Test server connectivity
        import urllib.request
        try:
            urllib.request.urlopen(f"http://{comfyui_server}/system_stats", timeout=3)
            print("[OK] ComfyUI server is reachable")
        except Exception as e:
            print(f"[X] ComfyUI server not reachable: {e}")
            print(f"    Make sure ComfyUI is running at {comfyui_server}")
            return False
        
        # Test provider initialization
        generator = ImageGenerator()
        providers = generator.get_available_providers()
        
        if "comfyui" in providers:
            print("[OK] ComfyUI provider is available")
            provider_info = providers["comfyui"]
            print(f"    Model: {provider_info.get('model', 'N/A')}")
            print(f"    Features: {list(provider_info.get('features', {}).keys())}")
            return True
        else:
            print("[X] ComfyUI provider not available")
            print("    Check logs for initialization errors")
            return False
            
    except Exception as e:
        print(f"\n[X] Connection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sdxl_generation():
    """Test SDXL image generation via ComfyUI"""
    print("\n" + "=" * 60)
    print("Testing SDXL Image Generation...")
    print("=" * 60)
    print("\n[!] This will generate an image using ComfyUI SDXL model")
    print("    Make sure ComfyUI server is running!")
    
    response = input("\nDo you want to test image generation? (y/n): ").strip().lower()
    
    if response != 'y':
        print("Skipping image generation test...")
        return True
    
    try:
        generator = ImageGenerator()
        
        # Test prompt
        test_prompt = "A beautiful landscape with mountains and a lake at sunset, highly detailed, photorealistic"
        
        print(f"\n[INFO] Generating image with SDXL...")
        print(f"  Prompt: {test_prompt}")
        print(f"  Provider: comfyui")
        print(f"  Size: 1024x1024")
        print(f"  This may take 30-60 seconds...\n")
        
        result = generator.generate(
            prompt=test_prompt,
            style=ImageStyle.PHOTOREAL,
            width=1024,
            height=1024,
            provider="comfyui",  # Force ComfyUI provider
            steps=25,  # SDXL typically uses 20-30 steps
            guidance_scale=7.0,  # SDXL uses higher CFG (5-9)
            seed=None  # Random seed
        )
        
        if result.success:
            print("\n[OK] Image generated successfully!")
            print(f"  Provider: {result.provider}")
            print(f"  Model: {result.model}")
            print(f"  Images generated: {len(result.images)}")
            
            # Check if images are in result
            if result.images:
                print(f"  Image data available: {len(result.images)} image(s)")
                
                # Try to save the image
                try:
                    from PIL import Image
                    from io import BytesIO
                    import os
                    
                    output_dir = Path("test_output")
                    output_dir.mkdir(exist_ok=True)
                    
                    for i, img_data in enumerate(result.images):
                        if isinstance(img_data, dict) and "bytes" in img_data:
                            img_bytes = img_data["bytes"]
                        elif isinstance(img_data, bytes):
                            img_bytes = img_data
                        else:
                            print(f"  [!] Image {i+1}: Unexpected format")
                            continue
                        
                        img = Image.open(BytesIO(img_bytes))
                        output_path = output_dir / f"sdxl_test_{i+1}.png"
                        img.save(output_path)
                        print(f"  [OK] Image {i+1} saved to: {output_path}")
                        
                except Exception as e:
                    print(f"  [!] Could not save image: {e}")
                    print(f"  [INFO] Image data is available in result.images")
            
            if result.metadata:
                print(f"\n  Metadata:")
                for key, value in result.metadata.items():
                    print(f"    {key}: {value}")
            
            return True
        else:
            print(f"\n[X] Image generation failed: {result.error}")
            if result.metadata:
                print(f"  Metadata: {result.metadata}")
            return False
            
    except Exception as e:
        print(f"\n[X] Generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_workflow_validation():
    """Test that workflow files are valid"""
    print("\n" + "=" * 60)
    print("Testing Workflow Validation...")
    print("=" * 60)
    
    try:
        from comfyui_provider import ComfyUIProvider
        from pathlib import Path
        
        config = Config()
        provider = ComfyUIProvider(
            server_address=config.get_comfyui_server_address(),
            workflow_dir=config.get_comfyui_workflow_dir()
        )
        
        # Get available models
        models = provider.get_available_models()
        print(f"\n[INFO] Available models in ComfyUI: {models}")
        
        # Validate workflows
        workflows = [
            (Path(config.get_comfyui_workflow_dir()) / "t2i_flux.json", "T2I"),
            (Path(config.get_comfyui_workflow_dir()) / "i2i_flux.json", "I2I")
        ]
        
        for workflow_path, workflow_type in workflows:
            if workflow_path.exists():
                is_valid, error = provider.validate_workflow_model(str(workflow_path))
                if is_valid:
                    print(f"[OK] {workflow_type} workflow is valid")
                else:
                    print(f"[X] {workflow_type} workflow validation failed: {error}")
            else:
                print(f"[!] {workflow_type} workflow not found: {workflow_path}")
        
        return True
        
    except Exception as e:
        print(f"\n[X] Workflow validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all ComfyUI SDXL tests"""
    print("\n" + "=" * 60)
    print("ComfyUI SDXL Integration Test")
    print("=" * 60)
    
    # Test 1: Connection
    if not test_comfyui_connection():
        print("\n" + "=" * 60)
        print("[X] Connection test failed. Please check:")
        print("    1. ComfyUI server is running")
        print("    2. Server address is correct (default: 127.0.0.1:8188)")
        print("    3. Check logs for errors")
        print("=" * 60)
        sys.exit(1)
    
    # Test 2: Workflow validation
    test_workflow_validation()
    
    # Test 3: Image generation
    if not test_sdxl_generation():
        print("\n" + "=" * 60)
        print("[!] Image generation test failed. Check:")
        print("    1. ComfyUI server is running")
        print("    2. SDXL model is loaded")
        print("    3. Workflow files are correct")
        print("    4. Check ComfyUI server logs")
        print("=" * 60)
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("[OK] All tests completed!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Test in the web app: Select 'comfyui' as provider")
    print("  2. Generate images through the Streamlit interface")
    print("  3. Check test_output/ folder for generated images")
    print()


if __name__ == "__main__":
    from pathlib import Path
    main()

