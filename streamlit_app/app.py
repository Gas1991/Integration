import streamlit as st
import pandas as pd
import os
from pymongo import MongoClient

# Constantes
CACHE_FILE = "data_cache.csv"
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "your_database"
COLLECTION_NAME = "your_collection"

# Connexion MongoDB
def get_mongo_collection():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    return db[COLLECTION_NAME]

# Charger les données depuis MongoDB
def load_data_from_mongo():
    collection = get_mongo_collection()
    data = list(collection.find())
    if data:
        df = pd.DataFrame(data)
        return df
    else:
        st.error("Aucune donnée trouvée dans la base MongoDB.")
        return pd.DataFrame()

# Sauvegarder le cache
def save_cache(df):
    df.to_csv(CACHE_FILE, index=False)

# Charger le cache avec gestion d'erreurs
def load_cache():
    if os.path.exists(CACHE_FILE):
        if os.path.getsize(CACHE_FILE) > 0:
            try:
                return pd.read_csv(CACHE_FILE)
            except pd.errors.EmptyDataError:
                st.warning("⚠️ Le fichier cache est vide ou corrompu, chargement depuis MongoDB.")
                df = load_data_from_mongo()
                save_cache(df)
                return df
        else:
            st.warning("⚠️ Le cache est vide, chargement depuis MongoDB.")
            df = load_data_from_mongo()
            save_cache(df)
            return df
    else:
        st.warning("📂 Pas de fichier cache trouvé, chargement depuis MongoDB.")
        df = load_data_from_mongo()
        save_cache(df)
        return df

# Fonction principale Streamlit
def main():
    st.title("📊 Application Streamlit avec cache CSV et MongoDB")

    # Chargement des données
    df = load_cache()

    # Affichage des données
    if not df.empty:
        st.subheader("✅ Données chargées")
        st.dataframe(df)
    else:
        st.error("❌ Impossible de charger des données.")

    # Bouton pour forcer rechargement depuis MongoDB
    if st.button("🔄 Recharger depuis MongoDB"):
        df = load_data_from_mongo()
        if not df.empty:
            save_cache(df)
            st.success("Cache mis à jour.")
            st.experimental_rerun()
        else:
            st.error("Aucune donnée disponible dans MongoDB.")

if __name__ == "__main__":
    main()
