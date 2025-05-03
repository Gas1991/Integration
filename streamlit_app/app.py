import streamlit as st
from pymongo import MongoClient
import pandas as pd
from datetime import datetime
from urllib.parse import quote_plus

# 🔐 Configuration MongoDB
username = quote_plus('ghassengharbi191')
password = quote_plus('RLQuuAeyYH8n3icB')
MONGO_URI = f'mongodb+srv://{username}:{password}@cluster0.wrzdaw1.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
MONGO_DB = 'Mytek_database'
COLLECTION_NAME = 'Produits_mytek'

# 🎨 Streamlit page config
st.set_page_config(layout="wide")
st.title("📊 Produits Dashboard")

# 📦 Mongo client cached resource
@st.cache_resource(ttl=86400)
def get_mongo_client():
    try:
        client = MongoClient(MONGO_URI, connectTimeoutMS=30000, socketTimeoutMS=None)
        client.admin.command('ping')
        return client
    except Exception as e:
        st.error(f"🔌 Erreur de connexion MongoDB : {str(e)}")
        st.stop()

# 📥 Load data from MongoDB and cache
@st.cache_data(ttl=86400)
def load_data_from_mongo():
    try:
        client = get_mongo_client()
        db = client[MONGO_DB]
        docs = list(db[COLLECTION_NAME].find())
        if not docs:
            return pd.DataFrame()
        df = pd.json_normalize(docs)
        if '_id' in df.columns:
            df['_id'] = df['_id'].astype(str)
        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement des données : {e}")
        return pd.DataFrame()

# 📑 Clean DataFrame for display
def clean_dataframe_for_display(df):
    for col in df.columns:
        if df[col].apply(lambda x: isinstance(x, (list, dict))).any():
            df[col] = df[col].astype(str)
    return df

# 🚀 Main app logic
def main():
    st.markdown("""
        <style>
        [data-testid="stElementToolbar"] { display: none; }
        </style>
        """, unsafe_allow_html=True)

    # Load data into session state if not already loaded
    if 'df' not in st.session_state or 'last_update' not in st.session_state:
        st.info("📦 Chargement des produits depuis la base de données...")
        df = load_data_from_mongo()
        st.session_state.df = df
        st.session_state.last_update = datetime.now()
        st.success("✅ Données chargées et mises en cache.")

    st.caption(f"🕒 Dernière mise à jour : {st.session_state.last_update.strftime('%d/%m/%Y %H:%M:%S')}")

    # Button to force reload cache
    if st.button("🔄 Forcer la mise à jour des données"):
        load_data_from_mongo.clear()
        df = load_data_from_mongo()
        st.session_state.df = df
        st.session_state.last_update = datetime.now()
        st.success("✅ Données et cache rechargés.")

    df = st.session_state.df

    # Tabs for dashboard
    tab1 = st.tabs(["📑 Liste des Produits"])[0]

    with tab1:
        st.header("📝 Produits")
        if not df.empty:
            columns_to_show = [
                'sku', 'title', 'description_meta', 'fiche_technique',
                'value_html_inner', 'savoir_plus_text', 'image_url'
            ]
            existing_columns = [col for col in columns_to_show if col in df.columns]
            df_filtered = df[existing_columns]

            # Search bar
            search_term = st.text_input("🔍 Rechercher un produit", "")
            if search_term:
                mask = df_filtered.astype(str).apply(lambda row: row.str.contains(search_term, case=False, na=False)).any(axis=1)
                df_filtered = df_filtered[mask]

            df_filtered = clean_dataframe_for_display(df_filtered)
            st.dataframe(df_filtered, height=600, use_container_width=True)

            # Optional : Export CSV
            csv = df_filtered.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Télécharger les données en CSV",
                data=csv,
                file_name="produits_mytek.csv",
                mime="text/csv"
            )

        else:
            st.warning("Aucun produit disponible dans la base.")

if __name__ == "__main__":
    main()
