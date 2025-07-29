"""
Image Storage Service for Facebook Messenger compatibility
"""

import aiohttp
import asyncio
import base64
import io
from typing import Optional, Dict, Any
from PIL import Image
import logging

logger = logging.getLogger(__name__)

class ImageStorageService:
    """Service to handle image storage for Facebook Messenger compatibility"""
    
    def __init__(self):
        self.session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def download_image(self, image_url: str) -> Optional[bytes]:
        """Download image from URL"""
        try:
            session = await self._get_session()
            timeout = aiohttp.ClientTimeout(total=30)
            
            async with session.get(image_url, timeout=timeout) as response:
                if response.status == 200:
                    image_data = await response.read()
                    logger.info("image_downloaded_successfully", url=image_url, size=len(image_data))
                    return image_data
                else:
                    logger.error("image_download_failed", url=image_url, status=response.status)
                    return None
                    
        except Exception as e:
            logger.error("image_download_exception", url=image_url, error=str(e))
            return None
    
    async def upload_to_imgur(self, image_data: bytes, client_id: str) -> Optional[str]:
        """Upload image to Imgur (Facebook-friendly)"""
        try:
            # Encode image as base64
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            
            session = await self._get_session()
            headers = {
                'Authorization': f'Client-ID {client_id}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'image': image_b64,
                'type': 'base64'
            }
            
            async with session.post('https://api.imgur.com/3/image', 
                                  headers=headers, 
                                  json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    imgur_url = result['data']['link']
                    logger.info("image_uploaded_to_imgur", url=imgur_url)
                    return imgur_url
                else:
                    logger.error("imgur_upload_failed", status=response.status)
                    return None
                    
        except Exception as e:
            logger.error("imgur_upload_exception", error=str(e))
            return None
    
    async def upload_to_cloudinary(self, image_data: bytes, cloud_name: str, api_key: str, api_secret: str) -> Optional[str]:
        """Upload image to Cloudinary (Facebook-friendly)"""
        try:
            # This would require cloudinary library
            # For now, return None to indicate not implemented
            logger.info("cloudinary_upload_not_implemented")
            return None
            
        except Exception as e:
            logger.error("cloudinary_upload_exception", error=str(e))
            return None
    
    async def get_facebook_compatible_url(self, original_url: str, 
                                        imgur_client_id: Optional[str] = None,
                                        cloudinary_config: Optional[Dict[str, str]] = None) -> str:
        """Get Facebook-compatible image URL"""
        try:
            # Strategy 1: Try original URL first
            if await self._test_facebook_compatibility(original_url):
                logger.info("original_url_facebook_compatible", url=original_url)
                return original_url
            
            # Strategy 2: Try Imgur if configured
            if imgur_client_id:
                logger.info("trying_imgur_upload")
                image_data = await self.download_image(original_url)
                if image_data:
                    imgur_url = await self.upload_to_imgur(image_data, imgur_client_id)
                    if imgur_url:
                        return imgur_url
            
            # Strategy 3: Try Cloudinary if configured
            if cloudinary_config:
                logger.info("trying_cloudinary_upload")
                image_data = await self.download_image(original_url)
                if image_data:
                    cloudinary_url = await self.upload_to_cloudinary(
                        image_data, 
                        cloudinary_config['cloud_name'],
                        cloudinary_config['api_key'],
                        cloudinary_config['api_secret']
                    )
                    if cloudinary_url:
                        return cloudinary_url
            
            # Fallback: Return original URL
            logger.warning("no_facebook_compatible_url_found", original_url=original_url)
            return original_url
            
        except Exception as e:
            logger.error("facebook_compatible_url_generation_failed", error=str(e))
            return original_url
    
    async def _test_facebook_compatibility(self, image_url: str) -> bool:
        """Test if image URL is Facebook-compatible"""
        try:
            session = await self._get_session()
            timeout = aiohttp.ClientTimeout(total=10)
            
            # Test basic accessibility
            async with session.head(image_url, timeout=timeout) as response:
                if response.status != 200:
                    return False
                
                content_type = response.headers.get('content-type', '')
                if not content_type.startswith('image/'):
                    return False
                
                # Check if it's from a Facebook-trusted domain
                trusted_domains = [
                    'imgur.com',
                    'cloudinary.com',
                    'amazonaws.com',
                    'cloudfront.net',
                    'cdn.jsdelivr.net',
                    'images.unsplash.com'
                ]
                
                for domain in trusted_domains:
                    if domain in image_url:
                        return True
                
                # For Supabase URLs, they might work but are less trusted
                if 'supabase.co' in image_url:
                    logger.info("supabase_url_detected", url=image_url)
                    return True  # Let's try it
                
                return False
                
        except Exception as e:
            logger.error("facebook_compatibility_test_failed", url=image_url, error=str(e))
            return False
    
    async def close(self):
        """Close the session"""
        if self.session and not self.session.closed:
            await self.session.close()

# Global instance
_image_storage_service = None

def get_image_storage_service() -> ImageStorageService:
    """Get global image storage service instance"""
    global _image_storage_service
    if _image_storage_service is None:
        _image_storage_service = ImageStorageService()
    return _image_storage_service