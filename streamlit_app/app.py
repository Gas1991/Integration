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

st.set_page_config(layout="wide")
st.title("📊 Produits Dashboard")

# Connect to MongoDB with retry logic to ensure the client is correctly handled
@st.cache_resource(ttl=86400)
def get_mongo_client():
    try:
        client = MongoClient(MONGO_URI, connectTimeoutMS=30000, socketTimeoutMS=None)
        client.admin.command('ping')  # Test connection
        return client
    except Exception as e:
        st.error(f"🔌 Erreur de connexion MongoDB : {str(e)}")
        st.stop()

# Load data from MongoDB and normalize to a DataFrame
@st.cache_data(ttl=86400)
def load_data_from_mongo():
    client = get_mongo_client()
    db = client[MONGO_DB]
    docs = list(db[COLLECTION_NAME].find())
    if docs:
        df = pd.json_normalize(docs)
        if '_id' in df.columns:
            df['_id'] = df['_id'].astype(str)  # Convert '_id' to string for easier handling
        return df
    else:
        return pd.DataFrame()  # Return an empty DataFrame if no data is found

# Clean the dataframe for display (handle complex types like lists or dicts)
def clean_dataframe_for_display(df):
    for col in df.columns:
        if df[col].apply(lambda x: isinstance(x, (list, dict))).any():
            df.loc[:, col] = df[col].astype(str)  # Use .loc to avoid SettingWithCopyWarning
    return df

def main():
    st.markdown(
    """
    <style>
    /* Désactiver sélection de texte partout */
    body {
        -webkit-user-select: none;
        -moz-user-select: none;
        -ms-user-select: none;
        user-select: none;
    }
    /* Masquer la toolbar Streamlit */
    [data-testid="stElementToolbar"] {
        display: none;
    }
    </style>
    <script>
    // Simple authentication logic
    var username = prompt("Enter your username:");
    var password = prompt("Enter your password:");

    // Check credentials (you can modify these)
    if (username === "admin" && password === "password") {
        alert("Login successful!");
    } else {
        alert("Incorrect username or password.");
        window.location.reload();  // Refresh the page to prompt again
    }
    </script>
    """,
    unsafe_allow_html=True
)


    # Initial loading of data or timestamp
    if 'df' not in st.session_state or 'last_update' not in st.session_state:
        st.info("📦 Chargement des produits depuis DB ...")
        df = load_data_from_mongo()  # Load data
        st.session_state.df = df
        st.session_state.last_update = datetime.now()
        st.success("✅ Données chargées et mises en cache.")

    st.caption(f"🕒 Dernière mise à jour : {st.session_state.last_update.strftime('%d/%m/%Y %H:%M:%S')}")

    # Force data reload if the user clicks the update button
    if st.button("🔄 Forcer mise à jour des données DB"):
        load_data_from_mongo.clear()  # Clear the cache
        df = load_data_from_mongo()  # Reload data
        st.session_state.df = df
        st.session_state.last_update = datetime.now()
        st.success("✅ Cache actualisé et données rechargées.")

    df = st.session_state.df  # Access data from session state

    tab1 = st.tabs(["📑 Produits"])[0]  # Remove image tab handling (not needed here)

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
                # Optimized search
                combined_text = df_filtered.astype(str).agg(' '.join, axis=1)
                mask = combined_text.str.contains(search_term, case=False, na=False)
                df_filtered = df_filtered[mask]

            df_filtered = clean_dataframe_for_display(df_filtered)
            st.dataframe(df_filtered, height=600, use_container_width=True)

        else:
            st.warning("Aucun produit disponible.")

if __name__ == "__main__":
    main()
