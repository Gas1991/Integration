import streamlit as st
from pymongo import MongoClient
import urllib.parse
import certifi
from datetime import datetime

st.title("🔌 MongoDB Connection Tester")

# Connection form
with st.form("connection_form"):
    st.subheader("Connection Parameters")
    
    mongo_uri = st.text_input(
        "MongoDB URI",
        "mongodb+srv://username:password@cluster0.mongodb.net/database?retryWrites=true&w=majority"
    )
    
    test_type = st.radio(
        "Test Type",
        ["Simple Connection", "List Collections", "Sample Document Query"]
    )
    
    submitted = st.form_submit_button("Test Connection")

if submitted:
    st.divider()
    st.subheader("Test Results")
    
    with st.spinner("Testing connection..."):
        start_time = datetime.now()
        
        try:
            # Create client with SSL configuration
            client = MongoClient(
                mongo_uri,
                tls=True,
                tlsCAFile=certifi.where(),
                connectTimeoutMS=5000,
                serverSelectionTimeoutMS=5000
            )
            
            # Test connection
            if test_type == "Simple Connection":
                # Basic ping test
                client.admin.command('ping')
                st.success("✅ Successfully connected to MongoDB!")
                st.json({
                    "status": "connected",
                    "server_info": client.server_info(),
                    "response_time": f"{(datetime.now() - start_time).total_seconds():.2f}s"
                })
                
            elif test_type == "List Collections":
                # Get database name from URI
                db_name = mongo_uri.split("/")[-1].split("?")[0]
                db = client[db_name]
                collections = db.list_collection_names()
                
                st.success(f"✅ Found {len(collections)} collections in database '{db_name}'")
                st.write("Collections:", collections)
                
            elif test_type == "Sample Document Query":
                db_name = mongo_uri.split("/")[-1].split("?")[0]
                db = client[db_name]
                collections = db.list_collection_names()
                
                if collections:
                    selected_collection = st.selectbox("Select collection", collections)
                    sample_doc = db[selected_collection].find_one()
                    
                    if sample_doc:
                        st.success(f"✅ Found document in '{selected_collection}' collection")
                        st.json(sample_doc)
                    else:
                        st.warning(f"⚠️ No documents found in '{selected_collection}'")
                else:
                    st.warning("⚠️ No collections found in database")
                    
        except Exception as e:
            st.error(f"❌ Connection failed: {str(e)}")
            
        st.write(f"⏱️ Test duration: {(datetime.now() - start_time).total_seconds():.2f} seconds")
