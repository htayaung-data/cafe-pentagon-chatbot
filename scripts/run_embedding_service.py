#!/usr/bin/env python3
"""
Standalone Embedding Service Runner
Run this script independently to embed data into Pinecone
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.embedding_service import get_embedding_service
from src.utils.logger import setup_logger, get_logger

# Setup logging
setup_logger()
logger = get_logger("embedding_runner")


async def main():
    """Main function to run embedding service"""
    parser = argparse.ArgumentParser(description="Cafe Pentagon Embedding Service")
    parser.add_argument(
        "--force", 
        action="store_true", 
        help="Force update all embeddings regardless of file modification time"
    )
    parser.add_argument(
        "--type", 
        choices=["menu", "faq", "events", "all"], 
        default="all",
        help="Type of data to embed (default: all)"
    )
    parser.add_argument(
        "--status", 
        action="store_true", 
        help="Show current embedding status"
    )
    parser.add_argument(
        "--clear", 
        choices=["menu", "faq", "events", "all"], 
        help="Clear embeddings for specific namespace or all namespaces"
    )
    
    args = parser.parse_args()
    
    logger.info("starting_embedding_service_runner")
    
    # Get embedding service
    embedding_service = get_embedding_service()
    
    try:
        if args.status:
            # Show status
            status = embedding_service.get_embedding_status()
            print("\n" + "="*60)
            print("EMBEDDING STATUS")
            print("="*60)
            
            for data_type, info in status.items():
                status_icon = "✅" if info["status"] == "embedded" else "❌"
                last_updated = info.get("last_updated")
                if last_updated:
                    from datetime import datetime
                    last_updated_str = datetime.fromtimestamp(last_updated).strftime("%Y-%m-%d %H:%M:%S")
                else:
                    last_updated_str = "Never"
                
                print(f"{status_icon} {data_type.upper()}:")
                print(f"   Status: {info['status']}")
                print(f"   Count: {info['count']}")
                print(f"   Last Updated: {last_updated_str}")
                print()
            
            return
        
        if args.clear:
            # Clear specific namespace or all namespaces
            if args.clear == "all":
                print("Clearing all embeddings...")
                results = await embedding_service.clear_all_namespaces()
                success_count = sum(results.values())
                total_count = len(results)
                
                print(f"✅ {success_count}/{total_count} namespaces cleared successfully")
                for namespace, success in results.items():
                    status = "✅" if success else "❌"
                    print(f"   {status} {namespace}")
            else:
                namespace = args.clear
                print(f"Clearing {namespace} embeddings...")
                success = await embedding_service.clear_namespace(namespace)
                if success:
                    print(f"✅ {namespace} embeddings cleared successfully")
                else:
                    print(f"❌ Failed to clear {namespace} embeddings")
            return
        
        # Perform embedding
        if args.type == "all":
            if args.force:
                print("🔄 Force updating all embeddings...")
                results = await embedding_service.embed_all_data()
            else:
                print("🔄 Updating embeddings if needed...")
                results = await embedding_service.update_embeddings_if_needed()
        else:
            # Embed specific type
            data_type = args.type
            print(f"🔄 Embedding {data_type} data...")
            
            if data_type == "menu":
                results = {"menu": await embedding_service.embed_menu_data()}
            elif data_type == "faq":
                results = {"faq": await embedding_service.embed_faq_data()}
            elif data_type == "events":
                results = {"events": await embedding_service.embed_events_data()}
        
        # Print results
        print("\n" + "="*60)
        print("EMBEDDING RESULTS")
        print("="*60)
        
        success_count = sum(results.values())
        total_count = len(results)
        
        for data_type, success in results.items():
            status = "✅ SUCCESS" if success else "❌ FAILED"
            print(f"{data_type.upper()}: {status}")
        
        print("="*60)
        
        if success_count == total_count:
            print("🎉 All embeddings completed successfully!")
        else:
            print(f"⚠️  {success_count}/{total_count} embeddings completed successfully")
        
        # Show final status
        print("\n" + "="*60)
        print("FINAL STATUS")
        print("="*60)
        
        status = embedding_service.get_embedding_status()
        for data_type, info in status.items():
            status_icon = "✅" if info["status"] == "embedded" else "❌"
            print(f"{status_icon} {data_type.upper()}: {info['status']} ({info['count']} items)")
        
        logger.info("embedding_service_runner_completed", 
                   success_count=success_count, 
                   total_count=total_count)
        
    except KeyboardInterrupt:
        print("\n⚠️  Embedding service interrupted by user")
        logger.info("embedding_service_interrupted")
    except Exception as e:
        print(f"\n❌ Error running embedding service: {str(e)}")
        logger.error("embedding_service_error", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 