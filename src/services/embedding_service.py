"""
Independent Embedding Service for Cafe Pentagon Chatbot
Handles Pinecone data embedding as a separate service
"""

import asyncio
import json
import os
import time
from typing import Dict, List, Any, Optional
from pathlib import Path
from langchain_openai import OpenAIEmbeddings
import pinecone
from src.config.settings import get_settings
from src.config.constants import PINECONE_NAMESPACES, DATA_FILES
from src.data.loader import get_data_loader
from src.utils.logger import setup_logger, get_logger

# Setup logging
setup_logger()
logger = get_logger("embedding_service")


class EmbeddingService:
    """Independent service for managing Pinecone embeddings"""
    
    def __init__(self):
        """Initialize embedding service"""
        self.settings = get_settings()
        self.data_loader = get_data_loader()
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-ada-002",
            api_key=self.settings.openai_api_key
        )
        
        # Initialize Pinecone
        self.pinecone_index = self._initialize_pinecone()
        
        # Embedding status tracking
        self.embedding_status = {
            "menu": {"last_updated": None, "count": 0, "status": "not_embedded"},
            "faq": {"last_updated": None, "count": 0, "status": "not_embedded"},
            "events": {"last_updated": None, "count": 0, "status": "not_embedded"}
        }
        
        logger.info("embedding_service_initialized")
    
    def _initialize_pinecone(self):
        """Initialize Pinecone index"""
        try:
            from pinecone import Pinecone, ServerlessSpec
            
            pc = Pinecone(api_key=self.settings.pinecone_api_key)
            
            # Check if index exists
            if self.settings.pinecone_index_name not in pc.list_indexes().names():
                logger.warning("pinecone_index_not_found", index_name=self.settings.pinecone_index_name)
                logger.info("creating_pinecone_index", index_name=self.settings.pinecone_index_name)
                
                # Create index
                pc.create_index(
                    name=self.settings.pinecone_index_name,
                    dimension=1536,  # OpenAI ada-002 embedding dimension
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
                
                logger.info("pinecone_index_created", index_name=self.settings.pinecone_index_name)
            
            index = pc.Index(self.settings.pinecone_index_name)
            logger.info("pinecone_initialized", index_name=self.settings.pinecone_index_name)
            return index
            
        except Exception as e:
            logger.error("pinecone_initialization_failed", error=str(e))
            return None
    
    async def embed_menu_data(self) -> bool:
        """Embed menu data into Pinecone"""
        if not self.pinecone_index:
            logger.error("pinecone_not_available")
            return False
        
        try:
            # Clear existing menu namespace first to avoid duplicates
            logger.info("clearing_menu_namespace")
            await self.clear_namespace(PINECONE_NAMESPACES["menu"])
            
            # Load menu data
            menu_data = self.data_loader.load_menu_data()
            if not menu_data:
                logger.error("no_menu_data_found")
                return False
            
            logger.info("embedding_menu_data", item_count=len(menu_data))
            
            # Prepare vectors for embedding
            vectors = []
            for item in menu_data:
                # Handle Pydantic model
                if hasattr(item, 'model_dump'):
                    item_dict = item.model_dump()
                elif hasattr(item, 'dict'):
                    item_dict = item.dict()
                else:
                    item_dict = item
                
                # Create text for embedding
                text = f"{item_dict.get('english_name', '')} {item_dict.get('myanmar_name', '')} {item_dict.get('description_en', '')} {item_dict.get('description_mm', '')} {item_dict.get('category', '')}"
                
                # Generate embedding
                embedding = self.embeddings.embed_query(text)
                
                # Prepare metadata
                metadata = {
                    "id": str(item_dict.get("id")),
                    "name": item_dict.get("english_name", ""),
                    "myanmar_name": item_dict.get("myanmar_name", ""),
                    "description": item_dict.get("description_en", ""),
                    "description_mm": item_dict.get("description_mm", ""),
                    "price": item_dict.get("price", 0),
                    "currency": item_dict.get("currency", "MMK"),
                    "category": str(item_dict.get("category", "")),
                    "image_url": item_dict.get("image_url", ""),
                    "dietary_info": json.dumps(item_dict.get("dietary_info", {})),
                    "allergens": json.dumps(item_dict.get("allergens", [])),
                    "spice_level": item_dict.get("spice_level", ""),
                    "preparation_time": item_dict.get("preparation_time", ""),
                    "type": "menu_item"
                }
                
                vectors.append({
                    "id": f"menu_{item_dict.get('id')}",
                    "values": embedding,
                    "metadata": metadata
                })
            
            # Insert to Pinecone (not upsert since we cleared the namespace)
            self.pinecone_index.upsert(
                vectors=vectors,
                namespace=PINECONE_NAMESPACES["menu"]
            )
            
            # Update status
            self.embedding_status["menu"] = {
                "last_updated": time.time(),
                "count": len(vectors),
                "status": "embedded"
            }
            
            logger.info("menu_data_embedded", vectors_count=len(vectors))
            return True
            
        except Exception as e:
            logger.error("menu_embedding_failed", error=str(e))
            self.embedding_status["menu"]["status"] = "failed"
            return False
    
    async def embed_faq_data(self) -> bool:
        """Embed FAQ data into Pinecone"""
        if not self.pinecone_index:
            logger.error("pinecone_not_available")
            return False
        
        try:
            # Clear existing FAQ namespace first to avoid duplicates
            logger.info("clearing_faq_namespace")
            await self.clear_namespace(PINECONE_NAMESPACES["faq"])
            
            # Load FAQ data
            faq_data = self.data_loader.load_faq_data()
            if not faq_data:
                logger.error("no_faq_data_found")
                return False
            
            logger.info("embedding_faq_data", item_count=len(faq_data))
            
            # Prepare vectors for embedding
            vectors = []
            for item in faq_data:
                # Handle Pydantic model
                if hasattr(item, 'model_dump'):
                    item_dict = item.model_dump()
                elif hasattr(item, 'dict'):
                    item_dict = item.dict()
                else:
                    item_dict = item
                
                # Create text for embedding
                text = f"{item_dict.get('question_en', '')} {item_dict.get('question_mm', '')} {item_dict.get('answer_en', '')} {item_dict.get('answer_mm', '')}"
                
                # Generate embedding
                embedding = self.embeddings.embed_query(text)
                
                # Prepare metadata
                metadata = {
                    "id": str(item_dict.get("id")),
                    "question": item_dict.get("question_en", ""),
                    "question_mm": item_dict.get("question_mm", ""),
                    "answer": item_dict.get("answer_en", ""),
                    "answer_mm": item_dict.get("answer_mm", ""),
                    "category": item_dict.get("category", ""),
                    "tags": json.dumps(item_dict.get("tags", [])),
                    "priority": item_dict.get("priority", 1),
                    "content": f"Q: {item_dict.get('question_en', '')}\nA: {item_dict.get('answer_en', '')}",
                    "type": "faq_item"
                }
                
                vectors.append({
                    "id": f"faq_{item_dict.get('id')}",
                    "values": embedding,
                    "metadata": metadata
                })
            
            # Insert to Pinecone (not upsert since we cleared the namespace)
            self.pinecone_index.upsert(
                vectors=vectors,
                namespace=PINECONE_NAMESPACES["faq"]
            )
            
            # Update status
            self.embedding_status["faq"] = {
                "last_updated": time.time(),
                "count": len(vectors),
                "status": "embedded"
            }
            
            logger.info("faq_data_embedded", vectors_count=len(vectors))
            return True
            
        except Exception as e:
            logger.error("faq_embedding_failed", error=str(e))
            self.embedding_status["faq"]["status"] = "failed"
            return False
    
    async def embed_events_data(self) -> bool:
        """Embed events data into Pinecone"""
        if not self.pinecone_index:
            logger.error("pinecone_not_available")
            return False
        
        try:
            # Clear existing events namespace first to avoid duplicates
            logger.info("clearing_events_namespace")
            await self.clear_namespace(PINECONE_NAMESPACES["events"])
            
            # Load events data
            events_data = self.data_loader.load_events_data()
            if not events_data:
                logger.error("no_events_data_found")
                return False
            
            logger.info("embedding_events_data", item_count=len(events_data))
            
            # Prepare vectors for embedding
            vectors = []
            for item in events_data:
                # Handle Pydantic model
                if hasattr(item, 'model_dump'):
                    item_dict = item.model_dump()
                elif hasattr(item, 'dict'):
                    item_dict = item.dict()
                else:
                    item_dict = item
                
                # Create text for embedding
                text = f"{item_dict.get('title_en', '')} {item_dict.get('title_mm', '')} {item_dict.get('description_en', '')} {item_dict.get('description_mm', '')} {item_dict.get('type', '')} {item_dict.get('artist_en', '')}"
                
                # Generate embedding
                embedding = self.embeddings.embed_query(text)
                
                # Prepare metadata
                metadata = {
                    "id": str(item_dict.get("event_id")),
                    "title": item_dict.get("title_en", ""),
                    "title_mm": item_dict.get("title_mm", ""),
                    "description": item_dict.get("description_en", ""),
                    "description_mm": item_dict.get("description_mm", ""),
                    "event_type": str(item_dict.get("type", "")),
                    "date": item_dict.get("date", ""),
                    "time": item_dict.get("time", ""),
                    "artist": item_dict.get("artist_en", ""),
                    "artist_mm": item_dict.get("artist_mm", ""),
                    "special_menu": json.dumps(item_dict.get("special_menu", [])),
                    "promotion_code": item_dict.get("promotion_code", ""),
                    "price": json.dumps(item_dict.get("price", {})),
                    "max_capacity": item_dict.get("max_capacity", 0),
                    "current_bookings": item_dict.get("current_bookings", 0),
                    "features": json.dumps(item_dict.get("features", [])),
                    "status": item_dict.get("status", ""),
                    "type": "event_item"
                }
                
                vectors.append({
                    "id": f"event_{item_dict.get('event_id')}",
                    "values": embedding,
                    "metadata": metadata
                })
            
            # Insert to Pinecone (not upsert since we cleared the namespace)
            self.pinecone_index.upsert(
                vectors=vectors,
                namespace=PINECONE_NAMESPACES["events"]
            )
            
            # Update status
            self.embedding_status["events"] = {
                "last_updated": time.time(),
                "count": len(vectors),
                "status": "embedded"
            }
            
            logger.info("events_data_embedded", vectors_count=len(vectors))
            return True
            
        except Exception as e:
            logger.error("events_embedding_failed", error=str(e))
            self.embedding_status["events"]["status"] = "failed"
            return False
    
    async def embed_all_data(self) -> Dict[str, bool]:
        """Embed all data into Pinecone"""
        logger.info("starting_data_embedding")
        
        results = {
            "menu": await self.embed_menu_data(),
            "faq": await self.embed_faq_data(),
            "events": await self.embed_events_data()
        }
        
        success_count = sum(results.values())
        total_count = len(results)
        
        logger.info("data_embedding_completed", 
                   success_count=success_count, 
                   total_count=total_count,
                   results=results)
        
        return results
    
    def get_embedding_status(self) -> Dict[str, Any]:
        """Get current embedding status"""
        # Sync with actual Pinecone data first
        self._sync_embedding_status_with_pinecone()
        return self.embedding_status
    
    def _sync_embedding_status_with_pinecone(self):
        """Sync embedding status with actual data in Pinecone"""
        if not self.pinecone_index:
            return
        
        try:
            from src.config.constants import PINECONE_NAMESPACES
            
            for data_type, namespace in PINECONE_NAMESPACES.items():
                if data_type in ["menu", "faq", "events"]:
                    try:
                        # Query Pinecone to get actual count
                        results = self.pinecone_index.query(
                            vector=[0.0] * 1536,  # Dummy vector
                            namespace=namespace,
                            top_k=1000,  # Get all items to count properly
                            include_metadata=False
                        )
                        
                        # Update status based on actual data
                        if results.matches:
                            self.embedding_status[data_type]["count"] = len(results.matches)
                            self.embedding_status[data_type]["status"] = "embedded"
                            # Set a recent timestamp if not already set
                            if not self.embedding_status[data_type].get("last_updated"):
                                import time
                                self.embedding_status[data_type]["last_updated"] = time.time()
                        else:
                            self.embedding_status[data_type]["count"] = 0
                            self.embedding_status[data_type]["status"] = "not_embedded"
                            
                    except Exception as e:
                        logger.error(f"error_syncing_{data_type}_status", error=str(e))
                        
        except Exception as e:
            logger.error("error_syncing_embedding_status", error=str(e))
    
    def is_data_embedded(self, data_type: str) -> bool:
        """Check if specific data type is embedded"""
        status = self.embedding_status.get(data_type, {})
        return status.get("status") == "embedded"
    
    def get_last_updated(self, data_type: str) -> Optional[float]:
        """Get last updated timestamp for data type"""
        status = self.embedding_status.get(data_type, {})
        return status.get("last_updated")
    
    async def clear_namespace(self, namespace: str) -> bool:
        """Clear all vectors from a namespace"""
        if not self.pinecone_index:
            logger.error("pinecone_not_available")
            return False
        
        try:
            self.pinecone_index.delete(namespace=namespace, delete_all=True)
            logger.info("namespace_cleared", namespace=namespace)
            return True
        except Exception as e:
            logger.error("namespace_clear_failed", namespace=namespace, error=str(e))
            return False
    
    async def clear_all_namespaces(self) -> Dict[str, bool]:
        """Clear all namespaces to avoid duplicates"""
        logger.info("clearing_all_namespaces")
        results = {}
        
        for data_type, namespace in PINECONE_NAMESPACES.items():
            if data_type in ["menu", "faq", "events"]:  # Only clear data namespaces
                results[data_type] = await self.clear_namespace(namespace)
        
        return results
    
    async def update_embeddings_if_needed(self, force_update: bool = False) -> Dict[str, bool]:
        """Update embeddings only if needed or forced"""
        if force_update:
            logger.info("force_updating_embeddings")
            return await self.embed_all_data()
        
        # Check if data files have been modified since last embedding
        results = {}
        for data_type in ["menu", "faq", "events"]:
            if self._should_update_embeddings(data_type):
                logger.info(f"updating_{data_type}_embeddings")
                if data_type == "menu":
                    results[data_type] = await self.embed_menu_data()
                elif data_type == "faq":
                    results[data_type] = await self.embed_faq_data()
                elif data_type == "events":
                    results[data_type] = await self.embed_events_data()
            else:
                logger.info(f"{data_type}_embeddings_up_to_date")
                results[data_type] = self.is_data_embedded(data_type)
        
        return results
    
    def _should_update_embeddings(self, data_type: str) -> bool:
        """Check if embeddings should be updated based on file modification time"""
        # Get file path
        file_path = DATA_FILES.get(data_type)
        if not file_path:
            return True
        
        # Check if file exists
        if not os.path.exists(file_path):
            return True
        
        # Get file modification time
        file_mtime = os.path.getmtime(file_path)
        
        # Get last embedding time
        last_updated = self.get_last_updated(data_type)
        
        # Update if file is newer than last embedding
        if last_updated is None or file_mtime > last_updated:
            return True
        
        return False


# Global embedding service instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create embedding service instance"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service 