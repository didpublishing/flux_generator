# ComfyUI API Integration - Production Plan

## Overview
This plan outlines the integration of ComfyUI API into the Flux Generator project. ComfyUI is already installed at `E:\StabilityMatrix-win-x64\Data\Packages\ComfyUI` and will be accessed via its REST API and WebSocket interface.

## Current Architecture
- **Provider System**: Pluggable architecture with `ImageProvider` abstract base class
- **Existing Providers**: OpenAI DALL-E 3, Flux (via BFL API, Fal.ai, Together, Replicate)
- **Router System**: `ImageProviderRouter` selects providers based on style/features
- **Generator Service**: `ImageGenerator` handles caching, templates, and high-level orchestration

## Integration Goals
1. Add ComfyUI as a new image provider alongside existing providers
2. Support dynamic workflow JSON manipulation for custom ComfyUI workflows
3. Enable Text-to-Image (T2I) and Image-to-Image (I2I) workflows
4. Support custom nodes (Qwen VLM, Flux Guidance, etc.)
5. Maintain compatibility with existing provider router system

---

## Phase 1: Core Infrastructure Setup

### 1.1 Create ComfyUI Provider Module
**File**: `comfyui_provider.py`

**Responsibilities**:
- Implement `ImageProvider` interface
- Handle ComfyUI API communication (HTTP + WebSocket)
- Manage workflow JSON loading and manipulation
- Support synchronous and asynchronous execution

**Key Functions**:
- `queue_prompt(prompt_json, client_id, server_address)` - Submit workflow to ComfyUI
- `get_history(prompt_id, server_address)` - Poll for execution status
- `get_image(filename, subfolder, folder_type, server_address)` - Retrieve generated images
- `upload_image(input_path, filename, server_address)` - Upload images for I2I workflows
- `find_node_by_class_type(workflow_json, class_type)` - Locate nodes in workflow JSON
- `execute_comfy_workflow(...)` - Main execution function

### 1.2 Configuration Updates
**File**: `config.py`

**Changes**:
- Add `COMFYUI_SERVER_ADDRESS` environment variable (default: `127.0.0.1:8188`)
- Add `COMFYUI_WORKFLOW_DIR` for storing workflow JSON files
- Add `COMFYUI_CLIENT_ID` (UUID generation)
- Add `COMFYUI_TEMP_DIR` for temporary uploads

**File**: `env.example`

**Additions**:
```env
# ComfyUI Configuration
COMFYUI_SERVER_ADDRESS=127.0.0.1:8188
COMFYUI_WORKFLOW_DIR=workflows/comfyui
COMFYUI_TEMP_DIR=temp_uploads
```

### 1.3 Dependencies
**File**: `requirements-web.txt` (or `requirements.txt`)

**Add**:
```
websocket-client>=1.6.0
requests>=2.31.0
Pillow>=10.0.0
numpy>=1.24.0
```

---

## Phase 2: ComfyUI Provider Implementation

### 2.1 ComfyUIProvider Class Structure

```python
class ComfyUIProvider(ImageProvider):
    def __init__(self, server_address: str, workflow_dir: str, temp_dir: str):
        # Initialize connection settings
        # Load default workflow templates
        # Setup temp directories
    
    def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        # Main entry point
        # Determine workflow type (T2I vs I2I)
        # Load appropriate workflow JSON
        # Inject parameters
        # Execute and return result
```

### 2.2 Workflow Management

**Workflow Storage**:
- Default workflows stored in `workflows/comfyui/`
- Standard T2I workflow: `workflows/comfyui/t2i_flux.json`
- Standard I2I workflow: `workflows/comfyui/i2i_flux.json`
- User can provide custom workflow paths

**Workflow Loading**:
- Load JSON from file
- Validate structure
- Support both API format and UI format (convert if needed)

### 2.3 Dynamic Parameter Injection

**Node Finding Logic**:
- `find_node_by_class_type()` - Locate nodes by class type
- Support multiple node types:
  - `CLIPTextEncode` - Positive/negative prompts
  - `KSampler` - Seed, steps, CFG, denoise
  - `LoadImage` - Input image for I2I
  - `AnySwitch` / `Primitive` - Mode switching (T2I/I2I)
  - `Qwen2-VL-Instruct` - VLM prompt refinement (custom node)
  - `FluxGuidance` - Guidance control (custom node)

**Parameter Mapping**:
- Map `ImageGenerationRequest` to workflow parameters
- Handle different workflow structures
- Support custom node parameters

### 2.4 Execution Flow

1. **Load Workflow**: Read JSON from file
2. **Determine Mode**: T2I or I2I based on `source_image_url`
3. **Inject Parameters**:
   - Update prompt nodes
   - Update sampler settings
   - Update mode switch if present
   - Upload and reference input image (I2I)
4. **Queue Prompt**: Submit to ComfyUI API
5. **Poll Status**: Wait for completion via `get_history()`
6. **Retrieve Images**: Download via `get_image()`
7. **Return Result**: Format as `ImageGenerationResult`

---

## Phase 3: Integration with Existing System

### 3.1 Provider Router Updates
**File**: `image_provider_router.py`

**Changes**:
- Add ComfyUI provider initialization in `_initialize_providers()`
- Add ComfyUI to routing rules (optional feature routing)
- Support workflow selection based on style/features

**Routing Configuration**:
```json
{
  "comfyui": {
    "provider": "comfyui",
    "workflow": "t2i_flux.json",
    "priority": 2,
    "features": ["img2img", "inpainting", "custom_nodes"]
  }
}
```

### 3.2 Generator Service Updates
**File**: `image_generator.py`

**Changes**:
- ComfyUI provider automatically available if server is reachable
- No template modifications needed (ComfyUI handles prompting)
- Cache support works the same way

### 3.3 Configuration Integration
**File**: `config.py`

**Add Methods**:
```python
def get_comfyui_server_address(self) -> str:
    return os.getenv('COMFYUI_SERVER_ADDRESS', '127.0.0.1:8188')

def get_comfyui_workflow_dir(self) -> str:
    return os.getenv('COMFYUI_WORKFLOW_DIR', 'workflows/comfyui')

def get_comfyui_temp_dir(self) -> str:
    return os.getenv('COMFYUI_TEMP_DIR', 'temp_uploads')
```

---

## Phase 4: Advanced Features

### 4.1 Custom Node Support
- Qwen VLM integration for prompt refinement
- Flux Guidance nodes for enhanced control
- Any Switch nodes for workflow mode selection
- Document parameter injection patterns

### 4.2 Workflow Templates
Create default workflow templates:
- **Basic T2I**: Simple Flux text-to-image
- **Advanced T2I**: With upscaling, guidance, etc.
- **I2I**: Image-to-image with denoise control
- **Inpainting**: Mask-based editing
- **Custom**: User-defined workflows

### 4.3 Error Handling
- Server connection failures
- Workflow JSON validation errors
- Node not found errors
- Execution timeout handling
- Image retrieval failures

### 4.4 Logging & Debugging
- Log workflow modifications
- Log node locations found
- Log execution status
- Debug mode for verbose output

---

## Phase 5: Testing & Validation

### 5.1 Unit Tests
- Test node finding logic
- Test parameter injection
- Test workflow loading
- Test API communication (mocked)

### 5.2 Integration Tests
- Test with running ComfyUI server
- Test T2I workflow execution
- Test I2I workflow execution
- Test error scenarios

### 5.3 User Testing
- Test with actual ComfyUI installation
- Verify workflow compatibility
- Test custom node support
- Validate image quality/results

---

## Phase 6: Documentation

### 6.1 User Guide
- How to prepare ComfyUI workflows
- How to export workflows in API format
- How to configure ComfyUI connection
- Workflow template examples

### 6.2 Developer Guide
- Provider architecture overview
- Adding custom workflow templates
- Extending node support
- Troubleshooting guide

### 6.3 API Reference
- ComfyUIProvider class documentation
- Workflow parameter mapping
- Custom node integration patterns

---

## Implementation Checklist

### Core Development
- [ ] Create `comfyui_provider.py` with base structure
- [ ] Implement API communication functions (queue, history, get_image, upload)
- [ ] Implement workflow JSON loading
- [ ] Implement node finding logic
- [ ] Implement parameter injection
- [ ] Implement execution flow
- [ ] Add error handling and logging

### Integration
- [ ] Update `config.py` with ComfyUI settings
- [ ] Update `image_provider_router.py` to include ComfyUI
- [ ] Update `env.example` with ComfyUI variables
- [ ] Test provider selection and routing

### Workflow Management
- [ ] Create default workflow templates
- [ ] Create workflow directory structure
- [ ] Document workflow format requirements
- [ ] Create workflow validation utility

### Testing
- [ ] Test with ComfyUI server at `127.0.0.1:8188`
- [ ] Test T2I workflow execution
- [ ] Test I2I workflow execution
- [ ] Test error scenarios (server down, invalid workflow, etc.)
- [ ] Test with custom nodes (Qwen, Flux Guidance)

### Documentation
- [ ] Create user setup guide
- [ ] Document workflow preparation steps
- [ ] Create example workflows
- [ ] Update main README with ComfyUI info

---

## Technical Considerations

### ComfyUI Server Requirements
- Server must be running at configured address
- Server must have required models loaded
- Server must have custom nodes installed (if using)
- Server must accept API connections

### Workflow Compatibility
- Workflows must be exported in API format
- Workflows must use supported node types
- Custom nodes must match expected class types
- Workflow structure must be consistent

### Performance
- Polling interval optimization (balance responsiveness vs. load)
- Timeout handling for long-running generations
- Concurrent request handling (if needed)
- Image caching strategy

### Security
- Local server only (127.0.0.1) - no external exposure by default
- File path validation for workflows
- Input image validation
- Error message sanitization

---

## Timeline Estimate

- **Phase 1**: 2-3 hours (Core infrastructure)
- **Phase 2**: 4-6 hours (Provider implementation)
- **Phase 3**: 1-2 hours (Integration)
- **Phase 4**: 2-3 hours (Advanced features)
- **Phase 5**: 2-3 hours (Testing)
- **Phase 6**: 1-2 hours (Documentation)

**Total Estimated Time**: 12-19 hours

---

## Risk Assessment

### High Risk
- **ComfyUI server not running**: Mitigate with clear error messages and startup checks
- **Workflow format incompatibility**: Mitigate with validation and documentation
- **Custom node not found**: Mitigate with graceful degradation and logging

### Medium Risk
- **Performance issues with polling**: Mitigate with configurable intervals
- **Large image uploads**: Mitigate with size limits and compression

### Low Risk
- **API version changes**: Mitigate with version checking (if available)
- **Network issues**: Mitigate with retry logic

---

## Success Criteria

1. ✅ ComfyUI provider successfully integrated into provider router
2. ✅ T2I workflows execute and return images
3. ✅ I2I workflows execute and return images
4. ✅ Parameters correctly injected into workflows
5. ✅ Error handling works for common failure scenarios
6. ✅ Documentation complete and clear
7. ✅ Works with ComfyUI installation at specified path

---

## Next Steps

1. Review and approve this plan
2. Set up development environment
3. Begin Phase 1 implementation
4. Test with local ComfyUI instance
5. Iterate based on testing results

---

## Notes

- ComfyUI installation path: `E:\StabilityMatrix-win-x64\Data\Packages\ComfyUI`
- Default server address: `127.0.0.1:8188`
- Workflows should be exported in API format from ComfyUI UI
- Custom nodes (Qwen, Flux Guidance) are optional but supported
- The provider will work alongside existing providers (OpenAI, Flux API)

