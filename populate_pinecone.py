"""
Populate Pinecone with all data from JSON files
This script will clear existing data and populate all namespaces with fresh data
"""

import asyncio
import sys
import os
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.embedding_service import get_embedding_service
from src.utils.logger import get_logger

logger = get_logger("populate_pinecone")


async def populate_pinecone_data():
    """Populate all Pinecone namespaces with current data"""
    print("🚀 Starting Pinecone Data Population...")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Get embedding service
        embedding_service = get_embedding_service()
        
        # Check if Pinecone is available
        if not embedding_service.pinecone_index:
            print("❌ ERROR: Pinecone is not available. Please check your configuration.")
            return False
        
        print("✅ Pinecone connection established")
        
        # Get current embedding status
        print("\n📊 Current Embedding Status:")
        current_status = embedding_service.get_embedding_status()
        for data_type, status in current_status.items():
            print(f"  {data_type}: {status['status']} ({status['count']} items)")
        
        # Clear all namespaces first
        print("\n🧹 Clearing all namespaces...")
        clear_results = await embedding_service.clear_all_namespaces()
        
        print("📋 Clear Results:")
        for data_type, success in clear_results.items():
            status = "✅ SUCCESS" if success else "❌ FAILED"
            print(f"  {data_type}: {status}")
        
        # Check if any clear operations failed
        if not all(clear_results.values()):
            print("⚠️  Some clear operations failed. Continuing anyway...")
        
        # Embed all data
        print("\n📤 Embedding all data...")
        embed_results = await embedding_service.embed_all_data()
        
        print("📋 Embed Results:")
        for data_type, success in embed_results.items():
            status = "✅ SUCCESS" if success else "❌ FAILED"
            print(f"  {data_type}: {status}")
        
        # Get final embedding status
        print("\n📊 Final Embedding Status:")
        final_status = embedding_service.get_embedding_status()
        for data_type, status in final_status.items():
            print(f"  {data_type}: {status['status']} ({status['count']} items)")
        
        # Summary
        success_count = sum(embed_results.values())
        total_count = len(embed_results)
        
        print(f"\n{'='*60}")
        print("📋 POPULATION SUMMARY")
        print(f"{'='*60}")
        print(f"Total Data Types: {total_count}")
        print(f"Successfully Embedded: {success_count}")
        print(f"Failed: {total_count - success_count}")
        print(f"Success Rate: {(success_count/total_count)*100:.1f}%")
        
        if success_count == total_count:
            print("\n🎉 ALL DATA SUCCESSFULLY EMBEDDED!")
            print("✅ Pinecone is now ready for RAG operations")
            return True
        else:
            print("\n⚠️  SOME DATA TYPES FAILED TO EMBED")
            print("Please check the logs for details")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        logger.error("pinecone_population_failed", error=str(e))
        return False


async def verify_pinecone_data():
    """Verify that data was properly embedded"""
    print("\n🔍 Verifying Pinecone Data...")
    
    try:
        embedding_service = get_embedding_service()
        
        if not embedding_service.pinecone_index:
            print("❌ ERROR: Pinecone is not available")
            return False
        
        # Get embedding status
        status = embedding_service.get_embedding_status()
        
        print("📊 Verification Results:")
        all_good = True
        
        for data_type, data_status in status.items():
            if data_status['status'] == 'embedded' and data_status['count'] > 0:
                print(f"  ✅ {data_type}: {data_status['count']} items embedded")
            else:
                print(f"  ❌ {data_type}: {data_status['status']} ({data_status['count']} items)")
                all_good = False
        
        if all_good:
            print("\n🎉 VERIFICATION PASSED!")
            print("All namespaces have data and are ready for use")
            return True
        else:
            print("\n⚠️  VERIFICATION FAILED!")
            print("Some namespaces are missing data")
            return False
            
    except Exception as e:
        print(f"❌ ERROR during verification: {str(e)}")
        return False


async def main():
    """Main function"""
    print("="*60)
    print("🏪 CAFE PENTAGON - PINECONE DATA POPULATION")
    print("="*60)
    
    # Populate data
    success = await populate_pinecone_data()
    
    if success:
        # Verify data
        await verify_pinecone_data()
        
        print("\n" + "="*60)
        print("🎯 NEXT STEPS:")
        print("="*60)
        print("1. Run Phase 3 tests to verify RAG functionality")
        print("2. Test with Streamlit interface")
        print("3. Proceed to Phase 4: Human Escalation System")
        print("="*60)
    else:
        print("\n❌ Data population failed. Please check the logs and try again.")


if __name__ == "__main__":
    asyncio.run(main()) 