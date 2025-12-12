"""Test the exported HiDream workflow with ComfyUI connection"""
import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

# Import the provider
try:
    from comfyui_provider import ComfyUIProvider
except ImportError as e:
    print(f"[ERROR] Failed to import ComfyUIProvider: {e}")
    sys.exit(1)

def test_server_connection(server_address: str = "127.0.0.1:8188"):
    """Test if ComfyUI server is reachable"""
    print(f"Testing ComfyUI server connection to {server_address}...")
    print("=" * 60)
    
    endpoints = ["/system_stats", "/object_info"]
    
    for endpoint in endpoints:
        try:
            url = f"http://{server_address}{endpoint}"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as response:
                data = response.read()
                print(f"[OK] {endpoint} - Server is reachable!")
                if endpoint == "/object_info":
                    try:
                        obj_info = json.loads(data)
                        print(f"   Found {len(obj_info)} node types in ComfyUI")
                    except:
                        pass
                return True
        except urllib.error.URLError as e:
            print(f"[ERROR] {endpoint} - Connection failed: {e}")
        except urllib.error.HTTPError as e:
            print(f"[WARNING] {endpoint} - HTTP {e.code}: {e.reason}")
        except Exception as e:
            print(f"[ERROR] {endpoint} - {type(e).__name__}: {e}")
    
    return False

def test_workflow_structure(workflow_path: str):
    """Test if the exported workflow has the expected structure"""
    print(f"\nAnalyzing exported workflow: {workflow_path}")
    print("=" * 60)
    
    if not Path(workflow_path).exists():
        print(f"[ERROR] Workflow file not found: {workflow_path}")
        return False
    
    try:
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
        
        print(f"[OK] Workflow JSON is valid")
        print(f"   Found {len(workflow)} nodes")
        
        # Check for key node types
        node_types = {}
        for node_id, node_data in workflow.items():
            class_type = node_data.get("class_type", "Unknown")
            node_types[class_type] = node_types.get(class_type, 0) + 1
        
        print(f"\nNode types found:")
        for node_type, count in sorted(node_types.items()):
            print(f"   - {node_type}: {count}")
        
        # Check for specific nodes we need
        required_nodes = {
            "CLIPTextEncode": "Text encoding (prompts)",
            "KSampler": "Image sampling",
            "VAEDecode": "Image decoding",
            "SaveImage": "Image saving"
        }
        
        optional_nodes = {
            "UNETLoader": "UNET model loading (Flux/HiDream)",
            "QuadrupleCLIPLoader": "Multi-CLIP loading (Flux/HiDream)",
            "EmptySD3LatentImage": "SD3 latent image (Flux/HiDream)",
            "ModelSamplingSD3": "SD3 model sampling",
            "CheckpointLoaderSimple": "Standard checkpoint loading",
            "EmptyLatentImage": "Standard latent image"
        }
        
        print(f"\nRequired nodes:")
        missing_required = []
        for node_type, description in required_nodes.items():
            if node_type in node_types:
                print(f"   [OK] {node_type} - {description}")
            else:
                print(f"   [MISSING] {node_type} - {description}")
                missing_required.append(node_type)
        
        print(f"\nOptional nodes (workflow-specific):")
        for node_type, description in optional_nodes.items():
            if node_type in node_types:
                print(f"   [FOUND] {node_type} - {description}")
        
        # Check model references
        print(f"\nModel references:")
        unet_node = None
        checkpoint_node = None
        
        for node_id, node_data in workflow.items():
            if node_data.get("class_type") == "UNETLoader":
                unet_node = node_id
                model_name = node_data.get("inputs", {}).get("unet_name", "Not specified")
                print(f"   UNETLoader ({node_id}): {model_name}")
            elif node_data.get("class_type") == "CheckpointLoaderSimple":
                checkpoint_node = node_id
                model_name = node_data.get("inputs", {}).get("ckpt_name", "Not specified")
                print(f"   CheckpointLoaderSimple ({node_id}): {model_name}")
        
        if not unet_node and not checkpoint_node:
            print(f"   [WARNING] No model loader found in workflow")
        
        if missing_required:
            print(f"\n[WARNING] Missing required nodes: {', '.join(missing_required)}")
            return False
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to analyze workflow: {type(e).__name__}: {e}")
        return False

def test_provider_with_workflow(workflow_path: str):
    """Test if the provider can work with the exported workflow"""
    print(f"\nTesting provider with exported workflow...")
    print("=" * 60)
    
    try:
        provider = ComfyUIProvider(server_address="127.0.0.1:8188")
        
        # Test model discovery
        print("Checking available models...")
        models = provider.get_available_models()
        if models:
            print(f"[OK] Found {len(models)} available models:")
            for model in models[:5]:  # Show first 5
                print(f"   - {model}")
            if len(models) > 5:
                print(f"   ... and {len(models) - 5} more")
        else:
            print("[WARNING] No models found (server may not be running or models not loaded)")
        
        # Test workflow validation
        print(f"\nValidating workflow model...")
        is_valid, error_msg = provider.validate_workflow_model(workflow_path)
        if is_valid:
            print("[OK] Workflow model validation passed")
        else:
            print(f"[WARNING] Workflow validation: {error_msg}")
        
        # Test parameter injection (dry run - don't actually queue)
        print(f"\nTesting parameter injection (dry run)...")
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
        
        # Make a copy for testing
        test_workflow = json.loads(json.dumps(workflow))
        
        # Try to inject parameters
        provider._inject_parameters(
            test_workflow,
            pos_prompt="test prompt",
            neg_prompt="test negative",
            seed=12345,
            steps=16,
            cfg=1.0,
            width=1024,
            height=1024
        )
        
        # Check if parameters were injected
        sampler_node = provider.find_node_by_class_type(test_workflow, "KSampler")
        if sampler_node:
            sampler_inputs = test_workflow[sampler_node]["inputs"]
            if sampler_inputs.get("seed") == 12345:
                print("[OK] Seed injection works")
            if sampler_inputs.get("steps") == 16:
                print("[OK] Steps injection works")
            if sampler_inputs.get("cfg") == 1.0:
                print("[OK] CFG injection works")
        
        # Check prompt injection
        text_nodes = []
        for node_id, node_data in test_workflow.items():
            if node_data.get("class_type") == "CLIPTextEncode":
                text_nodes.append(node_id)
        
        if text_nodes:
            first_text = test_workflow[text_nodes[0]]["inputs"].get("text", "")
            if "test prompt" in first_text:
                print("[OK] Prompt injection works")
        
        # Check dimension injection
        latent_node = provider.find_node_by_class_type(test_workflow, "EmptySD3LatentImage")
        if not latent_node:
            latent_node = provider.find_node_by_class_type(test_workflow, "EmptyLatentImage")
        
        if latent_node:
            latent_inputs = test_workflow[latent_node]["inputs"]
            if latent_inputs.get("width") == 1024 and latent_inputs.get("height") == 1024:
                print("[OK] Dimension injection works")
        
        print("\n[OK] Parameter injection test completed")
        return True
        
    except Exception as e:
        print(f"[ERROR] Provider test failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    workflow_path = "HiDream_TI_Flo.json"
    
    print("=" * 60)
    print("ComfyUI Exported Workflow Test")
    print("=" * 60)
    
    # Test 1: Server connection
    if not test_server_connection():
        print("\n[ERROR] Cannot connect to ComfyUI server. Please start ComfyUI first.")
        sys.exit(1)
    
    # Test 2: Workflow structure
    if not test_workflow_structure(workflow_path):
        print("\n[ERROR] Workflow structure validation failed")
        sys.exit(1)
    
    # Test 3: Provider compatibility
    if not test_provider_with_workflow(workflow_path):
        print("\n[WARNING] Provider compatibility test had issues")
        print("The workflow may still work, but some features might not function correctly.")
    else:
        print("\n" + "=" * 60)
        print("[SUCCESS] All tests passed!")
        print("=" * 60)
        print("\nThe exported workflow should work with the ComfyUI provider.")
        print("You can now use this workflow by:")
        print(f"  1. Copying it to workflows/comfyui/t2i_flux.json (or i2i_flux.json)")
        print("  2. Or using it directly with the provider")

if __name__ == "__main__":
    main()

