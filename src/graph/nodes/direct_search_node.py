"""
Direct Search Node for LangGraph
Simple vector search with English terms, returns bilingual results
No complex routing - just direct search with fallback
"""

import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from langchain_openai import OpenAIEmbeddings
from src.utils.logger import get_logger
from src.config.settings import get_settings
from src.config.constants import PINECONE_NAMESPACES

logger = get_logger("direct_search_node")


@dataclass
class SearchResult:
    """Simple search result with bilingual content"""
    content: str
    metadata: Dict[str, Any]
    namespace: str
    relevance_score: float
    language: str  # "en" or "my"


class DirectSearchNode:
    """
    Direct search node that performs simple vector search
    Uses English search terms, returns bilingual results
    """
    
    def __init__(self):
        """Initialize direct search node"""
        self.settings = get_settings()
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            model=self.settings.openai_embedding_model,
            api_key=self.settings.openai_api_key
        )
        
        # Initialize Pinecone
        from pinecone import Pinecone
        pc = Pinecone(api_key=self.settings.pinecone_api_key)
        self.pinecone_index = pc.Index(self.settings.pinecone_index_name)
        
        # Search configuration
        self.search_config = {
            "max_results": 5,
            # Lower threshold to improve recall for short queries and bilingual content
            "min_relevance_threshold": 0.3,
            "include_metadata": True
        }
        
        logger.info("direct_search_node_initialized")

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform direct search based on analysis results
        
        Args:
            state: Current conversation state with analysis results
            
        Returns:
            Updated state with search results
        """
        user_message = state.get("user_message", "")
        search_terms = state.get("search_terms", [])
        search_namespace = state.get("search_namespace")
        response_strategy = state.get("response_strategy", "polite_fallback")
        
        if not user_message:
            logger.warning("empty_user_message_in_direct_search")
            return self._set_default_search_results(state)
        
        # If no search required, skip search
        if response_strategy == "direct_answer":
            logger.info("skipping_search_for_direct_answer", response_strategy=response_strategy)
            return self._set_direct_answer_results(state)
        
        if not search_terms:
            logger.warning("no_search_terms_provided")
            return self._set_default_search_results(state)
        
        try:
            # Perform direct search
            search_results = await self._perform_direct_search(search_terms, search_namespace)
            
            # Update state with search results
            updated_state = state.copy()
            updated_state.update({
                "search_results": search_results,
                "data_found": len(search_results) > 0,
                "search_performed": True,
                "search_namespace_used": self._determine_search_namespace(search_namespace, search_terms),
                "search_terms_used": search_terms
            })
            
            # Log search results
            logger.info("direct_search_completed",
                       user_message=user_message[:100],
                       search_terms=search_terms,
                       search_namespace=search_namespace,
                       results_count=len(search_results),
                       data_found=len(search_results) > 0)
            
            return updated_state
            
        except Exception as e:
            logger.error("direct_search_failed",
                        error=str(e),
                        user_message=user_message[:100],
                        search_terms=search_terms)
            
            # Fallback to default search results
            return self._set_default_search_results(state)

    async def _perform_direct_search(self, search_terms: List[str], namespace: Optional[str]) -> List[SearchResult]:
        """
        Perform direct vector search with English terms
        
        Args:
            search_terms: English search terms
            namespace: Target namespace (menu, faq, events, jobs)
            
        Returns:
            List of search results with bilingual content
        """
        try:
            # Create search query from terms
            search_query = " ".join(search_terms)
            
            # Generate embedding for search query
            query_embedding = await self.embeddings.aembed_query(search_query)
            
            # Determine search namespace
            target_namespace = self._determine_search_namespace(namespace, search_terms)
            
            # Perform search
            search_response = self.pinecone_index.query(
                vector=query_embedding,
                namespace=target_namespace,
                top_k=self.search_config["max_results"],
                include_metadata=self.search_config["include_metadata"]
            )
            
            # Process search results
            search_results = []
            for match in search_response.matches:
                if match.score >= self.search_config["min_relevance_threshold"]:
                    result = self._create_search_result(match, target_namespace)
                    if result:
                        search_results.append(result)
            
            # If no results in primary namespace, try fallback search in FAQ
            if not search_results and target_namespace != "faq":
                logger.info("no_results_in_primary_namespace_trying_fallback", 
                           primary_namespace=target_namespace)
                fallback_results = await self._perform_fallback_search(search_terms)
                search_results.extend(fallback_results)

            # If still no results, try cross-namespace search to maximize recall
            if not search_results:
                cross_ns_results = await self._perform_cross_namespace_search(search_terms, exclude_namespace=target_namespace)
                if cross_ns_results:
                    logger.info("cross_namespace_search_found_results", count=len(cross_ns_results))
                    search_results.extend(cross_ns_results)
            
            return search_results
            
        except Exception as e:
            logger.error("vector_search_failed", error=str(e), search_terms=search_terms)
            return []

    def _determine_search_namespace(self, namespace: Optional[str], search_terms: List[str]) -> str:
        """
        Determine which namespace to search based on terms and namespace
        
        Args:
            namespace: Suggested namespace from analysis
            search_terms: Search terms
            
        Returns:
            Target namespace for search
        """
        # Accept either key (e.g., "faq") or mapped value (also "faq")
        if namespace and (namespace in PINECONE_NAMESPACES or namespace in PINECONE_NAMESPACES.values()):
            # Normalize to key string if a mapped value was supplied
            for key, value in PINECONE_NAMESPACES.items():
                if namespace == key or namespace == value:
                    return key
        
        # Fallback namespace determination based on search terms
        terms_lower = [term.lower() for term in search_terms]
        
        # Menu-related terms
        menu_terms = ["menu", "food", "dish", "meal", "breakfast", "lunch", "dinner", "drink", "coffee", "tea"]
        if any(term in terms_lower for term in menu_terms):
            return "menu"
        
        # Events-related terms
        events_terms = ["event", "promotion", "special", "offer", "entertainment", "party"]
        if any(term in terms_lower for term in events_terms):
            return "events"
        
        # Jobs-related terms
        jobs_terms = ["job", "employment", "career", "hire", "work", "position"]
        if any(term in terms_lower for term in jobs_terms):
            return "jobs"
        
        # Default to FAQ
        return "faq"

    async def _perform_fallback_search(self, search_terms: List[str]) -> List[SearchResult]:
        """
        Perform fallback search in FAQ namespace
        
        Args:
            search_terms: Search terms
            
        Returns:
            Fallback search results
        """
        try:
            search_query = " ".join(search_terms)
            query_embedding = await self.embeddings.aembed_query(search_query)
            
            search_response = self.pinecone_index.query(
                vector=query_embedding,
                namespace="faq",
                top_k=3,  # Fewer results for fallback
                include_metadata=self.search_config["include_metadata"]
            )
            
            fallback_results = []
            for match in search_response.matches:
                if match.score >= 0.3:  # Lower threshold for fallback
                    result = self._create_search_result(match, "faq")
                    if result:
                        fallback_results.append(result)
            
            return fallback_results
            
        except Exception as e:
            logger.error("fallback_search_failed", error=str(e))
            return []

    def _create_search_result(self, match: Any, namespace: str) -> Optional[SearchResult]:
        """
        Create search result from Pinecone match
        
        Args:
            match: Pinecone match object
            namespace: Source namespace
            
        Returns:
            SearchResult object or None if invalid
        """
        try:
            metadata = match.metadata or {}
            
            # Extract content based on namespace
            content = self._extract_content_from_metadata(metadata, namespace)
            if not content:
                return None
            
            # Determine language from content
            language = self._detect_content_language(content)
            
            return SearchResult(
                content=content,
                metadata=metadata,
                namespace=namespace,
                relevance_score=float(match.score),
                language=language
            )
            
        except Exception as e:
            logger.error("failed_to_create_search_result", error=str(e))
            return None

    def _extract_content_from_metadata(self, metadata: Dict[str, Any], namespace: str) -> str:
        """
        Extract relevant content from metadata based on namespace
        
        Args:
            metadata: Pinecone metadata
            namespace: Source namespace
            
        Returns:
            Extracted content string
        """
        try:
            if namespace == "menu":
                # Extract menu item information (support legacy and new keys)
                english_name = metadata.get("english_name") or metadata.get("name", "")
                myanmar_name = metadata.get("myanmar_name", "")
                description_en = metadata.get("description_en") or metadata.get("description", "")
                description_mm = metadata.get("description_mm", "")
                price = metadata.get("price", "")
                currency = metadata.get("currency", "")
                
                content_parts = []
                if english_name:
                    content_parts.append(f"English: {english_name}")
                if myanmar_name:
                    content_parts.append(f"Myanmar: {myanmar_name}")
                if description_en:
                    content_parts.append(f"Description: {description_en}")
                if description_mm:
                    content_parts.append(f"ဖော်ပြချက်: {description_mm}")
                if price:
                    content_parts.append(f"Price: {price} {currency}")
                
                return " | ".join(content_parts)
                
            elif namespace == "faq":
                # Extract FAQ information (support legacy and new keys)
                question_en = metadata.get("question_en") or metadata.get("question", "")
                answer_en = metadata.get("answer_en") or metadata.get("answer", "")
                question_mm = metadata.get("question_mm", "")
                answer_mm = metadata.get("answer_mm", "")
                
                content_parts = []
                if question_en:
                    content_parts.append(f"Q: {question_en}")
                if answer_en:
                    content_parts.append(f"A: {answer_en}")
                if question_mm:
                    content_parts.append(f"မေး: {question_mm}")
                if answer_mm:
                    content_parts.append(f"ဖြေ: {answer_mm}")
                
                return " | ".join(content_parts)
                
            elif namespace == "events":
                # Extract events information
                title_en = metadata.get("title_en", "")
                description_en = metadata.get("description_en", "")
                title_mm = metadata.get("title_mm", "")
                description_mm = metadata.get("description_mm", "")
                
                content_parts = []
                if title_en:
                    content_parts.append(f"Event: {title_en}")
                if description_en:
                    content_parts.append(f"Details: {description_en}")
                if title_mm:
                    content_parts.append(f"အစီအစဉ်: {title_mm}")
                if description_mm:
                    content_parts.append(f"အသေးစိတ်: {description_mm}")
                
                return " | ".join(content_parts)
                
            elif namespace == "jobs":
                # Extract jobs information (support legacy and new keys)
                position_en = metadata.get("position_en") or metadata.get("title_en", "")
                position_mm = metadata.get("position_mm") or metadata.get("title_mm", "")
                # Prefer explicit description_en; fallback to content or responsibilities
                description_en = metadata.get("description_en") or metadata.get("content", "")
                description_mm = metadata.get("description_mm", "")
                
                content_parts = []
                if position_en:
                    content_parts.append(f"Position: {position_en}")
                if description_en:
                    content_parts.append(f"Description: {description_en}")
                if position_mm:
                    content_parts.append(f"ရာထူး: {position_mm}")
                if description_mm:
                    content_parts.append(f"ဖော်ပြချက်: {description_mm}")
                
                return " | ".join(content_parts)
            
            # Fallback to text/content field if available
            return metadata.get("text", metadata.get("content", ""))
            
        except Exception as e:
            logger.error("failed_to_extract_content", error=str(e), namespace=namespace)
            return ""

    def _detect_content_language(self, content: str) -> str:
        """
        Detect language of content
        
        Args:
            content: Content string
            
        Returns:
            Language code ("en", "my", or "mixed")
        """
        # Check for Burmese characters
        burmese_chars = set("ကခဂဃငစဆဇဈဉညဋဌဍဎဏတထဒဓနပဖဗဘမယရလဝသဟဠအဣဤဥဦဧဨဩဪါာိီုူေဲဳဴဵံ့း္်ျြွှဿ၀၁၂၃၄၅၆၇၈၉၏ၐၑၒၓၔၕၖၗၘၙၚၛၜၝၞၟၠၡၢၣၤၥၦၧၨၩၪၫၬၭၮၯၰၱၲၳၴၵၶၷၸၹၺၻၼၽၾၿႀႁႂႃႄႅႆႇႈႉႊႋႌႍႎႏ႐႑႒႓႔႕႖႗႘႙ႚႛႜႝ႞႟ႠႡႢႣႤႥႦႧႨႩႪႫႬႭႮႯႰႱႲႳႴႵႶႷႸႹႺႻႼႽႾႿ")
        
        has_burmese = any(char in burmese_chars for char in content)
        has_english = any(char.isascii() and char.isalpha() for char in content)
        
        if has_burmese and has_english:
            return "mixed"
        elif has_burmese:
            return "my"
        else:
            return "en"

    async def _perform_cross_namespace_search(self, search_terms: List[str], exclude_namespace: Optional[str] = None) -> List[SearchResult]:
        """
        Search across all namespaces if primary search yields no results.

        Args:
            search_terms: English search terms
            exclude_namespace: Namespace to skip (already searched)

        Returns:
            Aggregated results across namespaces
        """
        try:
            namespaces_order = ["faq", "menu", "events", "jobs"]
            results: List[SearchResult] = []
            search_query = " ".join(search_terms)
            query_embedding = await self.embeddings.aembed_query(search_query)

            for ns in namespaces_order:
                if exclude_namespace and ns == exclude_namespace:
                    continue
                try:
                    response = self.pinecone_index.query(
                        vector=query_embedding,
                        namespace=ns,
                        top_k=3,
                        include_metadata=self.search_config["include_metadata"]
                    )
                    for match in response.matches:
                        if match.score >= self.search_config["min_relevance_threshold"]:
                            sr = self._create_search_result(match, ns)
                            if sr:
                                results.append(sr)
                except Exception as inner_e:
                    logger.warning("cross_namespace_query_failed", namespace=ns, error=str(inner_e))
                    continue

            return results
        except Exception as e:
            logger.error("cross_namespace_search_failed", error=str(e))
            return []

    def _set_direct_answer_results(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set results for direct answer strategy (no search needed)
        
        Args:
            state: Current state
            
        Returns:
            Updated state
        """
        updated_state = state.copy()
        updated_state.update({
            "search_results": [],
            "data_found": False,
            "search_performed": False,
            "search_namespace_used": None,
            "search_terms_used": []
        })
        
        return updated_state

    def _set_default_search_results(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set default search results when search fails
        
        Args:
            state: Current state
            
        Returns:
            Updated state with default results
        """
        updated_state = state.copy()
        updated_state.update({
            "search_results": [],
            "data_found": False,
            "search_performed": True,
            "search_namespace_used": "faq",
            "search_terms_used": ["general", "information"]
        })
        
        return updated_state
