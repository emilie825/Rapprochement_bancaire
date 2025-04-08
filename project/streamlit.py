import streamlit as st
import pandas as pd
import os
import tempfile
import shutil
import time
import base64
from PIL import Image
import main
from io import BytesIO

# Configuration
st.set_page_config(page_title="Rapprochement Bancaire", layout="wide")
st.title("💼 Système de Rapprochement Bancaire")

# Session State
if 'results_df' not in st.session_state:
    st.session_state.results_df = None
if 'clicked_row' not in st.session_state:
    st.session_state.clicked_row = None
if 'temp_images' not in st.session_state:
    st.session_state.temp_images = {}

# CSS personnalisé
st.markdown("""
<style>
    .stSelectbox div[data-baseweb="select"] {
        margin-bottom: 20px;
    }
    .stImage img {
        border-radius: 10px;
        box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
    }
    .stDataFrame tr:hover {
        background-color: #f5f5f5;
        cursor: pointer;
    }
    .selected-row {
        background-color: #e6f7ff !important;
    }
    .stProgress > div > div > div > div {
        background-color: #1e88e5;
    }
    .stqdm > div > div > div > div {
        background-color: #1e88e5 !important;
    }
</style>
""", unsafe_allow_html=True)

def download_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return output

def safe_display_columns(df, columns):
    return df[[col for col in columns if col in df.columns]]

def save_uploaded_files(uploaded_files, save_dir, progress_callback=None):
    os.makedirs(save_dir, exist_ok=True)
    saved_files = []
    for i, uploaded_file in enumerate(uploaded_files):
        file_path = os.path.join(save_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        saved_files.append(file_path)
        if progress_callback:
            progress_callback((i + 1) / len(uploaded_files))
    return saved_files

def image_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

def display_image_from_base64(base64_str, caption):
    st.markdown(
        f'<img src="data:image/jpeg;base64,{base64_str}" width="350" style="border-radius: 10px; box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);"/>',
        unsafe_allow_html=True
    )
    st.caption(caption)

# Interface principale
tab1, tab2 = st.tabs(["Rapprochement", "Présentation de l'application"])

with tab1:
    st.header("Rapprochement Bancaire")

    col1, col2 = st.columns(2)
    with col1:
        uploaded_receipts = st.file_uploader("Factures (images)",
                                          type=["jpg", "jpeg", "png"],
                                          accept_multiple_files=True)
    with col2:
        uploaded_statements = st.file_uploader("Relevés bancaires (CSV)",
                                            type=["csv"],
                                            accept_multiple_files=True)

    if st.button("Exécuter le rapprochement", type="primary"):
        if not uploaded_receipts or not uploaded_statements:
            st.error("Veuillez uploader au moins une facture et un relevé bancaire")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            result_container = st.empty()

            try:
                # Étape 1: Initialisation (5%)
                status_text.text("Initialisation...")
                temp_dir = tempfile.mkdtemp()
                receipts_dir = os.path.join(temp_dir, "receipts")
                statements_dir = os.path.join(temp_dir, "statements")
                os.makedirs(receipts_dir, exist_ok=True)
                os.makedirs(statements_dir, exist_ok=True)
                progress_bar.progress(5)

                # Étape 2: Sauvegarde des fichiers (15%)
                def update_progress(progress):
                    progress_bar.progress(5 + int(progress * 10))
                    status_text.text(f"Sauvegarde des fichiers... {int(progress * 100)}%")

                status_text.text("Sauvegarde des factures...")
                receipt_paths = save_uploaded_files(uploaded_receipts, receipts_dir, update_progress)

                status_text.text("Sauvegarde des relevés...")
                statement_paths = save_uploaded_files(uploaded_statements, statements_dir, update_progress)
                progress_bar.progress(20)

                # Étape 3: Conversion des images (15%)
                status_text.text("Conversion des images...")
                st.session_state.temp_images = {}
                total_images = len(receipt_paths)
                for i, path in enumerate(receipt_paths):
                    img_name = os.path.basename(path)
                    st.session_state.temp_images[img_name] = image_to_base64(path)
                    progress_bar.progress(20 + int((i + 1) / total_images * 15))
                    status_text.text(f"Conversion des images... {i + 1}/{total_images}")
                progress_bar.progress(35)

                # Étape 4: Traitement principal (50%)
                status_text.text("Traitement des données...")
                output_excel = os.path.join(temp_dir, "results.xlsx")

                # Simulation de progression pour le traitement
                for i in range(1, 11):
                    time.sleep(0.3)  # À remplacer par votre traitement réel
                    progress_bar.progress(35 + int(i * 5))
                    status_text.text(f"Traitement des données... Étape {i}/10")

                # Appel réel à votre fonction de traitement
                main.process_uploads(receipts_dir, statements_dir, output_excel)
                progress_bar.progress(85)

                # Étape 5: Chargement des résultats (15%)
                status_text.text("Chargement des résultats...")
                if os.path.exists(output_excel):
                    st.session_state.results_df = pd.read_csv(output_excel)
                    st.session_state.clicked_row = None
                    progress_bar.progress(100)
                    status_text.text("")
                    result_container.success(f"Analyse terminée ({len(st.session_state.results_df)} transactions)")
                else:
                    raise FileNotFoundError("Le fichier de résultats n'a pas été généré")

            except Exception as e:
                progress_bar.progress(100)
                status_text.text("")
                result_container.error(f"Erreur lors du traitement: {str(e)}")
                if 'debug_output' in locals():
                    st.text_area("Détails de l'erreur", debug_output, height=100)
            finally:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)

    if st.session_state.results_df is not None:
        st.subheader("Résultats du rapprochement")
        st.subheader("Appuyez sur le bouton à gauche de la colonne à afficher pour voir la facture!")
        display_df = safe_display_columns(st.session_state.results_df, ['vendor', 'amount', 'currency', 'date'])

        selected_rows = st.dataframe(
            display_df,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            key="dataframe_tab1"
        )

        if hasattr(selected_rows, 'selection') and selected_rows.selection:
            selected_indices = selected_rows.selection.rows
            if selected_indices:
                st.session_state.clicked_row = selected_indices[0]

        if st.session_state.clicked_row is not None:
            row = st.session_state.results_df.iloc[st.session_state.clicked_row]
            img_name = os.path.basename(row.get('image_path', ''))
            base64_img = st.session_state.temp_images.get(img_name)

            if base64_img:
                st.divider()
                col1, col2 = st.columns([1, 2])
                with col1:
                    display_image_from_base64(base64_img, img_name)
                with col2:
                    st.subheader("Détails de la transaction")
                    st.json({
                        "Fournisseur": row.get('vendor', 'N/A'),
                        "Montant": row.get('amount', 'N/A'),
                        "Devise": row.get('currency', 'N/A'),
                        "Date": row.get('date', 'N/A')
                    })
            else:
                st.warning("Image non disponible")

        # Téléchargement du fichier Excel
        excel_file = download_excel(st.session_state.results_df)
        st.download_button(
            label="Télécharger les résultats en Excel",
            data=excel_file,
            file_name="resultats_rapprochement.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

with tab2:
    st.header("Présentation de l'Application")

    st.markdown("""
    #### Bienvenue sur notre Système de Rapprochement Bancaire !

    Cette application est conçue pour vous aider à rapprocher facilement vos factures et vos relevés bancaires. Voici un aperçu des fonctionnalités principales et comment les utiliser :

    ---

    #### **Fonctionnalités Principales :**

    1. **Rapprochement Bancaire :**
       - **Objectif :** Comparer vos factures avec vos relevés bancaires pour vérifier la concordance des transactions.
       - **Comment ça marche ?**
         1. Téléchargez vos factures (images) et vos relevés bancaires (CSV).
         2. Cliquez sur "Exécuter le rapprochement".
         3. L'application analysera les fichiers et affichera les résultats dans un tableau.
         4. **Cliquez sur la première colonne de la ligne du tableau** pour voir les détails de la facture et l'image associée.

    2. **Recherche de Factures :**
       - **Objectif :** Trouver des correspondances entre un fichier de résultats (CSV) et des images de factures.
       - **Comment ça marche ?**
         1. Téléchargez un fichier de résultats (CSV) et les images de factures correspondantes.
         2. Cliquez sur "Rechercher les factures".
         3. L'application recherchera les correspondances et affichera les résultats dans un tableau.
         4. Cliquez sur une ligne du tableau pour voir les détails de la facture et l'image associée.
         5. Vous avez un bouton en bas du tableau qui vous permet de telecharger le fichier final en excel

    ---

    #### **Pourquoi Utiliser Notre Application ?**

    - **Gain de Temps :** Automatisez le processus de rapprochement bancaire pour gagner du temps et réduire les erreurs.
    - **Simplicité :** Interface utilisateur intuitive et facile à utiliser, même pour les non-initiés.
    - **Précision :** Assurez-vous que toutes vos transactions sont correctement enregistrées et rapprochées.

    ---

    #### **Comment Commencer ?**

    1. **Préparez vos fichiers :** Assurez-vous d'avoir vos factures sous forme d'images (JPG, PNG) et vos relevés bancaires au format CSV.
    2. **Téléchargez les fichiers :** Utilisez les options de téléchargement dans les onglets appropriés.
    3. **Lancez l'analyse :** Cliquez sur les boutons d'action pour démarrer le processus de rapprochement ou de recherche.
    4. **Consultez les résultats :** Explorez les résultats dans les tableaux interactifs et visualisez les images des factures.

    """)
