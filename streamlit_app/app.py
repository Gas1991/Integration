from pymongo import MongoClient
import pandas as pd
import os
from PIL import Image
import gridfs
from urllib.parse import quote_plus

# Configuration sécurisée MongoDB
username = quote_plus('ghassengharbi191')
password = quote_plus('RLQuuAeyYH8n3icB')
MONGO_URI = f'mongodb+srv://{username}:{password}@cluster0.wrzdaw1.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
MONGO_DB = 'Mytek_database'
IMAGES_DIR = r'D:\scarpy\mytek\crawling\images'

# Initialisation Streamlit
st.set_page_config(layout="wide")
st.title("Mytek Analytics Dashboard")

@st.cache_resource(ttl=3600)
def get_mongo_client():
    """Crée une connexion MongoDB sécurisée"""
    try:
        client = MongoClient(MONGO_URI, connectTimeoutMS=30000, socketTimeoutMS=None)
        client.admin.command('ping')  # Test de connexion
        return client
    except Exception as e:
        st.error(f"🔌 Erreur de connexion MongoDB: {str(e)}")
        st.stop()

def main():
    # Vérification du dossier images
    if not os.path.exists(IMAGES_DIR):
        os.makedirs(IMAGES_DIR)
        st.warning(f"Dossier images créé: {IMAGES_DIR}")

    client = get_mongo_client()
    db = client[MONGO_DB]
    
    # Interface utilisateur
    tab1, tab2 = st.tabs(["Produits", "Images"])
    
    with tab1:
        st.header("Liste des Produits")
        try:
            collections = db.list_collection_names()
            selected_collection = st.selectbox("Collection", collections)
            
            # Options de requête
            limit = st.number_input("Nombre max de documents", 1, 30000, 100)
            query_filter = st.text_input("Filtre (JSON)", '{}')
            
            # Exécution de la requête
            try:
                filter_dict = eval(query_filter)  # Attention: utiliser avec précaution
                docs = list(db[selected_collection].find(filter_dict).limit(limit))
                
                if docs:
                    df = pd.json_normalize(docs)
                    if '_id' in df.columns:
                        df['_id'] = df['_id'].astype(str)
                    
                    st.dataframe(df, height=600)
                    
                    # Statistiques
                    if 'special_price' in df.columns:
                        st.metric("Moyenne des prix", f"{df['special_price'].mean():.2f} DT")
                else:
                    st.warning("Aucun document trouvé!")
            except Exception as qe:
                st.error(f"Erreur de requête: {qe}")
                
        except Exception as e:
            st.error(f"Erreur MongoDB: {str(e)}")
    
    with tab2:
        st.header("Gestion des Images")
        image_option = st.radio("Source", ["Local", "GridFS"])
        
        if image_option == "Local":
            try:
                images = [f for f in os.listdir(IMAGES_DIR) if f.endswith(('.jpg', '.png'))]
                selected_image = st.selectbox("Choisir une image", images)
                img_path = os.path.join(IMAGES_DIR, selected_image)
                st.image(img_path, caption=selected_image)
            except Exception as e:
                st.error(f"Erreur images locales: {str(e)}")
        else:
            try:
                fs = gridfs.GridFS(db)
                files = list(fs.find())
                if files:
                    selected_file = st.selectbox("Fichiers GridFS", [f.filename for f in files])
                    file_data = fs.find_one({'filename': selected_file})
                    st.image(file_data.read(), caption=selected_file)
                else:
                    st.warning("Aucun fichier dans GridFS")
            except Exception as e:
                st.error(f"Erreur GridFS: {str(e)}")

if __name__ == "__main__":
    main()
