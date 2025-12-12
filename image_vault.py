"""
Image Vault - Automatic storage and management of generated images
"""

import json
import os
import uuid
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
from PIL import Image
import requests
import io

logger = logging.getLogger("flux_prompt")


class ImageVault:
    """Manages automatic storage of generated images"""
    
    def __init__(self, vault_dir: str = "vault/images"):
        """
        Initialize Image Vault
        
        Args:
            vault_dir: Directory where images are stored
        """
        base_dir = Path(__file__).parent.resolve()
        vault_path = Path(vault_dir)
        if not vault_path.is_absolute():
            vault_path = base_dir / vault_path
        
        self.vault_dir = vault_path
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        
        # Metadata file
        self.metadata_file = self.vault_dir / "vault_metadata.json"
        self.metadata = self._load_metadata()
        
        logger.info(f"Image Vault initialized at: {self.vault_dir}")
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load vault metadata from file"""
        if not self.metadata_file.exists():
            return {
                "images": {},
                "metadata": {
                    "created": datetime.now().isoformat(),
                    "total_images": 0,
                    "last_updated": datetime.now().isoformat()
                }
            }
        
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load vault metadata: {e}")
            return {
                "images": {},
                "metadata": {
                    "created": datetime.now().isoformat(),
                    "total_images": 0,
                    "last_updated": datetime.now().isoformat()
                }
            }
    
    def _save_metadata(self):
        """Save vault metadata to file"""
        try:
            self.metadata["metadata"]["last_updated"] = datetime.now().isoformat()
            self.metadata["metadata"]["total_images"] = len(self.metadata["images"])
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save vault metadata: {e}")
    
    def save_image(
        self,
        image_url: str,
        prompt: str,
        provider: str,
        model: str,
        style: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        source_type: str = "generated"  # "generated" or "edited"
    ) -> str:
        """
        Save an image to the vault
        
        Args:
            image_url: URL of the image to save
            prompt: Prompt used to generate the image
            provider: Provider used (openai, flux, etc.)
            model: Model used (dall-e-3, flux-pro, etc.)
            style: Image style (optional)
            metadata: Additional metadata (optional)
            source_type: Type of generation ("generated" or "edited")
            
        Returns:
            Image ID in vault
        """
        try:
            # Generate unique ID
            image_id = str(uuid.uuid4())[:8]
            timestamp = datetime.now()
            
            # Download image from URL
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # Save image file
            image_filename = f"{image_id}.png"
            image_path = self.vault_dir / image_filename
            
            with open(image_path, 'wb') as f:
                f.write(response.content)
            
            # Create metadata entry
            image_metadata = {
                "id": image_id,
                "filename": image_filename,
                "prompt": prompt,
                "provider": provider,
                "model": model,
                "style": style,
                "source_type": source_type,
                "timestamp": timestamp.isoformat(),
                "date": timestamp.strftime('%Y-%m-%d'),
                "time": timestamp.strftime('%H:%M:%S'),
                "metadata": metadata or {}
            }
            
            # Add to vault
            self.metadata["images"][image_id] = image_metadata
            self._save_metadata()
            
            logger.info(f"Image saved to vault: {image_id} ({image_filename})")
            return image_id
            
        except Exception as e:
            logger.error(f"Failed to save image to vault: {e}")
            raise
    
    def save_image_from_bytes(
        self,
        image_bytes: bytes,
        prompt: str,
        provider: str,
        model: str,
        style: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        source_type: str = "generated"
    ) -> str:
        """
        Save an image from bytes to the vault
        
        Args:
            image_bytes: Image data as bytes
            prompt: Prompt used to generate the image
            provider: Provider used
            model: Model used
            style: Image style (optional)
            metadata: Additional metadata (optional)
            source_type: Type of generation
            
        Returns:
            Image ID in vault
        """
        try:
            # Generate unique ID
            image_id = str(uuid.uuid4())[:8]
            timestamp = datetime.now()
            
            # Save image file
            image_filename = f"{image_id}.png"
            image_path = self.vault_dir / image_filename
            
            with open(image_path, 'wb') as f:
                f.write(image_bytes)
            
            # Create metadata entry
            image_metadata = {
                "id": image_id,
                "filename": image_filename,
                "prompt": prompt,
                "provider": provider,
                "model": model,
                "style": style,
                "source_type": source_type,
                "timestamp": timestamp.isoformat(),
                "date": timestamp.strftime('%Y-%m-%d'),
                "time": timestamp.strftime('%H:%M:%S'),
                "metadata": metadata or {}
            }
            
            # Add to vault
            self.metadata["images"][image_id] = image_metadata
            self._save_metadata()
            
            logger.info(f"Image saved to vault: {image_id} ({image_filename})")
            return image_id
            
        except Exception as e:
            logger.error(f"Failed to save image to vault: {e}")
            raise
    
    def get_image_path(self, image_id: str) -> Optional[Path]:
        """Get file path for an image by ID"""
        if image_id in self.metadata["images"]:
            filename = self.metadata["images"][image_id]["filename"]
            return self.vault_dir / filename
        return None
    
    def get_image_metadata(self, image_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for an image by ID"""
        return self.metadata["images"].get(image_id)
    
    def list_images(
        self,
        source_type: Optional[str] = None,
        provider: Optional[str] = None,
        style: Optional[str] = None,
        limit: Optional[int] = None,
        sort_by: str = "timestamp",
        reverse: bool = True
    ) -> List[Dict[str, Any]]:
        """
        List images in vault with optional filtering
        
        Args:
            source_type: Filter by source type ("generated" or "edited")
            provider: Filter by provider
            style: Filter by style
            limit: Maximum number of results
            sort_by: Sort field ("timestamp", "date", "provider")
            reverse: Sort in reverse order (newest first)
            
        Returns:
            List of image metadata dictionaries
        """
        images = list(self.metadata["images"].values())
        
        # Apply filters
        if source_type:
            images = [img for img in images if img.get("source_type") == source_type]
        
        if provider:
            images = [img for img in images if img.get("provider") == provider]
        
        if style:
            images = [img for img in images if img.get("style") == style]
        
        # Sort
        if sort_by == "timestamp":
            images.sort(key=lambda x: x.get("timestamp", ""), reverse=reverse)
        elif sort_by == "date":
            images.sort(key=lambda x: x.get("date", ""), reverse=reverse)
        elif sort_by == "provider":
            images.sort(key=lambda x: x.get("provider", ""), reverse=reverse)
        
        # Limit
        if limit:
            images = images[:limit]
        
        return images
    
    def delete_image(self, image_id: str) -> bool:
        """Delete an image from the vault"""
        if image_id not in self.metadata["images"]:
            return False
        
        try:
            # Delete image file
            image_path = self.get_image_path(image_id)
            if image_path and image_path.exists():
                image_path.unlink()
            
            # Remove from metadata
            del self.metadata["images"][image_id]
            self._save_metadata()
            
            logger.info(f"Image deleted from vault: {image_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete image: {e}")
            return False
    
    def get_vault_stats(self) -> Dict[str, Any]:
        """Get statistics about the vault"""
        images = self.metadata["images"]
        
        stats = {
            "total_images": len(images),
            "by_source_type": {},
            "by_provider": {},
            "by_style": {},
            "total_size_mb": 0,
        }
        
        # Calculate stats
        for img in images.values():
            # By source type
            source_type = img.get("source_type", "unknown")
            stats["by_source_type"][source_type] = stats["by_source_type"].get(source_type, 0) + 1
            
            # By provider
            provider = img.get("provider", "unknown")
            stats["by_provider"][provider] = stats["by_provider"].get(provider, 0) + 1
            
            # By style
            style = img.get("style") or "none"
            stats["by_style"][style] = stats["by_style"].get(style, 0) + 1
        
        # Calculate total size
        try:
            total_size = sum(
                (self.vault_dir / img["filename"]).stat().st_size
                for img in images.values()
                if (self.vault_dir / img["filename"]).exists()
            )
            stats["total_size_mb"] = round(total_size / (1024 * 1024), 2)
        except Exception:
            pass
        
        return stats
    
    def export_image(self, image_id: str, export_path: str) -> bool:
        """
        Export an image to a custom location
        
        Args:
            image_id: ID of image to export
            export_path: Destination path for export
            
        Returns:
            True if successful
        """
        image_path = self.get_image_path(image_id)
        if not image_path or not image_path.exists():
            return False
        
        try:
            shutil.copy2(image_path, export_path)
            logger.info(f"Image exported: {image_id} -> {export_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export image: {e}")
            return False

