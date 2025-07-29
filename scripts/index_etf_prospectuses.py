#!/usr/bin/env python3
"""Standalone script to index ETF prospectus documents into Azure AI Search.

This script processes PDF files from the res/ directory and indexes them
into the investr-etfs Azure AI Search index with semantic search capabilities.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from loguru import logger

from investr.search.azure_search_client import AzureSearchClient
from investr.search.document_processor import DocumentProcessor


async def main():
    """Index ETF prospectus documents into Azure AI Search."""
    # Load environment variables from app/.env
    env_path = project_root / "app" / ".env"
    load_dotenv(env_path)
    
    logger.info("🚀 Starting ETF Prospectus Indexing")
    logger.info(f"Environment file: {env_path}")
    
    # Verify environment variables
    required_vars = [
        "AZURE_AI_SEARCH_SERVICE_ENDPOINT",
        "AZURE_AI_SEARCH_ADMIN_KEY", 
        "AZURE_AI_SEARCH_INDEX_NAME",
        "OPENAI_API_KEY"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {missing_vars}")
        return False
    
    # Log configuration (without sensitive data)
    endpoint = os.getenv("AZURE_AI_SEARCH_SERVICE_ENDPOINT")
    index_name = os.getenv("AZURE_AI_SEARCH_INDEX_NAME")
    logger.info(f"🔍 Azure Search Endpoint: {endpoint}")
    logger.info(f"📚 Index Name: {index_name}")
    
    try:
        # Initialize Azure Search client
        logger.info("🔧 Initializing Azure AI Search client...")
        search_client = AzureSearchClient()
        
        # Create index if it doesn't exist
        logger.info("📋 Creating search index if needed...")
        index_created = await search_client.create_index_if_not_exists()
        if index_created:
            logger.success("✅ Search index ready")
        else:
            logger.error("❌ Failed to create search index")
            return False
        
        # Initialize document processor
        logger.info("📄 Initializing document processor...")
        doc_processor = DocumentProcessor(
            chunk_size=1000,  # Good size for ETF prospectus content
            chunk_overlap=200,  # Overlap to maintain context
            min_chunk_size=100  # Skip very small chunks
        )
        
        # Process documents from res/ directory
        res_directory = project_root / "res"
        logger.info(f"📁 Processing PDFs from: {res_directory}")
        
        if not res_directory.exists():
            logger.error(f"❌ Directory not found: {res_directory}")
            return False
        
        # Get the smallest PDF file for testing
        smallest_file = res_directory / "p-ishares-core-s-and-p-total-us-stock-market-etf-3-31.pdf"
        
        if not smallest_file.exists():
            logger.error(f"❌ Test file not found: {smallest_file.name}")
            return False
            
        pdf_files = [smallest_file]
        logger.info(f"📋 Processing smallest file for testing: {smallest_file.name} (320k)")
        
        for pdf_file in pdf_files:
            logger.info(f"  • {pdf_file.name}")
        
        # Process and index documents
        logger.info("🔄 Processing and indexing documents...")
        
        # Process the single file directly instead of using process_directory
        try:
            processed_doc = doc_processor.process_pdf(smallest_file)
            search_documents = doc_processor.convert_to_search_documents(processed_doc)
        except Exception as e:
            logger.error(f"❌ Failed to process {smallest_file.name}: {e}")
            return False
        
        if not search_documents:
            logger.error("❌ No documents were processed successfully")
            return False
        
        logger.info(f"📊 Processed {len(search_documents)} document chunks")
        
        # Index documents in Azure AI Search
        logger.info("☁️  Indexing documents in Azure AI Search...")
        indexed_count = await search_client.index_documents(search_documents)
        
        if indexed_count > 0:
            logger.success(f"✅ Successfully indexed {indexed_count}/{len(search_documents)} documents")
            
            # Verify the index
            logger.info("🔍 Verifying index status...")
            doc_count = await search_client.get_document_count()
            logger.info(f"📈 Total documents in index: {doc_count}")
            
            # Test a simple search
            logger.info("🧪 Testing search functionality...")
            test_results = await search_client.search_documents(
                query="ETF investment strategy",
                top=3
            )
            logger.info(f"🔍 Test search returned {len(test_results)} results")
            
            if test_results:
                logger.info("📄 Sample result:")
                sample = test_results[0]
                logger.info(f"   Title: {sample.title}")
                logger.info(f"   Source: {Path(sample.source).name}")
                logger.info(f"   Score: {sample.score:.3f}")
                logger.info(f"   Content preview: {sample.content[:100]}...")
            
            return True
        else:
            logger.error("❌ Failed to index any documents")
            return False
            
    except Exception as e:
        logger.error(f"💥 Indexing failed with error: {e}")
        logger.exception("Full error details:")
        return False


def setup_logging():
    """Configure logging for the script."""
    logger.remove()  # Remove default handler
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        level="INFO"
    )


if __name__ == "__main__":
    setup_logging()
    
    logger.info("🎯 ETF Prospectus Indexing Script")
    logger.info("=" * 50)
    
    # Run the indexing process
    success = asyncio.run(main())
    
    if success:
        logger.success("🎉 Indexing completed successfully!")
        logger.info("You can now search ETF prospectuses using the Search API")
    else:
        logger.error("💥 Indexing failed!")
        sys.exit(1)
