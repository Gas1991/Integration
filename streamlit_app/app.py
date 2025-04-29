def main():
    if not os.path.exists(IMAGES_DIR):
        os.makedirs(IMAGES_DIR)
        st.warning(f"Dossier images créé: {IMAGES_DIR}")

    # Contrôle de cache et bouton de mise à jour
    use_cache = os.path.exists(CACHE_FILE)

    if 'df' not in st.session_state:
        if use_cache:
            df = load_cache()
            st.session_state.df = df
            st.success("✅ Cache produit chargé depuis le fichier CSV.")
        else:
            st.info("📦 Pas de cache trouvé, chargement depuis MongoDB.")
            df = load_data_from_mongo()
            save_cache(df)
            st.session_state.df = df

    if st.button("🔄 Recharger depuis MongoDB (forcer MAJ cache)"):
        df = load_data_from_mongo()
        save_cache(df)
        st.session_state.df = df
        st.success("✅ Cache mis à jour avec succès.")

    df = st.session_state.df

    tab1, tab2 = st.tabs(["Produits", "Images"])

    with tab1:
        st.header("Liste des Produits")

        if not df.empty:
            columns_to_show = [
                'sku', 'title', 'page_type', 'description_meta', 'product_overview', 'savoir_plus_text', 'image_url'
            ]
            existing_columns = [col for col in columns_to_show if col in df.columns]
            df_filtered = df[existing_columns]

            search_term = st.text_input("Rechercher", "")
            if search_term:
                df_filtered = df_filtered[df_filtered.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)]

            st.dataframe(df_filtered, height=600, use_container_width=True)

            if 'special_price' in df.columns:
                st.metric("Moyenne des prix", f"{df['special_price'].mean():.2f} DT")
        else:
            st.warning("Aucun produit disponible.")

    with tab2:
        st.header("Gestion des Images")

        image_option = st.radio("Source", ["Local", "GridFS"])

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
                st.error(f"Erreur images locales: {str(e)}")

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
                    st.warning("Aucun fichier dans GridFS")
            except Exception as e:
                st.error(f"Erreur GridFS: {str(e)}")
