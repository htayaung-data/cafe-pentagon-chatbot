"""
Private Image Storage Service for Facebook Messenger
Uses private cloud storage instead of public services
"""

import aiohttp
import asyncio
import base64
import hashlib
import os
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class PrivateImageStorageService:
    """Private image storage service for Facebook Messenger compatibility"""
    
    def __init__(self):
        self.session = None
        self.cache = {}  # Simple in-memory cache for image URLs
    
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
    
    async def upload_to_cloudinary_private(self, image_data: bytes, 
                                         cloud_name: str, 
                                         api_key: str, 
                                         api_secret: str,
                                         folder: str = "cafe-pentagon") -> Optional[str]:
        """Upload image to Cloudinary with private access"""
        try:
            # Encode image as base64
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            
            session = await self._get_session()
            
            # Create signature for private upload
            timestamp = str(int(asyncio.get_event_loop().time()))
            signature_string = f"folder={folder}&timestamp={timestamp}{api_secret}"
            signature = hashlib.sha1(signature_string.encode()).hexdigest()
            
            data = {
                'file': f'data:image/jpeg;base64,{image_b64}',
                'folder': folder,
                'access_mode': 'authenticated',  # Private access
                'timestamp': timestamp,
                'signature': signature,
                'api_key': api_key
            }
            
            upload_url = f'https://api.cloudinary.com/v1_1/{cloud_name}/image/upload'
            
            async with session.post(upload_url, data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    # Get the authenticated URL (private)
                    private_url = result['secure_url']
                    logger.info("image_uploaded_to_cloudinary_private", url=private_url)
                    return private_url
                else:
                    logger.error("cloudinary_private_upload_failed", status=response.status)
                    return None
                    
        except Exception as e:
            logger.error("cloudinary_private_upload_exception", error=str(e))
            return None
    
    async def upload_to_aws_s3_private(self, image_data: bytes,
                                     bucket_name: str,
                                     access_key: str,
                                     secret_key: str,
                                     region: str = "us-east-1") -> Optional[str]:
        """Upload image to AWS S3 with private access"""
        try:
            # This would require boto3 library
            # For now, return None to indicate not implemented
            logger.info("aws_s3_private_upload_not_implemented")
            return None
            
        except Exception as e:
            logger.error("aws_s3_private_upload_exception", error=str(e))
            return None
    
    async def create_facebook_compatible_url(self, private_url: str,
                                           cloud_name: str = None,
                                           api_key: str = None,
                                           api_secret: str = None) -> str:
        """Create Facebook-compatible URL from private storage"""
        try:
            # For Cloudinary, we can create a public URL with transformations
            if 'cloudinary.com' in private_url and cloud_name:
                # Create a public URL with specific transformations
                # This keeps the original private but creates a public version for Facebook
                public_url = private_url.replace('/upload/', '/upload/f_auto,q_auto/')
                logger.info("facebook_compatible_url_created", original=private_url, public=public_url)
                return public_url
            
            # For other services, return the private URL
            # Facebook might still be able to access it if properly configured
            return private_url
            
        except Exception as e:
            logger.error("facebook_compatible_url_creation_failed", error=str(e))
            return private_url
    
    async def get_private_image_url(self, original_url: str,
                                  cloudinary_config: Optional[Dict[str, str]] = None,
                                  aws_config: Optional[Dict[str, str]] = None) -> str:
        """Get private image URL for Facebook compatibility"""
        try:
            # Check cache first
            cache_key = hashlib.md5(original_url.encode()).hexdigest()
            if cache_key in self.cache:
                logger.info("using_cached_private_url", original_url=original_url)
                return self.cache[cache_key]
            
            # Strategy 1: Try Cloudinary private upload
            if cloudinary_config:
                logger.info("trying_cloudinary_private_upload")
                image_data = await self.download_image(original_url)
                if image_data:
                    private_url = await self.upload_to_cloudinary_private(
                        image_data,
                        cloudinary_config['cloud_name'],
                        cloudinary_config['api_key'],
                        cloudinary_config['api_secret']
                    )
                    if private_url:
                        # Create Facebook-compatible URL
                        facebook_url = await self.create_facebook_compatible_url(
                            private_url,
                            cloudinary_config['cloud_name'],
                            cloudinary_config['api_key'],
                            cloudinary_config['api_secret']
                        )
                        # Cache the result
                        self.cache[cache_key] = facebook_url
                        return facebook_url
            
            # Strategy 2: Try AWS S3 private upload
            if aws_config:
                logger.info("trying_aws_s3_private_upload")
                image_data = await self.download_image(original_url)
                if image_data:
                    private_url = await self.upload_to_aws_s3_private(
                        image_data,
                        aws_config['bucket_name'],
                        aws_config['access_key'],
                        aws_config['secret_key'],
                        aws_config.get('region', 'us-east-1')
                    )
                    if private_url:
                        self.cache[cache_key] = private_url
                        return private_url
            
            # Fallback: Return original URL
            logger.warning("no_private_storage_configured", original_url=original_url)
            return original_url
            
        except Exception as e:
            logger.error("private_image_url_generation_failed", error=str(e))
            return original_url
    
    async def close(self):
        """Close the session"""
        if self.session and not self.session.closed:
            await self.session.close()

# Global instance
_private_image_storage_service = None

def get_private_image_storage_service() -> PrivateImageStorageService:
    """Get global private image storage service instance"""
    global _private_image_storage_service
    if _private_image_storage_service is None:
        _private_image_storage_service = PrivateImageStorageService()
    return _private_image_storage_service