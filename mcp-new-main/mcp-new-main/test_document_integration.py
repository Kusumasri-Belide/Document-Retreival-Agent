#!/usr/bin/env python3
"""
Test script to verify document agent integration with MCP server
"""
import requests
import json
import os
import sys

# Add the main app path for imports
sys.path.append('/home/ubuntu/mcp-new')

def test_oauth_flow():
    """Test OAuth endpoints"""
    base_url = "http://localhost:8001"
    
    print("🔐 Testing OAuth endpoints...")
    
    # Test discovery endpoint
    try:
        resp = requests.get(f"{base_url}/.well-known/oauth-authorization-server")
        if resp.status_code == 200:
            print("✅ OAuth discovery endpoint working")
        else:
            print(f"❌ OAuth discovery failed: {resp.status_code}")
    except Exception as e:
        print(f"❌ OAuth discovery error: {e}")

def test_mcp_tools():
    """Test MCP tools (requires valid OAuth token)"""
    base_url = "http://localhost:8001"
    
    # This would require a real OAuth token in production
    # For testing, you'd need to go through the full OAuth flow
    print("🛠️ MCP tool testing requires OAuth token...")
    print("   Use ServiceNow or implement OAuth flow to test tools")

def test_document_agent_imports():
    """Test if document agent modules can be imported"""
    print("📚 Testing document agent imports...")
    
    try:
        from backend.llm_answer import generate_answer
        print("✅ llm_answer module imported")
    except ImportError as e:
        print(f"❌ llm_answer import failed: {e}")
    
    try:
        from backend.retriever import retrieve_relevant_chunks
        print("✅ retriever module imported")
    except ImportError as e:
        print(f"❌ retriever import failed: {e}")
    
    try:
        from backend.config import PROCESSED_DIR, VECTOR_STORE_DIR
        print("✅ config module imported")
        print(f"   PROCESSED_DIR: {PROCESSED_DIR}")
        print(f"   VECTOR_STORE_DIR: {VECTOR_STORE_DIR}")
    except ImportError as e:
        print(f"❌ config import failed: {e}")

def test_data_availability():
    """Check if document data is available"""
    print("📄 Testing data availability...")
    
    try:
        from backend.config import PROCESSED_DIR, VECTOR_STORE_DIR
        import os
        
        # Check processed documents
        if os.path.exists(PROCESSED_DIR):
            docs = [f for f in os.listdir(PROCESSED_DIR) if f.endswith('.txt')]
            print(f"✅ Found {len(docs)} processed documents")
            if docs:
                print(f"   Sample docs: {docs[:3]}")
        else:
            print("❌ Processed directory not found")
        
        # Check vector store
        index_path = os.path.join(VECTOR_STORE_DIR, "faiss_index.bin")
        chunks_path = os.path.join(VECTOR_STORE_DIR, "chunks.pkl")
        
        if os.path.exists(index_path) and os.path.exists(chunks_path):
            print("✅ Vector store files found")
        else:
            print("❌ Vector store not built - run reindex_documents")
            
    except Exception as e:
        print(f"❌ Data check failed: {e}")

def main():
    print("🧪 MCP Document Agent Integration Test")
    print("=" * 50)
    
    test_document_agent_imports()
    print()
    test_data_availability()
    print()
    test_oauth_flow()
    print()
    test_mcp_tools()
    
    print("\n🎉 Test complete!")
    print("\n📋 Next steps:")
    print("   1. Ensure OAuth credentials are set up")
    print("   2. Start the MCP server: ./manage_server.sh start")
    print("   3. Configure ServiceNow with OAuth details")
    print("   4. Test tools through ServiceNow MCP integration")

if __name__ == "__main__":
    main()