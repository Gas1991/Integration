import streamlit as st
from pymongo import MongoClient
import pandas as pd
import os
from urllib.parse import quote_plus

username = quote_plus('ghassengharbi191')
password = quote_plus('RLQuuAeyYH8n3icB')
MONGO_URI = f'mongodb+srv://{username}:{password}@cluster0.wrzdaw1.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
MONGO_DB = 'Mytek_database'
COLLECTION_NAME = 'Produits_mytek'

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)
CSV_PATH = os.path.join(CACHE_DIR, "produits_cache.csv")

st.set_page_config(layout="wide")
st.title("📊 Mytek Produits Dashboard")

@st.cache_resource(ttl=3600)
def get_mongo_client():
    try:
        client = MongoClient(MONGO_URI, connectTimeoutMS=30000, socketTimeoutMS=None)
        client.admin.command('ping')
        return client
    except Exception as e:
        st.error(f"🔌 Erreur de connexion MongoDB: {str(e)}")
        st.stop()

def sauvegarder_dataframe_csv(df, chemin):
    df.to_csv(chemin, index=False, encoding='utf-8-sig')
    st.info(f"📦 CSV mis à jour : {chemin}")

def charger_ou_creer_dataframe():
    """Charge le CSV s'il existe et n'est pas vide, sinon récupère depuis MongoDB et crée le CSV"""
    if os.path.exists(CSV_PATH) and os.path.getsize(CSV_PATH) > 0:
        st.info("💾 Données chargées depuis le cache CSV.")
        return pd.read_csv(CSV_PATH)
    else:
        st.warning("📄 Pas de cache valide, récupération depuis MongoDB…")
        client = get_mongo_client()
        db = client[MONGO_DB]
        docs = list(db[COLLECTION_NAME].find())
        if docs:
            df = pd.json_normalize(docs)
            if '_id' in df.columns:
                df['_id'] = df['_id'].astype(str)
            sauvegarder_dataframe_csv(df, CSV_PATH)
            return df
        else:
            st.error("Aucun document trouvé dans MongoDB.")
            st.stop()

def main():
    df = charger_ou_creer_dataframe()

    st.header("Liste des Produits")
    st.dataframe(df)

    if st.button("🔄 Réindexer par 'sku'"):
        if 'sku' in df.columns:
            df = df.set_index('sku').reset_index()  # exemple de réindex
            sauvegarder_dataframe_csv(df, CSV_PATH)
            st.success("✅ Données réindexées et CSV mis à jour.")
        else:
            st.warning("Colonne 'sku' absente.")

if __name__ == "__main__":
    main()
