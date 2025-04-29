import streamlit as st
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
COLLECTION_NAME = 'Produits_mytek'
IMAGES_DIR = r'D:\scarpy\mytek\crawling\images'
CACHE_DIR = "cache"
CACHE_FILE = os.path.join(CACHE_DIR, "produits_cache.csv")

# Initialisation Streamlit
st.set_page_config(layout="wide")
st.title("Mytek Produits Dashboard")

@st.cache_resource(ttl=3600)
def get_mongo_client():
    try:
        client = MongoClient(MONGO_URI, connectTimeoutMS=30000, socketTimeoutMS=None)
        client.admin.command('ping')
        return client
    except Exception as e:
        st.error(f"🔌 Erreur de connexion MongoDB: {str(e)}")
        st.stop()

def load_data_from_mongo():
    client = get_mongo_client()
    db = client[MONGO_DB]
    docs = list(db[COLLECTION_NAME].find())
    if docs:
        df = pd.json_normalize(docs)
        if '_id' in df.columns:
            df['_id'] = df['_id'].astype(str)
        return df
    else:
        return pd.DataFrame()

def save_cache(df):
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    df.to_csv(CACHE_FILE, index=False)

def load_cache():
    return pd.read_csv(CACHE_FILE)

def main():
    if not os.path.exists(IMAGES_DIR):
        os.makedirs(IMAGES_DIR)
        st.warning(f"Dossier images créé: {IMAGES_DIR}")

    # Contrôle de cache et bouton de mise à jour
    use_cache = os.path.exists(CACHE_FILE)
    if use_cache:
        st.success("✅ Cache produit chargé depuis le fichier CSV.")
        if st.button("🔄 Recharger depuis MongoDB (forcer MAJ cache)"):
            df = load_data_from_mongo()
            save_cache(df)
            st.experimental_rerun()
        else:
            df = load_cache()
    else:
        st.info("📦 Pas de cache trouvé, chargement depuis MongoDB.")
        df = load_data_from_mongo()
        save_cache(df)

    tab1, tab2 = st.tabs(["Produits", "Images"])

    with tab1:
        st.header("Liste des Produits")

        if not df.empty:
            columns_to_show = [
                'sku', 'title', 'page_type', 'description_meta', 'product_overview', 'savoir_plus_text', 'image_url'
            ]
            existing_columns = [col for col in columns_to_show if col in df.columns]
            df_filtered = df[existing_columns]

            search_term = st.text_input("Rechercher", "")
            if search_term:
                df_filtered = df_filtered[df_filtered.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)]

            st.dataframe(df_filtered, height=600, use_container_width=True)

            if 'special_price' in df.columns:
                st.metric("Moyenne des prix", f"{df['special_price'].mean():.2f} DT")
        else:
            st.warning("Aucun produit disponible.")

    with tab2:
        st.header("Gestion des Images")

        image_option = st.radio("Source", ["Local", "GridFS"])

        if image_option == "Local":
            try:
                images = [f for f in os.listdir(IMAGES_DIR) if f.lower().endswith(('.jpg', '.png'))]
                if images:
                    for img_file in images:
                        img_path = os.path.join(IMAGES_DIR, img_file)
                        st.image(img_path, caption=img_file)
                else:
                    st.warning("Aucune image disponible dans le dossier local.")
            except Exception as e:
                st.error(f"Erreur images locales: {str(e)}")

        else:
            try:
                client = get_mongo_client()
                db = client[MONGO_DB]
                fs = gridfs.GridFS(db)
                files = list(fs.find())
                if files:
                    for file_data in files:
                        st.image(file_data.read(), caption=file_data.filename)
                else:
                    st.warning("Aucun fichier dans GridFS")
            except Exception as e:
                st.error(f"Erreur GridFS: {str(e)}")

if __name__ == "__main__":
    main()
