"""
Facebook Messenger Integration Service for Cafe Pentagon Chatbot
Handles webhook, message processing, and user management
"""

import hashlib
import hmac
import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import aiohttp
from fastapi import HTTPException, Request
from src.agents.main_agent import EnhancedMainAgent
from src.utils.logger import get_logger
from src.config.settings import get_settings
from src.data.models import UserProfile, Message, Conversation, LanguageEnum
from src.services.user_manager import UserManager
from src.services.image_storage_service import get_image_storage_service

logger = get_logger("facebook_messenger")


class FacebookMessengerService:
    """
    Facebook Messenger integration service
    """
    
    def __init__(self):
        """Initialize Facebook Messenger service"""
        self.settings = get_settings()
        self.main_agent = EnhancedMainAgent()
        self.user_manager = UserManager()
        self.page_access_token = self.settings.facebook_page_access_token
        self.verify_token = self.settings.facebook_verify_token
        self.api_url = "https://graph.facebook.com/v18.0"
        
        if not self.page_access_token:
            raise ValueError("Facebook Page Access Token not configured")
        
        logger.info("facebook_messenger_service_initialized")

    async def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """Verify webhook for Facebook Messenger"""
        if mode == "subscribe" and token == self.verify_token:
            logger.info("webhook_verified_successfully")
            return challenge
        else:
            logger.error("webhook_verification_failed", mode=mode, token=token)
            return None

    async def verify_signature(self, request: Request, body: bytes) -> bool:
        """Verify webhook signature for security"""
        try:
            signature = request.headers.get("x-hub-signature-256", "")
            if not signature.startswith("sha256="):
                return False
            
            expected_signature = "sha256=" + hmac.new(
                self.page_access_token.encode(),
                body,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.error("signature_verification_failed", error=str(e))
            return False

    async def process_webhook(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming webhook from Facebook"""
        try:
            if body.get("object") != "page":
                return {"status": "ignored", "reason": "not_page_object"}
            
            entries = body.get("entry", [])
            processed_messages = []
            
            for entry in entries:
                page_id = entry.get("id")
                messaging_events = entry.get("messaging", [])
                
                for event in messaging_events:
                    if "message" in event:
                        result = await self._handle_message(event)
                        processed_messages.append(result)
                    elif "postback" in event:
                        result = await self._handle_postback(event)
                        processed_messages.append(result)
            
            logger.info("webhook_processed", 
                       entries_count=len(entries),
                       messages_processed=len(processed_messages))
            
            return {
                "status": "success",
                "processed_messages": processed_messages
            }
            
        except Exception as e:
            logger.error("webhook_processing_failed", error=str(e))
            return {"status": "error", "error": str(e)}

    async def _handle_message(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming message from user"""
        try:
            sender_id = event["sender"]["id"]
            message_data = event["message"]
            
            # Extract message content
            if "text" in message_data:
                message_text = message_data["text"]
                message_type = "text"
            elif "attachments" in message_data:
                # Handle attachments (images, etc.)
                attachments = message_data["attachments"]
                message_text = f"[Attachment: {attachments[0].get('type', 'unknown')}]"
                message_type = "attachment"
            else:
                message_text = "[Unsupported message type]"
                message_type = "unsupported"
            
            # Get or create user profile with Facebook info
            facebook_profile = await self.get_user_info(sender_id)
            user_profile = await self.user_manager.get_or_create_user(sender_id, facebook_profile)
            
            # Process message with main agent (auto-detect language from message)
            response = await self.main_agent.chat(
                message_text,
                sender_id,
                None  # Let the agent auto-detect language from message content
            )
            
            # Check if we need to send an image first
            image_info = response.get("image_info")
            if image_info:
                logger.info("image_info_found", 
                           sender_id=sender_id,
                           image_info=image_info)
                
                # Send image first (without caption)
                image_success = await self.send_image_with_fallback(
                    sender_id, 
                    image_info["image_url"], 
                    ""  # No caption
                )
                logger.info("image_send_attempt_completed", 
                           sender_id=sender_id,
                           image_success=image_success,
                           image_url=image_info["image_url"])
                
                # If image sending failed, the fallback method already handled it
                # by sending a text message with the image URL
            else:
                logger.info("no_image_info_in_response", 
                           sender_id=sender_id,
                           response_keys=list(response.keys()))
            
            # Send text response after image (or immediately if no image)
            await self.send_message(sender_id, response["response"])
            
            # Update user profile with language preference
            if response.get("user_language") and response["user_language"] != user_profile.preferences.preferred_language.value:
                await self.user_manager.update_user_preferences(sender_id, {
                    "preferred_language": response["user_language"]
                })
            
            logger.info("message_processed", 
                       sender_id=sender_id,
                       message_type=message_type,
                       intent=response.get("primary_intent"),
                       image_sent=bool(image_info))
            
            return {
                "sender_id": sender_id,
                "message_type": message_type,
                "intent": response.get("primary_intent"),
                "status": "processed",
                "image_sent": bool(image_info)
            }
            
        except Exception as e:
            logger.error("message_handling_failed", error=str(e), event=event)
            return {"status": "error", "error": str(e)}

    async def _handle_postback(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Handle postback events (button clicks, etc.)"""
        try:
            sender_id = event["sender"]["id"]
            postback = event["postback"]
            payload = postback.get("payload", "")
            
            # Handle different postback types
            if payload.startswith("MENU_"):
                await self._handle_menu_postback(sender_id, payload)
            elif payload.startswith("ORDER_"):
                await self._handle_order_postback(sender_id, payload)
            elif payload.startswith("RESERVATION_"):
                await self._handle_reservation_postback(sender_id, payload)
            else:
                await self.send_message(sender_id, "I'm sorry, I didn't understand that action.")
            
            logger.info("postback_processed", sender_id=sender_id, payload=payload)
            
            return {
                "sender_id": sender_id,
                "postback_payload": payload,
                "status": "processed"
            }
            
        except Exception as e:
            logger.error("postback_handling_failed", error=str(e), event=event)
            return {"status": "error", "error": str(e)}

    async def send_message(self, recipient_id: str, message_text: str) -> bool:
        """Send message to Facebook user"""
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                url = f"{self.api_url}/me/messages?access_token={self.page_access_token}"
                headers = {
                    "Content-Type": "application/json"
                }
                data = {
                    "recipient": {"id": recipient_id},
                    "message": {"text": message_text}
                }
                
                timeout = aiohttp.ClientTimeout(total=30)  # 30 second timeout
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(url, headers=headers, json=data) as response:
                        if response.status == 200:
                            logger.info("message_sent_successfully", recipient_id=recipient_id)
                            return True
                        else:
                            error_text = await response.text()
                            logger.error("message_send_failed", 
                                       recipient_id=recipient_id,
                                       status=response.status,
                                       error=error_text,
                                       attempt=attempt + 1)
                            if attempt < max_retries - 1:
                                await asyncio.sleep(retry_delay)
                                continue
                            return False
                            
            except asyncio.TimeoutError:
                logger.error("message_send_timeout", 
                           recipient_id=recipient_id,
                           attempt=attempt + 1)
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                return False
            except Exception as e:
                logger.error("message_send_exception", 
                           recipient_id=recipient_id, 
                           error=str(e),
                           attempt=attempt + 1)
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    continue
                return False
        
        return False

    async def send_quick_replies(self, recipient_id: str, message_text: str, quick_replies: List[Dict[str, Any]]) -> bool:
        """Send message with quick reply buttons"""
        try:
            url = f"{self.api_url}/me/messages?access_token={self.page_access_token}"
            headers = {
                "Content-Type": "application/json"
            }
            data = {
                "recipient": {"id": recipient_id},
                "message": {
                    "text": message_text,
                    "quick_replies": quick_replies
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        logger.info("quick_replies_sent_successfully", recipient_id=recipient_id)
                        return True
                    else:
                        error_text = await response.text()
                        logger.error("quick_replies_send_failed", 
                                   recipient_id=recipient_id,
                                   status=response.status,
                                   error=error_text)
                        return False
                        
        except Exception as e:
            logger.error("quick_replies_send_exception", recipient_id=recipient_id, error=str(e))
            return False

    async def send_generic_template(self, recipient_id: str, elements: List[Dict[str, Any]]) -> bool:
        """Send generic template (for menu items, etc.)"""
        try:
            url = f"{self.api_url}/me/messages?access_token={self.page_access_token}"
            headers = {
                "Content-Type": "application/json"
            }
            data = {
                "recipient": {"id": recipient_id},
                "message": {
                    "attachment": {
                        "type": "template",
                        "payload": {
                            "template_type": "generic",
                            "elements": elements
                        }
                    }
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        logger.info("generic_template_sent_successfully", recipient_id=recipient_id)
                        return True
                    else:
                        error_text = await response.text()
                        logger.error("generic_template_send_failed", 
                                   recipient_id=recipient_id,
                                   status=response.status,
                                   error=error_text)
                        return False
                        
        except Exception as e:
            logger.error("generic_template_send_exception", recipient_id=recipient_id, error=str(e))
            return False

    async def send_image(self, recipient_id: str, image_url: str, caption: str = "") -> bool:
        """Send image message with improved error handling and Facebook compliance"""
        max_retries = 3
        retry_delay = 2  # seconds
        
        # Validate and fix image URL
        validated_url = self._validate_image_url_for_facebook(image_url)
        if not validated_url:
            logger.error("invalid_image_url_for_facebook", original_url=image_url)
            return False
        
        # Test if image URL is accessible (but don't fail if test fails)
        is_accessible = await self._test_image_url_accessibility(validated_url)
        if not is_accessible:
            logger.warning("image_url_accessibility_test_failed_but_continuing", image_url=validated_url)
            # Don't return False here - let Facebook try to access it anyway
        
        for attempt in range(max_retries):
            try:
                url = f"{self.api_url}/me/messages?access_token={self.page_access_token}"
                headers = {
                    "Content-Type": "application/json"
                }
                
                # Facebook Messenger requires specific image URL format
                # Ensure the image URL is publicly accessible and HTTPS
                payload = {
                    "recipient": {
                        "id": recipient_id
                    },
                    "message": {
                        "attachment": {
                            "type": "image",
                            "payload": {
                                "url": validated_url
                            }
                        }
                    }
                }
                
                # For Facebook Messenger, we'll send caption as a separate text message
                # if caption is provided, since image attachments don't support captions
                # in the same way as other platforms
                
                logger.info("attempting_to_send_image", 
                           recipient_id=recipient_id,
                           image_url=validated_url,
                           caption=caption,
                           attempt=attempt + 1)
                
                # Use longer timeout for image sending
                timeout = aiohttp.ClientTimeout(total=30, connect=15)
                
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(url, json=payload, headers=headers) as response:
                        if response.status == 200:
                            result = await response.json()
                            logger.info("image_sent_successfully", 
                                       recipient_id=recipient_id,
                                       message_id=result.get('message_id'),
                                       attempt=attempt + 1)
                            return True
                        else:
                            error_text = await response.text()
                            logger.error("image_send_failed", 
                                       recipient_id=recipient_id,
                                       status=response.status,
                                       error=error_text,
                                       attempt=attempt + 1)
                            
                            # If it's a permanent error, don't retry
                            if response.status in [400, 401, 403, 404]:
                                break
                            
                            # Wait before retry
                            if attempt < max_retries - 1:
                                await asyncio.sleep(retry_delay)
                                
            except asyncio.TimeoutError:
                logger.error("image_send_timeout", 
                           recipient_id=recipient_id,
                           attempt=attempt + 1)
                
                # If it's a timeout, try network connectivity handling
                if attempt == max_retries - 1:  # Last attempt
                    logger.info("trying_network_connectivity_handling")
                    return await self._handle_network_connectivity_issue(recipient_id, validated_url, caption)
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    
            except Exception as e:
                logger.error("image_send_exception", 
                           recipient_id=recipient_id,
                           error=str(e),
                           attempt=attempt + 1)
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
        
        logger.error("image_send_failed_after_retries", 
                   recipient_id=recipient_id,
                   max_retries=max_retries)
        return False

    async def send_image_alternative(self, recipient_id: str, image_url: str, caption: str = "") -> bool:
        """Alternative method to send images using Facebook's Media API"""
        try:
            # First, upload the image to Facebook's servers
            upload_url = f"{self.api_url}/me/message_attachments?access_token={self.page_access_token}"
            
            upload_data = {
                "message": {
                    "attachment": {
                        "type": "image",
                        "payload": {
                            "url": image_url,
                            "is_reusable": True
                        }
                    }
                }
            }
            
            # Upload the image
            timeout = aiohttp.ClientTimeout(total=60, connect=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(upload_url, json=upload_data) as response:
                    if response.status != 200:
                        logger.error("image_upload_failed", status=response.status)
                        return False
                    
                    upload_result = await response.json()
                    attachment_id = upload_result.get("attachment_id")
                    
                    if not attachment_id:
                        logger.error("no_attachment_id_received")
                        return False
                    
                    # Now send the message with the uploaded image
                    message_url = f"{self.api_url}/me/messages?access_token={self.page_access_token}"
                    message_data = {
                        "recipient": {"id": recipient_id},
                        "message": {
                            "attachment": {
                                "type": "image",
                                "payload": {
                                    "attachment_id": attachment_id
                                }
                            }
                        }
                    }
                    
                                         # For Facebook Messenger, captions are not supported in image attachments
                     # We'll send the caption as a separate text message if needed
                    
                    async with session.post(message_url, json=message_data) as msg_response:
                        if msg_response.status == 200:
                            logger.info("image_sent_via_media_api", recipient_id=recipient_id)
                            return True
                        else:
                            logger.error("image_send_via_media_api_failed", status=msg_response.status)
                            return False
                            
        except Exception as e:
            logger.error("alternative_image_send_failed", error=str(e))
            return False

    async def test_api_connectivity(self) -> Dict[str, Any]:
        """Test Facebook Messenger API connectivity and permissions"""
        try:
            # Test basic API access
            url = f"{self.api_url}/me?access_token={self.page_access_token}"
            
            # Use longer timeout for connectivity test
            timeout = aiohttp.ClientTimeout(total=30, connect=15)  # 30 second total timeout, 15 second connect timeout
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        page_info = await response.json()
                        logger.info("facebook_api_connectivity_test_passed", 
                                   page_id=page_info.get('id'),
                                   page_name=page_info.get('name'))
                        
                        return {
                            "status": "success",
                            "page_info": page_info,
                            "api_version": "v18.0"
                        }
                    else:
                        error_text = await response.text()
                        logger.error("facebook_api_connectivity_test_failed", 
                                   status=response.status,
                                   error=error_text)
                        
                        return {
                            "status": "failed",
                            "error": error_text,
                            "status_code": response.status
                        }
                        
        except asyncio.TimeoutError:
            logger.error("facebook_api_connectivity_test_timeout")
            return {
                "status": "timeout",
                "error": "Connection timeout - check network connectivity and Facebook API status"
            }
        except Exception as e:
            logger.error("facebook_api_connectivity_test_exception", error=str(e))
            return {
                "status": "exception",
                "error": str(e)
            }

    async def test_image_sending(self, recipient_id: str, test_image_url: str = None) -> Dict[str, Any]:
        """Test image sending functionality"""
        try:
            # Use a test image if none provided
            if not test_image_url:
                test_image_url = "https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop"
            
            logger.info("testing_image_sending", 
                       recipient_id=recipient_id,
                       test_image_url=test_image_url)
            
            # Test sending a simple image
            success = await self.send_image(
                recipient_id,
                test_image_url,
                "Test image from Cafe Pentagon Chatbot"
            )
            
            return {
                "status": "success" if success else "failed",
                "image_sent": success,
                "test_image_url": test_image_url
            }
            
        except Exception as e:
            logger.error("image_sending_test_exception", error=str(e))
            return {
                "status": "exception",
                "error": str(e)
            }



    async def _handle_menu_postback(self, sender_id: str, payload: str) -> None:
        """Handle menu-related postback actions"""
        # TODO: Implement menu browsing logic
        await self.send_message(sender_id, "Menu browsing feature coming soon!")

    async def _handle_order_postback(self, sender_id: str, payload: str) -> None:
        """Handle order-related postback actions"""
        # TODO: Implement ordering logic
        await self.send_message(sender_id, "Ordering feature coming soon!")

    async def _handle_reservation_postback(self, sender_id: str, payload: str) -> None:
        """Handle reservation-related postback actions"""
        # TODO: Implement reservation logic
        await self.send_message(sender_id, "Reservation feature coming soon!")

    async def get_user_info(self, facebook_id: str) -> Optional[Dict[str, Any]]:
        """Get user information from Facebook"""
        try:
            url = f"{self.api_url}/{facebook_id}"
            params = {
                "fields": "id,name,first_name,last_name,profile_pic",
                "access_token": self.page_access_token
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error("user_info_fetch_failed", 
                                   facebook_id=facebook_id,
                                   status=response.status)
                        return None
                        
        except Exception as e:
            logger.error("user_info_fetch_exception", facebook_id=facebook_id, error=str(e))
            return None 

    def _validate_image_url_for_facebook(self, image_url: str) -> str:
        """Validate and fix image URL for Facebook Messenger compatibility"""
        try:
            # Ensure HTTPS
            if image_url.startswith('http://'):
                image_url = image_url.replace('http://', 'https://')
            
            # Fix any double slashes in the URL (except for https://)
            if 'https://' in image_url:
                protocol = 'https://'
                rest_of_url = image_url[8:]  # Remove 'https://'
                # Replace any remaining double slashes with single slash
                rest_of_url = rest_of_url.replace('//', '/')
                image_url = protocol + rest_of_url
            
            # Check if URL is from Supabase and fix if needed
            if 'supabase.co' in image_url:
                # Fix double slash issues in Supabase URLs
                # Check for double slash anywhere in the URL after the domain
                if '/storage/v1/object/public/' in image_url:
                    parts = image_url.split('/storage/v1/object/public/')
                    if len(parts) == 2:
                        bucket_path = parts[0] + '/storage/v1/object/public/'
                        filename = parts[1]
                        
                        # Fix any double slashes in the filename
                        if '//' in filename:
                            filename = filename.replace('//', '/')
                            fixed_url = bucket_path + filename
                            logger.info("fixed_supabase_double_slash", 
                                      original_url=image_url,
                                      fixed_url=fixed_url)
                            image_url = fixed_url
                
                # Ensure proper Supabase storage URL format
                if '/storage/v1/object/public/' in image_url:
                    logger.info("supabase_image_url_validated", image_url=image_url)
                    return image_url
                else:
                    logger.warning("invalid_supabase_url_format", image_url=image_url)
            
            # For other URLs, ensure they're HTTPS and publicly accessible
            if not image_url.startswith('https://'):
                logger.error("image_url_not_https", image_url=image_url)
                return ""
            
            return image_url
            
        except Exception as e:
            logger.error("image_url_validation_failed", image_url=image_url, error=str(e))
            return ""

    async def _test_image_url_accessibility(self, image_url: str) -> bool:
        """Test if image URL is accessible from Facebook's servers"""
        try:
            timeout = aiohttp.ClientTimeout(total=10, connect=5)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.head(image_url) as response:
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '')
                        if content_type.startswith('image/'):
                            logger.info("image_url_accessible", image_url=image_url, content_type=content_type)
                            return True
                        else:
                            logger.warning("url_not_image_content", image_url=image_url, content_type=content_type)
                            return False
                    else:
                        logger.warning("image_url_not_accessible", image_url=image_url, status=response.status)
                        return False
                        
        except Exception as e:
            logger.error("image_url_accessibility_test_failed", image_url=image_url, error=str(e))
            return False 

    async def _get_alternative_image_url(self, original_url: str) -> str:
        """Get alternative image URL if original doesn't work with Facebook"""
        try:
            # Use the image storage service to get Facebook-compatible URLs
            image_storage_service = get_image_storage_service()
            
            # Get Imgur client ID from environment (optional)
            import os
            imgur_client_id = os.getenv('IMGUR_CLIENT_ID')
            
            # Get Cloudinary config from environment (optional)
            cloudinary_config = None
            cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME')
            api_key = os.getenv('CLOUDINARY_API_KEY')
            api_secret = os.getenv('CLOUDINARY_API_SECRET')
            
            if cloud_name and api_key and api_secret:
                cloudinary_config = {
                    'cloud_name': cloud_name,
                    'api_key': api_key,
                    'api_secret': api_secret
                }
            
            # Get Facebook-compatible URL
            compatible_url = await image_storage_service.get_facebook_compatible_url(
                original_url,
                imgur_client_id=imgur_client_id,
                cloudinary_config=cloudinary_config
            )
            
            if compatible_url != original_url:
                logger.info("facebook_compatible_url_generated", 
                           original_url=original_url,
                           compatible_url=compatible_url)
            
            return compatible_url
            
        except Exception as e:
            logger.error("alternative_image_url_generation_failed", original_url=original_url, error=str(e))
            return original_url

    async def send_image_with_fallback(self, recipient_id: str, image_url: str, caption: str = "") -> bool:
        """Send image with multiple fallback strategies"""
        try:
            # Strategy 1: Try original URL (with validation fixes)
            logger.info("trying_original_image_url", image_url=image_url)
            success = await self.send_image(recipient_id, image_url, caption)
            if success:
                return True
            
            # Strategy 2: Try alternative URL (Imgur/Cloudinary)
            logger.info("trying_alternative_image_url")
            alternative_url = await self._get_alternative_image_url(image_url)
            if alternative_url != image_url:
                success = await self.send_image(recipient_id, alternative_url, caption)
                if success:
                    return True
            
            # Strategy 3: Try alternative sending method (Media API)
            logger.info("trying_alternative_sending_method")
            success = await self.send_image_alternative(recipient_id, image_url, caption)
            if success:
                return True
            
            # Strategy 4: Try with network connectivity handling
            logger.info("trying_network_connectivity_handling")
            success = await self._handle_network_connectivity_issue(recipient_id, image_url, caption)
            if success:
                return True
            
            # Strategy 5: Send text with image URL as last resort
            logger.warning("all_image_sending_methods_failed_sending_text_fallback")
            fallback_message = f"📸 View image: {image_url}"
            await self.send_message(recipient_id, fallback_message)
            return True
            
        except Exception as e:
            logger.error("send_image_with_fallback_failed", error=str(e))
            return False 

    async def _handle_network_connectivity_issue(self, recipient_id: str, image_url: str, caption: str = "") -> bool:
        """Handle network connectivity issues with Facebook APIs"""
        try:
            logger.warning("facebook_network_connectivity_issue_detected")
            
            # Strategy 1: Try with different timeout settings
            logger.info("trying_extended_timeout_for_facebook")
            
            # Use much longer timeout for network issues
            timeout = aiohttp.ClientTimeout(total=60, connect=30)
            
            url = f"{self.api_url}/me/messages?access_token={self.page_access_token}"
            headers = {"Content-Type": "application/json"}
            
            payload = {
                "recipient": {"id": recipient_id},
                "message": {
                    "attachment": {
                        "type": "image",
                        "payload": {"url": image_url}
                    }
                }
            }
            
            # For Facebook Messenger, captions are not supported in image attachments
            # We'll send the caption as a separate text message if needed
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        logger.info("image_sent_with_extended_timeout")
                        return True
                    else:
                        logger.error("extended_timeout_failed", status=response.status)
            
            # Strategy 2: Try alternative Facebook API endpoints
            logger.info("trying_alternative_facebook_endpoints")
            
            # Try different Facebook API versions or endpoints
            alternative_urls = [
                f"https://graph.facebook.com/v18.0/me/messages?access_token={self.page_access_token}",
                f"https://graph.facebook.com/v17.0/me/messages?access_token={self.page_access_token}",
                f"https://graph.facebook.com/v16.0/me/messages?access_token={self.page_access_token}"
            ]
            
            for alt_url in alternative_urls:
                try:
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.post(alt_url, json=payload, headers=headers) as response:
                            if response.status == 200:
                                logger.info("image_sent_with_alternative_endpoint", url=alt_url)
                                return True
                except Exception as e:
                    logger.warning("alternative_endpoint_failed", url=alt_url, error=str(e))
                    continue
            
            # Strategy 3: Send as text with image URL
            logger.info("sending_text_with_image_url_as_fallback")
            fallback_message = f"📸 View image: {image_url}"
            await self.send_message(recipient_id, fallback_message)
            
            return True
            
        except Exception as e:
            logger.error("network_connectivity_handling_failed", error=str(e))
            return False 
