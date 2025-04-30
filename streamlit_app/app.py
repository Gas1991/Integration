import streamlit as st
from pymongo import MongoClient
import pandas as pd
import os
from PIL import Image
import gridfs
from urllib.parse import quote_plus
import time

# 🔐 Configuration MongoDB sécurisée
username = quote_plus('ghassengharbi191')
password = quote_plus('RLQuuAeyYH8n3icB')
MONGO_URI = f'mongodb+srv://{username}:{password}@cluster0.wrzdaw1.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
MONGO_DB = 'Mytek_database'
COLLECTION_NAME = 'Produits_mytek'

# 📁 Répertoires locaux
IMAGES_DIR = r'D:\scarpy\mytek\crawling\images'
CACHE_DIR = "cache"
CACHE_FILE = os.path.join(CACHE_DIR, "produits_cache.csv")

# ⚙️ Initialisation Streamlit
st.set_page_config(layout="wide")
st.title("📊 Produits Dashboard")

# 📦 Connexion MongoDB
@st.cache_resource(ttl=3600)
def get_mongo_client():
    try:
        client = MongoClient(MONGO_URI, connectTimeoutMS=30000, socketTimeoutMS=None)
        client.admin.command('ping')
        return client
    except Exception as e:
        st.error(f"🔌 Erreur de connexion MongoDB : {str(e)}")
        st.stop()

# 📥 Charger les données depuis MongoDB
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

# 📤 Sauvegarder le cache CSV
def save_cache(df):
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    df.to_csv(CACHE_FILE, index=False)

# 📥 Charger le cache CSV
def load_cache():
    return pd.read_csv(CACHE_FILE)

# 🖥️ Fonction principale Streamlit
def main():
    # Hide Streamlit Toolbar
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

    # Vérifie et crée le dossier images si besoin
    if not os.path.exists(IMAGES_DIR):
        os.makedirs(IMAGES_DIR)
        st.warning(f"Dossier images créé : {IMAGES_DIR}")

    # Chargement initial des données en session
    if 'df' not in st.session_state:
        if os.path.exists(CACHE_FILE):
            df = load_cache()
            st.success("✅ Cache produit chargé.")
        else:
            st.info("📦 Pas de cache trouvé, chargement depuis DB.")
            df = load_data_from_mongo()
            save_cache(df)
            st.success("✅ Cache produit sauvegardé.")
        st.session_state.df = df

    # Bouton de mise à jour MongoDB
    if st.button("🔄 Recharger depuis DB (forcer MAJ cache)"):
        df = load_data_from_mongo()
        save_cache(df)
        st.session_state.df = df
        last_mod_time = time.ctime(os.path.getmtime(CACHE_FILE))
        st.success("✅ Cache mis à jour depuis MongoDB.")
        st.info(f"📂 Fichier cache mis à jour : {CACHE_FILE}")
        st.write(f"🕒 Dernière mise à jour : {last_mod_time}")

    # Récupération du dataframe depuis la session
    df = st.session_state.df

    # Onglets de navigation
    tab1, tab2 = st.tabs(["📑 Produits", "🖼️ Images"])

    with tab1:
        st.header("📝 Liste des Produits")

        if not df.empty:
            columns_to_show = [
                'sku', 'title', 'page_type', 'description_meta', 'value_html_inner',
                'savoir_plus_text', 'image_url'
            ]
            existing_columns = [col for col in columns_to_show if col in df.columns]
            df_filtered = df[existing_columns]

            # Exclure les lignes vides
            df_filtered = df_filtered.dropna(subset=existing_columns, how='all')  # Remove rows where all selected columns are empty
            df_filtered = df_filtered[df_filtered.apply(lambda row: row.astype(str).str.strip().any(), axis=1)]  # Remove rows with all empty values

            # Pagination: Afficher chaque 10 lignes
            page_size = 10
            num_pages = len(df_filtered) // page_size + (1 if len(df_filtered) % page_size != 0 else 0)
            page = st.selectbox("Sélectionner la page", range(1, num_pages + 1))
            start_row = (page - 1) * page_size
            end_row = start_row + page_size

            # Filtrer les données selon la page sélectionnée
            df_filtered = df_filtered[start_row:end_row]

            # Champ de recherche
            search_term = st.text_input("🔍 Rechercher un produit", "")
            if search_term:
                df_filtered = df_filtered[
                    df_filtered.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)
                ]

            st.dataframe(df_filtered, height=600, use_container_width=True)

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
                client = get_mongo_client()
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

# ✅ Exécution
if __name__ == "__main__":
    main()
