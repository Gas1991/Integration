from urllib.parse import quote_plus
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

username = quote_plus('ghassengharbi191')
password = quote_plus('RLQuuAeyYH8n3icB')
MONGO_URI = f'mongodb+srv://{username}:{password}@cluster0.wrzdaw1.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
MONGO_DB = 'Mytek_database'
COLLECTION_NAME = 'Produits_mytek'

try:
    # Create a new client and connect to the server
    client = MongoClient(MONGO_URI)
    
    # Send a ping to confirm a successful connection
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
    
    # Test accessing the collection
    db = client[MONGO_DB]
    collection = db[COLLECTION_NAME]
    
    # Count documents as a simple test
    count = collection.count_documents({})
    print(f"Collection contains {count} documents")
    
except ConnectionFailure as e:
    print(f"Could not connect to MongoDB: {e}")
except OperationFailure as e:
    print(f"Authentication or operation failed: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
finally:
    # Close the connection
    client.close()
