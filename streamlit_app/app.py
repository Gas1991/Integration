import streamlit as st
from pymongo import MongoClient
import urllib.parse
import certifi
from datetime import datetime

# Configure Streamlit page
st.set_page_config(page_title="MongoDB Connection Tester", layout="wide")
st.title("🔍 MongoDB Atlas Connection Test")

# Securely format the URI (already properly formatted in your case)
uri = "mongodb+srv://ghassengharbi191:RLQuuAeyYH8n3icB@cluster0.wrzdaw1.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

def test_mongodb_connection(uri):
    """Test MongoDB connection and return results"""
    start_time = datetime.now()
    result = {
        "status": "unknown",
        "message": "",
        "server_info": None,
        "collections": [],
        "duration": 0
    }
    
    try:
        # Create secure connection
        client = MongoClient(
            uri,
            tls=True,
            tlsCAFile=certifi.where(),
            connectTimeoutMS=5000,
            serverSelectionTimeoutMS=5000
        )
        
        # Test basic connection
        server_info = client.server_info()
        result["status"] = "success"
        result["message"] = "✅ Successfully connected to MongoDB Atlas!"
        result["server_info"] = {
            "host": client.HOST,
            "port": client.PORT,
            "version": server_info.get("version"),
            "ok": server_info.get("ok")
        }
        
        # Test database access
        db = client.get_database()
        result["collections"] = db.list_collection_names()
        
    except Exception as e:
        result["status"] = "error"
        result["message"] = f"❌ Connection failed: {str(e)}"
    finally:
        result["duration"] = (datetime.now() - start_time).total_seconds()
        if 'client' in locals():
            client.close()
            
    return result

# Run the test when the button is clicked
if st.button("Test MongoDB Connection", type="primary"):
    st.write("### Testing connection to:")
    st.code(uri.split('@')[0] + "@...")  # Show partial URI for security
    
    with st.spinner("Connecting to MongoDB Atlas..."):
        test_result = test_mongodb_connection(uri)
    
    # Display results
    st.divider()
    
    if test_result["status"] == "success":
        st.success(test_result["message"])
        st.metric("Connection Time", f"{test_result['duration']:.3f} seconds")
        
        st.write("#### Server Information")
        st.json(test_result["server_info"])
        
        st.write(f"#### Collections Found ({len(test_result['collections'])})")
        st.write(test_result["collections"])
    else:
        st.error(test_result["message"])
        
    st.divider()
    st.write("Connection test completed at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# Security note
st.warning("""
**Important Security Notice:**  
This tester validates your connection but should not be deployed with your credentials. 
For production, use environment variables or Streamlit secrets management.
""")
