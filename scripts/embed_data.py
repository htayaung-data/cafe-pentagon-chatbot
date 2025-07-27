"""
Script to embed data into Pinecone for semantic search
"""

import asyncio
import json
from typing import List, Dict, Any
from langchain_openai import OpenAIEmbeddings
import pinecone
from src.config.settings import get_settings
from src.config.constants import PINECONE_NAMESPACES
from src.data.loader import get_data_loader
from src.utils.logger import setup_logger, get_logger

# Setup logging
setup_logger()
logger = get_logger("embed_data")


class DataEmbedder:
    """Class to handle data embedding into Pinecone"""
    
    def __init__(self):
        """Initialize data embedder"""
        self.settings = get_settings()
        self.data_loader = get_data_loader()
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-ada-002",
            api_key=self.settings.openai_api_key
        )
        
        # Initialize Pinecone
        self.pinecone_index = self._initialize_pinecone()
        
        logger.info("data_embedder_initialized")
    
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
    
    async def embed_menu_data(self):
        """Embed menu data into Pinecone"""
        if not self.pinecone_index:
            logger.error("pinecone_not_available")
            return False
        
        try:
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
            
            # Upsert to Pinecone
            self.pinecone_index.upsert(
                vectors=vectors,
                namespace=PINECONE_NAMESPACES["menu"]
            )
            
            logger.info("menu_data_embedded", vectors_count=len(vectors))
            return True
            
        except Exception as e:
            logger.error("menu_embedding_failed", error=str(e))
            return False
    
    async def embed_faq_data(self):
        """Embed FAQ data into Pinecone"""
        if not self.pinecone_index:
            logger.error("pinecone_not_available")
            return False
        
        try:
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
            
            # Upsert to Pinecone
            self.pinecone_index.upsert(
                vectors=vectors,
                namespace=PINECONE_NAMESPACES["faq"]
            )
            
            logger.info("faq_data_embedded", vectors_count=len(vectors))
            return True
            
        except Exception as e:
            logger.error("faq_embedding_failed", error=str(e))
            return False
    
    async def embed_events_data(self):
        """Embed events data into Pinecone"""
        if not self.pinecone_index:
            logger.error("pinecone_not_available")
            return False
        
        try:
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
            
            # Upsert to Pinecone
            self.pinecone_index.upsert(
                vectors=vectors,
                namespace=PINECONE_NAMESPACES["events"]
            )
            
            logger.info("events_data_embedded", vectors_count=len(vectors))
            return True
            
        except Exception as e:
            logger.error("events_embedding_failed", error=str(e))
            return False
    
    async def embed_all_data(self):
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


async def main():
    """Main function to run data embedding"""
    logger.info("starting_data_embedding_script")
    
    embedder = DataEmbedder()
    results = await embedder.embed_all_data()
    
    # Print results
    print("\n" + "="*50)
    print("DATA EMBEDDING RESULTS")
    print("="*50)
    
    for data_type, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{data_type.upper()}: {status}")
    
    print("="*50)
    
    success_count = sum(results.values())
    total_count = len(results)
    
    if success_count == total_count:
        print("🎉 All data embedded successfully!")
    else:
        print(f"⚠️  {success_count}/{total_count} data types embedded successfully")
    
    logger.info("data_embedding_script_completed")


if __name__ == "__main__":
    asyncio.run(main()) 