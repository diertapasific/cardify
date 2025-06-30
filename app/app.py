import streamlit as st
import tempfile
import os
from utils import extract_text_per_chunk
from model import ask_model

st.set_page_config(page_title="Flashcard Generator", layout="wide")
st.title("🔹 Flashcard Generator from PDF")

uploaded_file = st.file_uploader("Upload your PDF file", type="pdf")

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_path = tmp_file.name

    st.success("PDF uploaded successfully.")
    chunks = extract_text_per_chunk(tmp_path, pages_per_chunk=10)

    st.info(f"Total chunks: {len(chunks)}. Generating notes...")

    all_points = []
    for i, chunk in enumerate(chunks):
        with st.spinner(f"Processing chunk {i+1}..."):
            prompt = f"""
            Ambil 3–5 poin penting dari teks berikut ini. Gunakan format poin bullet:

            {chunk[:3000]}
            """
            result = ask_model(prompt)
            all_points.append(result)

    combined = "\n".join(all_points)

    with st.spinner("Generating flashcards..."):
        card_prompt = f"""
        Buat 30 flashcards dalam format Q&A berdasarkan poin-poin penting berikut:

        {combined}

        Gunakan format Markdown seperti ini:

        Card 1

        **Question**  
        Apa itu X?

        **Answer**  
        X adalah ...
        """
        cards = ask_model(card_prompt)

    st.subheader("📖 Flashcards")
    for card in cards.split("Card ")[1:]:
        st.markdown(f"### Card {card[:card.find('\n')]}")
        st.markdown(card[card.find('\n')+1:])

    st.download_button("Download Flashcards", cards, file_name="flashcards.md", mime="text/markdown")
