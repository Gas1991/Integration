# 📦 Imports
import streamlit as st
from pymongo import MongoClient
import pandas as pd
from datetime import datetime
from urllib.parse import quote_plus

# 📌 Configuration MongoDB
USERNAME = quote_plus('ghassengharbi191')
PASSWORD = quote_plus('RLQuuAeyYH8n3icB')
MONGO_URI = (
    f'mongodb+srv://{USERNAME}:{PASSWORD}@cluster0.wrzdaw1.mongodb.net/'
    '?retryWrites=true&w=majority&appName=Cluster0'
)
MONGO_DB = 'Mytek_database'
COLLECTION_NAME = 'Produits_mytek'

# 🔐 Authentification
VALID_USERNAME = "admin"
VALID_PASSWORD = "admin123"

# 🖥️ Configuration Streamlit
st.set_page_config(layout="wide")
st.title("📊 Dashboard Produits")

# 📡 Connexion MongoDB
@st.cache_resource(ttl=86400)
def get_mongo_client():
    try:
        client = MongoClient(MONGO_URI, connectTimeoutMS=30000, socketTimeoutMS=None)
        client.admin.command('ping')
        return client
    except Exception as e:
        st.error(f"🔌 Erreur de connexion MongoDB : {str(e)}")
        st.stop()

# 📄 Chargement des données depuis MongoDB
@st.cache_data(ttl=86400)
def load_data_from_mongo():
    client = get_mongo_client()
    db = client[MONGO_DB]
    docs = list(db[COLLECTION_NAME].find())
    if docs:
        df = pd.json_normalize(docs)
        if '_id' in df.columns:
            df['_id'] = df['_id'].astype(str)
        return df
    return pd.DataFrame()

# 🧹 Nettoyage des colonnes complexes pour affichage
def clean_dataframe_for_display(df):
    for col in df.columns:
        if df[col].apply(lambda x: isinstance(x, (list, dict))).any():
            df.loc[:, col] = df[col].astype(str)
    return df

# 🔐 Gestion de connexion utilisateur
def check_login():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        with st.form("login_form"):
            st.subheader("🔒 Connexion requise")
            login_username = st.text_input("Nom d'utilisateur")
            login_password = st.text_input("Mot de passe", type="password")
            login_button = st.form_submit_button("Se connecter")

            if login_button:
                if login_username == VALID_USERNAME and login_password == VALID_PASSWORD:
                    st.session_state.authenticated = True
                    st.success("✅ Connexion réussie")
                else:
                    st.error("❌ Identifiants incorrects.")
        return False
    return True

# 📊 Main dashboard
def main():
    # 🔧 Cache barre des options Streamlit
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

    # Authentification utilisateur
    if not check_login():
        return

    # Bouton déconnexion
    if st.button("🚪 Se déconnecter"):
        st.session_state.authenticated = False
        st.rerun()

    # Chargement initial des données
    if 'df' not in st.session_state or 'last_update' not in st.session_state:
        st.info("📦 Chargement des produits depuis la base de données...")
        df = load_data_from_mongo()
        st.session_state.df = df
        st.session_state.last_update = datetime.now()
        st.success("✅ Données chargées et mises en cache.")

    # Info dernière mise à jour
    st.caption(f"🕒 Dernière mise à jour : {st.session_state.last_update.strftime('%d/%m/%Y %H:%M:%S')}")

    # Bouton de rafraîchissement
    if st.button("🔄 Forcer mise à jour des données"):
        load_data_from_mongo.clear()
        df = load_data_from_mongo()
        st.session_state.df = df
        st.session_state.last_update = datetime.now()
        st.success("✅ Cache vidé et données rechargées.")

    df = st.session_state.df

    # 📑 Onglet produits
    tab1 = st.tabs(["📑 Produits"])[0]

    with tab1:
        st.header("📝 Liste des Produits")

        if not df.empty:
            columns_to_show = [
                'sku', 'title', 'description_meta', 'fiche_technique',
                'value_html_inner', 'savoir_plus_text', 'image_url'
            ]
            existing_columns = [col for col in columns_to_show if col in df.columns]
            df_filtered = df[existing_columns]

            # Recherche full-text simple
            search_term = st.text_input("🔍 Rechercher un produit")
            if search_term:
                combined_text = df_filtered.astype(str).agg(' '.join, axis=1)
                mask = combined_text.str.contains(search_term, case=False, na=False)
                df_filtered = df_filtered[mask]

            # Nettoyage et affichage
            df_filtered = clean_dataframe_for_display(df_filtered)
            st.dataframe(df_filtered, height=600, use_container_width=True)

        else:
            st.warning("⚠️ Aucun produit disponible.")

# 🚀 Exécution
if __name__ == "__main__":
    main()
