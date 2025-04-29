import streamlit as st
from pymongo import MongoClient
import pandas as pd
import os
from datetime import datetime
from urllib.parse import quote_plus

# Configuration MongoDB
username = quote_plus('ghassengharbi191')
password = quote_plus('RLQuuAeyYH8n3icB')
MONGO_URI = f'mongodb+srv://{username}:{password}@cluster0.wrzdaw1.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
MONGO_DB = 'Mytek_database'
COLLECTION_NAME = 'Produits_mytek'

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

CSV_PATH = os.path.join(CACHE_DIR, "produits_cache.csv")
INFO_PATH = os.path.join(CACHE_DIR, "cache_info.txt")

st.set_page_config(layout="wide")
st.title("Mytek Produits Dashboard")

@st.cache_resource(ttl=3600)
def get_mongo_client():
    client = MongoClient(MONGO_URI)
    client.admin.command('ping')
    return client

def sauvegarder_dataframe_csv(df, chemin):
    df.to_csv(chemin, index=False, encoding='utf-8-sig')

def lire_cache_info():
    """Lit le fichier info contenant le nombre de documents et date"""
    if os.path.exists(INFO_PATH):
        with open(INFO_PATH, 'r') as f:
            lignes = f.readlines()
            count = int(lignes[0].strip())
            last_update = lignes[1].strip()
            return count, last_update
    return 0, None

def sauvegarder_cache_info(count):
    """Enregistre le nombre de documents et date dans le fichier info"""
    with open(INFO_PATH, 'w') as f:
        f.write(f"{count}\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def charger_dataframe_depuis_csv():
    if os.path.exists(CSV_PATH) and os.path.getsize(CSV_PATH) > 0:
        return pd.read_csv(CSV_PATH)
    else:
        return None

def mettre_a_jour_csv_si_necessaire(db):
    """Compare MongoDB et CSV et met à jour si nécessaire"""
    current_count = db[COLLECTION_NAME].count_documents({})
    cached_count, last_update = lire_cache_info()

    if current_count != cached_count:
        st.warning("📊 Modification détectée dans la base MongoDB : mise à jour du CSV.")
        docs = list(db[COLLECTION_NAME].find())

        if docs:
            df = pd.json_normalize(docs)
            if '_id' in df.columns:
                df['_id'] = df['_id'].astype(str)

            sauvegarder_dataframe_csv(df, CSV_PATH)
            sauvegarder_cache_info(current_count)
            return df, True
        else:
            st.error("La collection est vide.")
            return None, False
    else:
        st.success(f"✅ Cache à jour (dernière mise à jour : {last_update})")
        df = charger_dataframe_depuis_csv()
        return df, False

def main():
    client = get_mongo_client()
    db = client[MONGO_DB]

    df, updated = mettre_a_jour_csv_si_necessaire(db)

    if df is not None:
        st.dataframe(df, height=600, use_container_width=True)
    else:
        st.warning("Aucune donnée disponible.")

if __name__ == "__main__":
    main()
