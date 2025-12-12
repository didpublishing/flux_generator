# Testing SDXL Model in the App

## Quick Test Summary

✅ **Connection Status**: ComfyUI server is reachable  
✅ **Provider Status**: ComfyUI provider is initialized  
✅ **Workflow Status**: T2I and I2I workflows are valid  
✅ **Models Available**: 
- `sd_xl_base_1.0.safetensors`
- `sd_xl_refiner_1.0.safetensors`

## How to Test SDXL in the Web App

### Option 1: Using the Web Interface

1. **Start the Streamlit app**:
   ```bash
   streamlit run web_app.py
   ```

2. **Navigate to "Generate Images" tab**

3. **Select ComfyUI as provider**:
   - In the provider dropdown, select `comfyui` (or "ComfyUI (Local)")
   - You should see it listed if ComfyUI server is running

4. **Enter a prompt**:
   - Example: "A beautiful landscape with mountains and a lake at sunset, highly detailed, photorealistic"

5. **Configure settings**:
   - **Width**: 1024 (SDXL standard)
   - **Height**: 1024 (SDXL standard)
   - **Steps**: 25-30 (recommended for SDXL)
   - **Guidance Scale**: 7.0 (SDXL typically uses 5-9)

6. **Click Generate**
   - First generation may take 30-60 seconds
   - Image will appear when complete

### Option 2: Using the Test Script

Run the automated test script:

```bash
python test_comfyui_sdxl.py
```

This will:
1. ✅ Test ComfyUI server connection
2. ✅ Validate workflow files
3. ✅ Test actual image generation (when you confirm)

## Troubleshooting

### ComfyUI Provider Not Showing

If ComfyUI doesn't appear in the provider list:

1. **Check ComfyUI server is running**:
   ```bash
   curl http://127.0.0.1:8188/system_stats
   ```

2. **Check application logs**:
   - Look for: `ComfyUI provider initialized (server: 127.0.0.1:8188)`
   - Or: `ComfyUI server not reachable`

3. **Verify environment variables** (optional):
   ```env
   COMFYUI_SERVER_ADDRESS=127.0.0.1:8188
   COMFYUI_WORKFLOW_DIR=workflows/comfyui
   COMFYUI_TEMP_DIR=temp_uploads
   ```

### Generation Fails

If image generation fails:

1. **Check ComfyUI server logs** - Look for errors in ComfyUI console
2. **Verify model is loaded** - SDXL model should be in ComfyUI's models folder
3. **Check workflow file** - Ensure `workflows/comfyui/t2i_flux.json` exists and is valid
4. **Verify model name** - Should be `sd_xl_base_1.0.safetensors`

### Common Errors

**"Workflow references model 'flux1-dev-fp8.safetensors' which is not available"**
- ✅ **Fixed**: Workflow files now use `sd_xl_base_1.0.safetensors`

**"ComfyUI server not reachable"**
- Ensure ComfyUI is running at `127.0.0.1:8188`
- Check firewall settings
- Verify port 8188 is not blocked

**"No images generated or timeout occurred"**
- Check ComfyUI server console for errors
- Verify model is loaded correctly
- Try increasing timeout in `comfyui_provider.py` (default: 300 seconds)

## SDXL-Specific Settings

SDXL works best with these settings:

- **CFG Scale**: 7.0 (range: 5-9)
- **Steps**: 25-30 (20 minimum, 30+ for higher quality)
- **Resolution**: 1024x1024 (native SDXL resolution)
- **Sampler**: Euler (default) or DPM++ 2M Karras
- **Scheduler**: Normal (default)

These are automatically configured in the workflow, but you can override them in the web app.

## Expected Results

When working correctly, you should see:

1. **Provider selection**: ComfyUI appears in dropdown
2. **Generation starts**: Progress indicator or "Generating..." message
3. **Image appears**: Generated image displays in the app
4. **Image saved**: Automatically saved to `vault/images/` folder
5. **Metadata shown**: Generation parameters displayed

## Next Steps

After successful test:

1. ✅ SDXL is working via ComfyUI
2. ✅ You can use it in the web app
3. ✅ Images are automatically saved to vault
4. ✅ You can generate images with different styles and prompts

## Notes

- First generation may be slower (model loading)
- SDXL generates at 1024x1024 natively
- For higher resolutions, consider upscaling workflows
- The refiner model (`sd_xl_refiner_1.0.safetensors`) can be used for 2-pass generation (not yet implemented in workflows)

