# ComfyUI Docker Setup Guide

## Problem: ComfyUI Not Showing in Provider List

If you're running the Flux Generator app in Docker and ComfyUI isn't appearing in the provider list, it's likely because the Docker container can't reach the ComfyUI server running on your host machine.

## Solution: Configure Docker Networking

### Option 1: Use `host.docker.internal` (Recommended for Windows/Mac)

The Docker Compose file is already configured to use `host.docker.internal:8188` by default. This allows the container to reach services on your host machine.

**To use this:**
1. Make sure ComfyUI is running on `127.0.0.1:8188` on your host
2. The Docker container will automatically use `host.docker.internal:8188`
3. No additional configuration needed!

### Option 2: Set Custom ComfyUI Address

If `host.docker.internal` doesn't work, you can set a custom address in your `.env` file:

```env
# Use host IP address instead (replace with your actual host IP)
COMFYUI_SERVER_ADDRESS=192.168.1.100:8188
```

To find your host IP:
- **Windows**: Open Command Prompt and run `ipconfig`, look for "IPv4 Address"
- **Mac/Linux**: Run `ifconfig` or `ip addr`, look for your network interface IP

### Option 3: Use Host Network Mode (Linux Only)

On Linux, you can use host networking mode:

```yaml
# In docker-compose.yml, add:
network_mode: host
```

Then ComfyUI will be accessible at `127.0.0.1:8188` from inside the container.

**Note:** This only works on Linux. Windows and Mac don't support host networking mode.

### Option 4: Run ComfyUI in Docker Too

If you want to run ComfyUI in Docker as well, you can:

1. Create a Docker Compose service for ComfyUI
2. Connect both services via a Docker network
3. Use the service name as the server address

Example `docker-compose.yml` addition:

```yaml
services:
  comfyui:
    image: comfyui/comfyui:latest  # Or your custom image
    ports:
      - "8188:8188"
    # ... other ComfyUI config
  
  flux-generator-comfy:
    # ... existing config
    environment:
      - COMFYUI_SERVER_ADDRESS=comfyui:8188
    depends_on:
      - comfyui
```

## Troubleshooting

### Check if ComfyUI Server is Reachable

1. **From host machine:**
   ```bash
   curl http://127.0.0.1:8188/system_stats
   ```

2. **From Docker container:**
   ```bash
   docker exec -it flux-generator-comfy curl http://host.docker.internal:8188/system_stats
   ```

### Check Docker Logs

```bash
docker compose logs flux-generator-comfy | grep -i comfyui
```

Look for messages like:
- ✅ `ComfyUI provider initialized (server: host.docker.internal:8188)`
- ❌ `ComfyUI server not reachable at...`

### Verify Network Connectivity

Test if the container can reach the host:

```bash
# Test from inside container
docker exec -it flux-generator-comfy ping host.docker.internal
```

## Current Configuration

The `docker-compose.yml` file is configured to:
- Use `host.docker.internal:8188` by default (Windows/Mac)
- Allow you to override via `COMFYUI_SERVER_ADDRESS` environment variable
- Include commented Linux compatibility options

## Quick Fix

If ComfyUI isn't showing up:

1. **Make sure ComfyUI is running** on your host at `127.0.0.1:8188`
2. **Restart the Docker container:**
   ```bash
   docker compose --profile web restart flux-generator-comfy
   ```
3. **Check the UI** - you should see a status message about ComfyUI
4. **Check logs** if it still doesn't appear:
   ```bash
   docker compose logs flux-generator-comfy | grep -i comfyui
   ```

## Status Indicator

The UI will now show a status message if ComfyUI server is reachable but not initialized, or if it's not reachable at all. This helps you diagnose the issue quickly.




