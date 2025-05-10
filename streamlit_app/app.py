import streamlit as st
from pymongo import MongoClient
import pandas as pd
from datetime import datetime
from urllib.parse import quote_plus
import math

# 🔐 Configuration MongoDB
username = quote_plus('ghassengharbi191')
password = quote_plus('RLQuuAeyYH8n3icB')
MONGO_URI = f'mongodb+srv://{username}:{password}@cluster0.wrzdaw1.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
MONGO_DB = 'Mytek_database'
COLLECTION_NAME = 'Produits_mytek'

st.set_page_config(layout="wide")
st.title("📊 Produits Dashboard")

# Connect to MongoDB
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

def clean_dataframe_for_display(df):
    for col in df.columns:
        if df[col].apply(lambda x: isinstance(x, (list, dict))).any():
            df.loc[:, col] = df[col].astype(str)
    return df

def main():
    st.markdown("""
        <style>
        [data-testid="stElementToolbar"] {
            display: none;
        }
        </style>
        """, unsafe_allow_html=True)

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

    tab1 = st.tabs(["📑 Produits"])[0]

    with tab1:
        st.header("📝 Liste des Produits")
        if not df.empty:
            columns_to_show = [
                'sku', 'title', 'description_meta', 'fiche_technique', 'value_html_inner',
                'savoir_plus_text', 'image_url'
            ]
            existing_columns = [col for col in columns_to_show if col in df.columns]
            df_filtered = df[existing_columns]

            search_term = st.text_input("🔍 Rechercher un produit", "")
            if search_term:
                combined_text = df_filtered.astype(str).agg(' '.join, axis=1)
                mask = combined_text.str.contains(search_term, case=False, na=False)
                df_filtered = df_filtered[mask]

            df_filtered = clean_dataframe_for_display(df_filtered)

            # Pagination
            page_size = 16
            total_products = len(df_filtered)
            total_pages = math.ceil(total_products / page_size)

            if 'current_page' not in st.session_state:
                st.session_state.current_page = 1

            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                if st.button("⬅️ Page précédente") and st.session_state.current_page > 1:
                    st.session_state.current_page -= 1
            with col3:
                if st.button("➡️ Page suivante") and st.session_state.current_page < total_pages:
                    st.session_state.current_page += 1

            start_idx = (st.session_state.current_page - 1) * page_size
            end_idx = start_idx + page_size

            st.caption(f"Page {st.session_state.current_page} sur {total_pages}")
            st.dataframe(df_filtered.iloc[start_idx:end_idx], height=600, use_container_width=True)

        else:
            st.warning("Aucun produit disponible.")

if __name__ == "__main__":
    main()
