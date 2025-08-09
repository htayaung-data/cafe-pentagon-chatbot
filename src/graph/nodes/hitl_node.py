"""
HITL (Human-in-the-Loop) Node for Simplified LangGraph
Handles human escalation detection and management using pure LLM analysis
"""

from typing import Dict, Any, Optional
from src.services.escalation_service import EscalationService
from src.services.conversation_tracking_service import get_conversation_tracking_service
from src.utils.api_client import get_openai_client
from src.utils.logger import get_logger

logger = get_logger("hitl_node")


class HITLNode:
    """
    LangGraph node for HITL (Human-in-the-Loop) management using pure LLM analysis
    Detects escalation needs and manages human handoff without pattern matching
    """
    
    def __init__(self):
        """Initialize HITL node"""
        self.escalation_service = EscalationService()
        self.conversation_tracking = get_conversation_tracking_service()
        self.openai_client = get_openai_client()
        from src.config.settings import get_settings
        self.settings = get_settings()
        logger.info("hitl_node_initialized")
    
    async def check_escalation(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if conversation needs human escalation using pure LLM analysis
        
        Args:
            state: Current conversation state
            
        Returns:
            Updated state with escalation decision
        """
        user_message = state.get("user_message", "")
        conversation_id = state.get("conversation_id", "")
        user_id = state.get("user_id", "")
        user_language = state.get("user_language", "en")
        response_strategy = state.get("response_strategy", "polite_fallback")
        analysis_confidence = state.get("analysis_confidence", 0.0)
        
        if not conversation_id:
            logger.warning("no_conversation_id_for_escalation_check", user_id=user_id)
            return state
        
        try:
            # Check if conversation is already escalated
            is_escalated = self.conversation_tracking.is_conversation_escalated(conversation_id)
            
            if is_escalated:
                logger.info("conversation_already_escalated", 
                           conversation_id=conversation_id,
                           user_id=user_id)

                # When admin has taken over, bot must not reply. Block downstream generation.
                updated_state = state.copy()
                updated_state.update({
                    "requires_human": True,
                    "human_handling": True,
                    "escalation_reason": "admin_locked",
                    "escalation_blocked": True,
                    "response_generated": False
                })
                return updated_state
            
            # Use pure LLM analysis to determine if escalation is needed
            requires_human = await self._llm_check_escalation_needed(
                user_message=user_message,
                user_language=user_language,
                response_strategy=response_strategy,
                analysis_confidence=analysis_confidence
            )
            
            if requires_human:
                # Mark message as requires_human and update conversation metadata for admin visibility.
                # Do NOT flip human_handling or rag_enabled here; only admin can lock the conversation.
                try:
                    # Use LLM to determine escalation reason (brief)
                    escalation_reason = await self._llm_determine_escalation_reason(
                    user_message=user_message,
                    user_language=user_language,
                    response_strategy=response_strategy,
                    analysis_confidence=analysis_confidence
                    )

                    # Update conversation metadata only (do not lock)
                    updates = {
                        "escalation_reason": escalation_reason,
                        "escalation_timestamp": "now()",
                        "priority": 2
                    }
                    self.conversation_tracking.update_conversation(conversation_id, updates=updates)
                except Exception as e:
                    logger.warning("escalation_metadata_update_failed", conversation_id=conversation_id, error=str(e))

                # Allow normal flow to continue (no blocking, no overriding of response).
                updated_state = state.copy()
                updated_state.update({
                    "requires_human": True,
                    "human_handling": False,
                    "escalation_blocked": False
                })
                return updated_state
            
            # No escalation needed
            updated_state = state.copy()
            updated_state.update({
                "requires_human": False,
                "human_handling": False,
                "escalation_reason": None
            })
            
            return updated_state
            
        except Exception as e:
            logger.error("escalation_check_failed", 
                        conversation_id=conversation_id,
                        error=str(e))
            return state
    
    async def _llm_check_escalation_needed(self, user_message: str, user_language: str, 
                                         response_strategy: str, analysis_confidence: float) -> bool:
        """
        Use LLM to determine if escalation is needed (no pattern matching)
        
        Args:
            user_message: User's input message
            user_language: User's language
            response_strategy: Response strategy from analysis
            analysis_confidence: Confidence score from analysis
            
        Returns:
            True if escalation is needed, False otherwise
        """
        try:
            # Do not hard-block on strategy; LLM decision takes precedence
            # Do not escalate solely due to low confidence; require explicit LLM confirmation
            if analysis_confidence < 0.1:
                pass
            
            # Create prompt for LLM analysis
            if user_language == "my":
                prompt = f"""
သင့်အနေနဲ့ ဒီအသုံးပြုသူရဲ့ မေးခွန်းကို စစ်ဆေးပြီး လူသားဝန်ထမ်းတစ်ယောက်နဲ့ ဆက်သွယ်ဖို့ လိုအပ်သလား ဆုံးဖြတ်ပေးပါ။

အသုံးပြုသူ မေးခွန်း: "{user_message}"

ဆုံးဖြတ်ချက် ချမှတ်ရန် စံနှုန်းများ:
- လူသားဝန်ထမ်းနဲ့ ဆက်သွယ်လိုတဲ့ တောင်းဆိုချက် (တာဝန်ရှိသူ၊ တာဝန်ခံ၊ မန်နေဂျာ၊ အုပ်ချုပ်သူနဲ့ ပြောချင်တယ်)
- ရှုပ်ထွေးတဲ့ ပြဿနာများ သို့မဟုတ် တိုင်ကြားချက်များ
- အထူးတောင်းဆိုချက်များ (ဓာတ်မတည့်ခြင်း၊ အထူးစီစဉ်ချက်များ)
- ငွေကြေးဆိုင်ရာ ပြဿနာများ
- ရှုပ်ထွေးတဲ့ စီစဉ်ချက်များ

မလိုအပ်တဲ့ အချက်များ:
- ယေဘုယျ မေးခွန်းများ (ဥပမာ - မွေးနေ့ပွဲလုပ်လို့ ရလား၊ ဆိုင်လိပ်စာ ကဘယ်မှာလဲ)
- သတင်းအချက်အလက် ရှာဖွေခြင်း
- ရိုးရှင်းတဲ့ မေးခွန်းများ

အသေအချာ ဥပမာများ:
- "တာဝန်ရှိသူနဲ့ ပြောချင်ပါတယ်", "မန်နေဂျာနဲ့ ပြောချင်တယ်", "တာဝန်ရှိသူ တစ်ယောက်နဲ့ ဆက်သွယ်ချင်တယ်" → yes
- "မွေးနေ့ပွဲ လုပ်လို့ ရလား", "လိပ်စာ ဘယ်မှာလဲ" → no

အဖြေ: လူသားဝန်ထမ်းနဲ့ ဆက်သွယ်ဖို့ လိုအပ်ရင် "yes"၊ မလိုအပ်ရင် "no" ပြောပါ။ အခြား စာသား မထည့်ပါနဲ့။
"""
            else:
                prompt = f"""
You are analyzing a user's question to determine if they need to speak with a human staff member.

User question: "{user_message}"

Decision criteria:
- Requests to speak with human staff (manager, supervisor, person in charge, responsible person)
- Complex problems or complaints
- Special requests (allergies, custom arrangements)
- Payment or billing issues
- Complex booking arrangements

NOT needed for:
- General questions (e.g., "Can I have a birthday party?", "What's your address?")
- Information seeking
- Simple questions

Clear examples:
- "I want to talk to the manager", "Can I speak to the person in charge?", "I need to talk to someone" → yes
- "Can I have a birthday party?", "What are your hours?" → no

Answer: Say "yes" if human assistance is needed, "no" if not needed. Do not add any other text.
"""
            
            # Get LLM response (deterministic in tests)
            if self.settings.test_mode:
                # Simple rule: escalate if message mentions manager/complaint keywords or Burmese equivalents
                lower = user_message.lower()
                needs = any(k in lower for k in ["manager", "supervisor", "complaint", "billing", "payment"])
                needs = needs or any(k in user_message for k in ["တာဝန်ရှိသူ", "တိုင်ကြား", "ငွေ", "အထူးစီစဉ်"])
                llm_response = "yes" if needs or analysis_confidence < 0.3 else "no"
            else:
                response = await self.openai_client.chat_completion(
                    messages=[{"role": "user", "content": prompt}],
                    model=self.settings.openai_model,
                    max_tokens=10,
                    temperature=0.1
                )
                llm_response = response.choices[0].message.content.strip().lower()
            
            # Parse response
            if "yes" in llm_response or "လိုအပ်" in llm_response or "ဟုတ်" in llm_response or "ရ" in llm_response:
                logger.info("llm_escalation_triggered", 
                           user_message=user_message[:100],
                           llm_response=llm_response)
                return True
            else:
                logger.info("llm_escalation_not_needed", 
                           user_message=user_message[:100],
                           llm_response=llm_response)
                return False
                
        except Exception as e:
            logger.error("llm_escalation_check_failed", error=str(e))
            # Fallback to confidence-based decision
            return analysis_confidence < 0.5
    
    async def _llm_determine_escalation_reason(self, user_message: str, user_language: str,
                                             response_strategy: str, analysis_confidence: float) -> str:
        """
        Use LLM to determine escalation reason (no pattern matching)
        
        Args:
            user_message: User's input message
            user_language: User's language
            response_strategy: Response strategy from analysis
            analysis_confidence: Confidence score from analysis
            
        Returns:
            Escalation reason string
        """
        try:
            if analysis_confidence < 0.3:
                return f"Low confidence in analysis ({analysis_confidence:.2f})"
            
            # Create prompt for LLM analysis
            if user_language == "my":
                prompt = f"""
အသုံးပြုသူရဲ့ မေးခွန်းကို ကြည့်ပြီး လူသားဝန်ထမ်းနဲ့ ဆက်သွယ်ရတဲ့ အကြောင်းရင်းကို ရှင်းပြပေးပါ။

အသုံးပြုသူ မေးခွန်း: "{user_message}"

အကြောင်းရင်း ရှင်းပြချက်: (တိုတိုနဲ့ ရှင်းရှင်းပဲ ရေးပါ)
"""
            else:
                prompt = f"""
Look at the user's question and explain why they need to speak with a human staff member.

User question: "{user_message}"

Reason: (Keep it brief and clear)
"""
            
            # Get LLM response (deterministic in tests)
            if self.settings.test_mode:
                if user_language == "my":
                    reason = "အသုံးပြုသူက တာဝန်ရှိသူနဲ့ ဆက်သွယ်လိုပါတယ်။"
                else:
                    reason = "User requested to speak with a manager or raised a complex issue."
            else:
                response = await self.openai_client.chat_completion(
                    messages=[{"role": "user", "content": prompt}],
                    model=self.settings.openai_model,
                    max_tokens=50,
                    temperature=0.1
                )
                reason = response.choices[0].message.content.strip()
            logger.info("llm_escalation_reason_determined", 
                       user_message=user_message[:100],
                       reason=reason)
            
            return reason
                
        except Exception as e:
            logger.error("llm_escalation_reason_failed", error=str(e))
            return "Complex request requiring human expertise"
    
    def _get_escalation_response(self, user_language: str, user_message: str = "") -> str:
        """
        Get escalation response in user's language
        
        Args:
            user_language: User's language (en, my)
            user_message: User's message for context
            
        Returns:
            Escalation response in appropriate language
        """
        # Check if this is a follow-up question about waiting
        if user_language == "my":
            if any(word in user_message for word in ["စောင့်", "ကြာ", "ဘယ်လောက်", "ဘယ်အချိန်"]):
                return "တာဝန်ရှိဝန်ထမ်း တစ်ဦး လာပြီးကူညီဆောင်ရွက်ပေးပါလိမ့်မယ် ခင်ဗျာ။ ခဏလေး စောင့်ပေးပါနော်..."
            elif any(word in user_message for word in ["မေးခဲ့", "ပြောခဲ့", "ဘာတွေ"]):
                return "သင့်မေးခွန်းများကို ကျွန်ုပ်တို့ မှတ်သားထားပါသည်။ တာဝန်ရှိဝန်ထမ်း တစ်ဦး လာပြီးကူညီဆောင်ရွက်ပေးပါလိမ့်မယ် ခင်ဗျာ။"
            else:
                return "တာဝန်ရှိဝန်ထမ်း တစ်ဦး လာပြီးကူညီဆောင်ရွက်ပေးပါလိမ့်မယ် ခင်ဗျာ။ ခဏလေး စောင့်ပေးပါနော်..."
        else:
            if any(word in user_message.lower() for word in ["wait", "long", "how long", "when"]):
                return "The responsible person is informed for this case, he will come and solve soon, kindly wait a moment."
            elif any(word in user_message.lower() for word in ["asked", "said", "what"]):
                return "We have noted your questions. The responsible person is informed for this case, he will come and solve soon."
            else:
                return "The responsible person is informed for this case, he will come and solve soon, kindly wait a moment."
