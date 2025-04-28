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

# Initialisation Streamlit
st.set_page_config(layout="wide")
st.title("Mytek Produits Dashboard")

@st.cache_resource(ttl=3600)
def get_mongo_client():
    """Crée une connexion MongoDB sécurisée"""
    try:
        client = MongoClient(MONGO_URI, connectTimeoutMS=30000, socketTimeoutMS=None)
        client.admin.command('ping')  # Test de connexion
        return client
    except Exception as e:
        st.error(f"🔌 Erreur de connexion MongoDB: {str(e)}")
        st.stop()

def main():
    # Vérification du dossier images
    if not os.path.exists(IMAGES_DIR):
        os.makedirs(IMAGES_DIR)
        st.warning(f"Dossier images créé: {IMAGES_DIR}")

    client = get_mongo_client()
    db = client[MONGO_DB]

    # Tabs interface
    tab1, tab2 = st.tabs(["Produits", "Images"])

    with tab1:
        st.header("Liste des Produits")
        
        # Add filter options in sidebar
        with st.sidebar:
            st.header("Filtres")
            # Filter by page_type (default to product_page)
            page_type_filter = st.selectbox(
                "Type de page",
                options=["product_page", "all"],
                index=0,
                help="Filtrer par type de page"
            )
            
            # Price range filter
            price_range = st.slider(
                "Plage de prix (DT)",
                min_value=0,
                max_value=10000,
                value=(0, 5000),
                step=50
            )
            
            # Availability filter
            availability_filter = st.checkbox(
                "Afficher seulement les produits en stock",
                value=False
            )
        
        try:
            # Build query based on filters
            query = {}
            
            # Apply page_type filter
            if page_type_filter != "all":
                query["page_type"] = page_type_filter
            
            # Apply price range filter
            if 'special_price' in db[COLLECTION_NAME].find_one({}, {'special_price': 1}):
                query["special_price"] = {"$gte": price_range[0], "$lte": price_range[1]}
            
            # Apply availability filter
            if availability_filter:
                query["availability"] = {"$ne": "Out of stock"}
            
            # Execute query with projection to improve performance
            projection = {
                'sku': 1,
                'title': 1,
                'page_type': 1,
                'description_meta': 1,
                'product_overview': 1,
                'description_marque_categorie': 1,
                'image_url': 1,
                'savoir_plus_text': 1,
                'local_image_path': 1,
                'special_price': 1,
                'availability': 1,
                '_id': 1
            }
            
            docs = list(db[COLLECTION_NAME].find(query, projection))
            
            if docs:
                df = pd.json_normalize(docs)
                if '_id' in df.columns:
                    df['_id'] = df['_id'].astype(str)

                # Default columns to show
                default_columns = [
                    'sku', 'title', 'page_type', 'description_meta', 'product_overview',
                        'image_url', 'savoir_plus_text','local_image_path',
                ]
                
                # Let user select which columns to display
                selected_columns = st.multiselect(
                    "Colonnes à afficher",
                    options=default_columns,
                    default=default_columns[:8]  # Show first 8 by default
                )
                
                # Filter dataframe based on selected columns
                df_filtered = df[selected_columns] if selected_columns else df[default_columns]
                
                # Search functionality
                search_term = st.text_input("Rechercher dans tous les champs", "")
                if search_term:
                    df_filtered = df_filtered[
                        df_filtered.apply(lambda row: row.astype(str).str.contains(
                            search_term, case=False, regex=False
                        ).any(axis=1)
                    ]
                
                # Display dataframe with improved styling
                st.dataframe(
                    df_filtered,
                    height=600,
                    use_container_width=True,
                    column_config={
                        "image_url": st.column_config.ImageColumn("Image Preview"),
                        "special_price": st.column_config.NumberColumn(
                            "Prix (DT)",
                            format="%.2f DT"
                        )
                    }
                )

                # Display statistics
                col1, col2, col3 = st.columns(3)
                if 'special_price' in df.columns:
                    with col1:
                        st.metric(
                            "Prix moyen",
                            f"{df['special_price'].mean():.2f} DT",
                            help="Prix moyen des produits filtrés"
                        )
                    with col2:
                        st.metric(
                            "Prix minimum",
                            f"{df['special_price'].min():.2f} DT",
                            help="Prix le plus bas parmi les produits filtrés"
                        )
                    with col3:
                        st.metric(
                            "Prix maximum",
                            f"{df['special_price'].max():.2f} DT",
                            help="Prix le plus élevé parmi les produits filtrés"
                        )
                
                # Show record count
                st.caption(f"Nombre de produits trouvés: {len(df_filtered)}")
            else:
                st.warning("Aucun document trouvé avec les filtres actuels!")

        except Exception as e:
            st.error(f"Erreur MongoDB: {str(e)}")

    with tab2:
        st.header("Gestion des Images")
        
        # Add pagination controls
        items_per_page = st.selectbox("Images par page", [10, 20, 50], index=0)
        page_number = st.number_input("Numéro de page", min_value=1, value=1)

        image_option = st.radio("Source", ["Local", "GridFS"])

        if image_option == "Local":
            try:
                images = [f for f in os.listdir(IMAGES_DIR) if f.lower().endswith(('.jpg', '.png'))]
                if images:
                    # Paginate images
                    start_idx = (page_number - 1) * items_per_page
                    end_idx = start_idx + items_per_page
                    paginated_images = images[start_idx:end_idx]
                    
                    cols = st.columns(3)  # Display 3 images per row
                    for i, img_file in enumerate(paginated_images):
                        with cols[i % 3]:
                            img_path = os.path.join(IMAGES_DIR, img_file)
                            try:
                                st.image(img_path, caption=img_file, use_column_width=True)
                            except Exception as e:
                                st.error(f"Erreur de chargement de l'image {img_file}: {str(e)}")
                    
                    # Show pagination info
                    st.write(f"Affichage des images {start_idx + 1}-{min(end_idx, len(images))} sur {len(images)}")
                else:
                    st.warning("Aucune image disponible dans le dossier local.")
            except Exception as e:
                st.error(f"Erreur images locales: {str(e)}")

        else:
            try:
                fs = gridfs.GridFS(db)
                files = list(fs.find())
                if files:
                    # Paginate GridFS files
                    start_idx = (page_number - 1) * items_per_page
                    end_idx = start_idx + items_per_page
                    paginated_files = files[start_idx:end_idx]
                    
                    cols = st.columns(3)  # Display 3 images per row
                    for i, file_data in enumerate(paginated_files):
                        with cols[i % 3]:
                            try:
                                st.image(file_data.read(), caption=file_data.filename, use_column_width=True)
                            except Exception as e:
                                st.error(f"Erreur de chargement de l'image {file_data.filename}: {str(e)}")
                    
                    # Show pagination info
                    st.write(f"Affichage des images {start_idx + 1}-{min(end_idx, len(files))} sur {len(files)}")
                else:
                    st.warning("Aucun fichier dans GridFS")
            except Exception as e:
                st.error(f"Erreur GridFS: {str(e)}")

if __name__ == "__main__":
    main()
