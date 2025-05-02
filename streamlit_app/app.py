import streamlit as st
from pymongo import MongoClient
import pandas as pd
import os
from PIL import Image
import gridfs
from urllib.parse import quote_plus
from datetime import datetime

# 🔐 Configuration MongoDB
username = quote_plus('ghassengharbi191')
password = quote_plus('RLQuuAeyYH8n3icB')
MONGO_URI = f'mongodb+srv://{username}:{password}@cluster0.wrzdaw1.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
MONGO_DB = 'Mytek_database'
COLLECTION_NAME = 'Produits_mytek'

IMAGES_DIR = r'D:\scarpy\mytek\crawling\images'

st.set_page_config(layout="wide")
st.title("📊 Produits Dashboard")

@st.cache_resource(ttl=86400)
def get_mongo_client():
    try:
        client = MongoClient(MONGO_URI, connectTimeoutMS=30000, socketTimeoutMS=None)
        client.admin.command('ping')
        return client
    except Exception as e:
        st.error(f"🔌 Erreur de connexion MongoDB : {str(e)}")
        st.stop()

@st.cache_data(ttl=86400)
def load_data_from_mongo():
    client = get_mongo_client()  # This will ensure the MongoDB client is opened only once
    try:
        db = client[MONGO_DB]
        docs = list(db[COLLECTION_NAME].find())
        if docs:
            df = pd.json_normalize(docs)
            if '_id' in df.columns:
                df['_id'] = df['_id'].astype(str)
            return df
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Erreur de chargement des données : {str(e)}")
        return pd.DataFrame()
    # No client.close() here as the client is kept open during the app's lifecycle

def clean_dataframe_for_display(df):
    for col in df.columns:
        if df[col].apply(lambda x: isinstance(x, (list, dict))).any():
            df[col] = df[col].astype(str)
    return df

def main():
    if not os.path.exists(IMAGES_DIR):
        os.makedirs(IMAGES_DIR)
        st.warning(f"Dossier images créé : {IMAGES_DIR}")

    st.markdown(
        """
        <style>
        [data-testid="stElementToolbar"] {
            display: none;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Chargement initial des données en session + timestamp
    if 'df' not in st.session_state or 'last_update' not in st.session_state:
        st.info("📦 Chargement des produits depuis DB ...")
        df = load_data_from_mongo()
        st.session_state.df = df
        st.session_state.last_update = datetime.now()
        st.success("✅ Données chargées et mises en cache.")

    st.caption(f"🕒 Dernière mise à jour : {st.session_state.last_update.strftime('%d/%m/%Y %H:%M:%S')}")

    if st.button("🔄 Forcer mise à jour des données DB"):
        load_data_from_mongo.clear()
        df = load_data_from_mongo()
        st.session_state.df = df
        st.session_state.last_update = datetime.now()
        st.success("✅ Cache actualisé et données rechargées.")

    df = st.session_state.df

    tab1, tab2 = st.tabs(["📑 Produits", "🖼️ Images"])

    with tab1:
        st.header("📝 Liste des Produits")
        if not df.empty:
            columns_to_show = [
                'sku','title','description_meta','fiche_technique', 'value_html_inner',
                'savoir_plus_text', 'image_url'
            ]
            existing_columns = [col for col in columns_to_show if col in df.columns]
            df_filtered = df[existing_columns]

            search_term = st.text_input("🔍 Rechercher un produit", "")
            if search_term:
                df_filtered = df_filtered[
                    df_filtered.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)
                ]

            df_filtered = clean_dataframe_for_display(df_filtered)
            st.dataframe(df_filtered, height=600, use_container_width=True)

            if 'special_price' in df.columns:
                try:
                    df['special_price'] = pd.to_numeric(df['special_price'], errors='coerce')
                    avg_price = df['special_price'].mean(skipna=True)
                    if pd.notnull(avg_price):
                        st.metric("💰 Moyenne des prix", f"{avg_price:.2f} DT")
                    else:
                        st.info("💰 Aucune valeur de prix valide pour calculer la moyenne.")
                except Exception as e:
                    st.error(f"Erreur moyenne : {str(e)}")
        else:
            st.warning("Aucun produit disponible.")

    with tab2:
        st.header("🖼️ Gestion des Images")
        image_option = st.radio("📂 Source des images :", ["Local", "GridFS"])

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
                st.error(f"❌ Erreur chargement images locales : {str(e)}")

        else:
            try:
                client = get_mongo_client()  # Use the existing Mongo client to interact with GridFS
                db = client[MONGO_DB]
                fs = gridfs.GridFS(db)
                files = list(fs.find())
                if files:
                    for file_data in files:
                        st.image(file_data.read(), caption=file_data.filename)
                else:
                    st.warning("Aucun fichier image dans GridFS.")
            except Exception as e:
                st.error(f"❌ Erreur chargement GridFS : {str(e)}")

if __name__ == "__main__":
    main()
