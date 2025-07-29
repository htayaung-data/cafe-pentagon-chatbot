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
            
            # Send response back to user
            await self.send_message(sender_id, response["response"])
            
            # Check if we need to send an image
            image_info = response.get("image_info")
            if image_info:
                # Send image after text message
                image_success = await self.send_image(
                    sender_id, 
                    image_info["image_url"], 
                    image_info["caption"]
                )
                logger.info("image_sent_after_response", 
                           sender_id=sender_id,
                           image_success=image_success)
            
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
        """Send image message"""
        try:
            url = f"{self.api_url}/me/messages?access_token={self.page_access_token}"
            headers = {
                "Content-Type": "application/json"
            }
            
            message_data = {
                "recipient": {"id": recipient_id},
                "message": {
                    "attachment": {
                        "type": "image",
                        "payload": {
                            "url": image_url
                        }
                    }
                }
            }
            
            # Add caption if provided
            if caption:
                message_data["message"]["attachment"]["payload"]["caption"] = caption
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=message_data) as response:
                    if response.status == 200:
                        logger.info("image_sent_successfully", recipient_id=recipient_id, image_url=image_url)
                        return True
                    else:
                        error_text = await response.text()
                        logger.error("image_send_failed", 
                                   recipient_id=recipient_id,
                                   status=response.status,
                                   error=error_text,
                                   image_url=image_url)
                        return False
                        
        except Exception as e:
            logger.error("image_send_exception", recipient_id=recipient_id, error=str(e), image_url=image_url)
            return False



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
