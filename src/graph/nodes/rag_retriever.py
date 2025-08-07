"""
RAG Retriever Node for LangGraph
Adapts the sophisticated search logic from previous implementation to work within LangGraph's intent-based routing
"""

from typing import Dict, Any, List, Optional
from src.services.vector_search_service import get_vector_search_service
from src.utils.logger import get_logger

logger = get_logger("rag_retriever_node")


class RAGRetrieverNode:
    """
    LangGraph node for RAG retrieval
    Adapts sophisticated search logic to work within LangGraph's intent-based routing
    """
    
    def __init__(self):
        """Initialize RAG retriever node"""
        self.vector_search = get_vector_search_service()
        logger.info("rag_retriever_node_initialized")
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieve relevant documents using analysis results and routing decisions
        
        Args:
            state: Current conversation state with analysis and routing results
            
        Returns:
            Updated state with retrieved documents and relevance scores
        """
        user_message = state.get("user_message", "")
        analysis_result = state.get("analysis_result", {})
        routing_decision = state.get("routing_decision", {})
        
        # Extract information from analysis result
        detected_language = analysis_result.get("detected_language", "en")
        primary_intent = analysis_result.get("primary_intent", "")
        intent_confidence = analysis_result.get("intent_confidence", 0.0)
        search_context = analysis_result.get("search_context", {})
        target_namespace = search_context.get("namespace", "")
        
        # Extract information from routing decision
        action_type = routing_decision.get("action_type", "")
        rag_enabled = routing_decision.get("rag_enabled", True)
        
        # Skip if RAG is not enabled or action type is not perform_search
        if not rag_enabled or action_type != "perform_search":
            logger.info("rag_skipped", 
                       action_type=action_type,
                       rag_enabled=rag_enabled)
            return self._set_empty_results(state)
        
        if not user_message or not target_namespace:
            logger.warning("missing_required_fields", 
                          user_message=bool(user_message),
                          target_namespace=bool(target_namespace))
            return self._set_empty_results(state)
        
        # Skip RAG if confidence is too low
        if intent_confidence < 0.3:
            logger.info("low_intent_confidence_skip_rag", 
                       intent=primary_intent,
                       confidence=intent_confidence)
            return self._set_empty_results(state)
        
        try:
            # Get conversation history for context
            conversation_history = state.get("conversation_history", [])
            
            # For Burmese queries, use sophisticated search logic adapted to namespace routing
            if detected_language == "my":
                documents = await self._search_burmese_with_namespace(user_message, target_namespace, detected_language, conversation_history)
            else:
                # For English queries, use the original namespace-based approach
                documents = await self._search_english_with_namespace(user_message, target_namespace, detected_language, conversation_history)
            
            # Calculate relevance score
            relevance_score = 0.9 if documents else 0.0
            
            # Log retrieval results
            logger.info("rag_retrieval_completed",
                       namespace=target_namespace,
                       intent=primary_intent,
                       results_count=len(documents),
                       relevance_score=relevance_score,
                       language=detected_language)
            
            # Update state with retrieval results
            updated_state = state.copy()
            updated_state.update({
                "rag_results": documents,
                "relevance_score": relevance_score,
                "search_metadata": {
                    "search_type": "adapted_sophisticated" if detected_language == "my" else "namespace_based",
                    "language": detected_language,
                    "total_results": len(documents),
                    "target_namespace": target_namespace
                },
                "retrieved_count": len(documents),
                "search_query": user_message,
                "search_namespace": target_namespace
            })
            
            return updated_state
            
        except Exception as e:
            logger.error("rag_retrieval_failed",
                        error=str(e),
                        namespace=target_namespace,
                        user_message=user_message[:100])
            
            # Return empty results on error
            return self._set_empty_results(state)
    
    async def _search_burmese_with_namespace(self, user_message: str, target_namespace: str, language: str, conversation_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Search using sophisticated logic adapted to namespace routing"""
        try:
            # Use the sophisticated search method but filter by namespace
            search_results = await self.vector_search.search_pinecone_for_data(user_message, language)
            
            documents = []
            
            # Filter results based on target namespace
            if target_namespace == "faq" and search_results.get("found_faq") and search_results.get("faq_results"):
                for faq in search_results["faq_results"]:
                    # Use Burmese content directly
                    question = faq.get('question_mm', faq.get('question_en', ''))
                    answer = faq.get('answer_mm', faq.get('answer_en', ''))
                    content = f"Q: {question}\nA: {answer}"
                    
                    documents.append({
                        "content": content,
                        "metadata": faq,
                        "score": 0.9,
                        "source": "faq"
                    })
            
            elif target_namespace == "menu" and search_results.get("found_menu") and search_results.get("menu_results"):
                for item in search_results["menu_results"]:
                    # Use Burmese content directly
                    item_name = item.get('myanmar_name', item.get('name', ''))
                    description = item.get('description_mm', item.get('description', ''))
                    content = f"{item_name}: {description}"
                    
                    documents.append({
                        "content": content,
                        "metadata": item,
                        "score": 0.9,
                        "source": "menu"
                    })
            
            elif target_namespace == "jobs" and search_results.get("found_events") and search_results.get("events_results"):
                for event in search_results["events_results"]:
                    # Use Burmese content directly
                    title = event.get('title_mm', event.get('title_en', ''))
                    description = event.get('description_mm', event.get('description_en', ''))
                    content = f"{title}: {description}"
                    
                    documents.append({
                        "content": content,
                        "metadata": event,
                        "score": 0.9,
                        "source": "jobs"
                    })
            
            return documents
            
        except Exception as e:
            logger.error("burmese_namespace_search_failed", error=str(e))
            return []
    
    async def _search_english_with_namespace(self, user_message: str, target_namespace: str, language: str, conversation_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Search using original namespace-based approach for English"""
        try:
            conversation_history = []
            
            # Query Pinecone based on namespace
            if target_namespace == "menu":
                search_results = await self._search_menu_namespace(user_message, language, conversation_history)
            elif target_namespace == "faq":
                search_results = await self._search_faq_namespace(user_message, language)
            elif target_namespace == "jobs":
                search_results = await self._search_job_namespace(user_message, language)
            else:
                search_results = await self._search_faq_namespace(user_message, language)
            
            return search_results.get("documents", [])
            
        except Exception as e:
            logger.error("english_namespace_search_failed", error=str(e))
            return []
    
    async def _search_menu_namespace(self, user_message: str, language: str, conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Search menu namespace using direct Pinecone query"""
        try:
            # Query Pinecone menu namespace directly
            query_vector = await self.vector_search.embeddings.aembed_query(user_message)
            
            # Search in menu namespace
            search_response = self.vector_search.pinecone_index.query(
                vector=query_vector,
                namespace="menu",
                top_k=10,
                include_metadata=True
            )
            
            documents = []
            for match in search_response.matches:
                # Only include results with similarity score above threshold
                if match.score > 0.4:  # Same threshold as working implementation
                    documents.append({
                        "content": match.metadata.get("content", ""),
                        "metadata": match.metadata,
                        "score": match.score,
                        "source": "menu"
                    })
            
            return {
                "documents": documents,
                "metadata": {
                    "search_type": "menu",
                    "language": language,
                    "total_results": len(documents)
                }
            }
            
        except Exception as e:
            logger.error("menu_search_failed", error=str(e))
            return {"documents": [], "metadata": {"error": str(e)}}
    
    async def _search_faq_namespace(self, user_message: str, language: str) -> Dict[str, Any]:
        """Search FAQ namespace"""
        try:
            # Query Pinecone FAQ namespace
            query_vector = await self.vector_search.embeddings.aembed_query(user_message)
            
            # Search in FAQ namespace
            search_response = self.vector_search.pinecone_index.query(
                vector=query_vector,
                namespace="faq",
                top_k=5,
                include_metadata=True
            )
            
            documents = []
            for match in search_response.matches:
                # Only include results with similarity score above threshold
                if match.score > 0.4:  # Same threshold as working implementation
                    documents.append({
                        "content": match.metadata.get("content", ""),
                        "metadata": match.metadata,
                        "score": match.score,
                        "source": "faq"
                    })
            
            return {
                "documents": documents,
                "metadata": {
                    "search_type": "faq",
                    "language": language,
                    "total_results": len(documents)
                }
            }
            
        except Exception as e:
            logger.error("faq_search_failed", error=str(e))
            return {"documents": [], "metadata": {"error": str(e)}}
    
    async def _search_job_namespace(self, user_message: str, language: str) -> Dict[str, Any]:
        """Search job application namespace"""
        try:
            # Query Pinecone job namespace
            query_vector = await self.vector_search.embeddings.aembed_query(user_message)
            
            # Search in jobs namespace
            search_response = self.vector_search.pinecone_index.query(
                vector=query_vector,
                namespace="jobs",
                top_k=5,
                include_metadata=True
            )
            
            documents = []
            for match in search_response.matches:
                # Only include results with similarity score above threshold
                if match.score > 0.4:  # Same threshold as working implementation
                    documents.append({
                        "content": match.metadata.get("content", ""),
                        "metadata": match.metadata,
                        "score": match.score,
                        "source": "jobs"
                    })
            
            return {
                "documents": documents,
                "metadata": {
                    "search_type": "jobs",
                    "language": language,
                    "total_results": len(documents)
                }
            }
            
        except Exception as e:
            logger.error("job_search_failed", error=str(e))
            return {"documents": [], "metadata": {"error": str(e)}}
    
    def _set_empty_results(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Set empty results when retrieval is skipped or fails"""
        updated_state = state.copy()
        updated_state.update({
            "rag_results": [],
            "relevance_score": 0.0,
            "search_metadata": {
                "search_type": "empty",
                "language": state.get("detected_language", "en"),
                "total_results": 0,
                "target_namespace": state.get("target_namespace", "")
            },
            "retrieved_count": 0,
            "search_query": "",
            "search_namespace": ""
        })
        
        return updated_state 