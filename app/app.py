import streamlit as st
from utils import extract_text_per_chunk
from model import ask_model
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io
import re

st.set_page_config(page_title="Cardify")
st.title("🧠 Cardify")
st.subheader("AI Flashcard Generator from PDF")

uploaded_file = st.file_uploader("📤 Select and upload a PDF file to generate flashcards", type=["pdf"])
if uploaded_file:
    # Jika file baru diunggah, reset semua state yang berhubungan
    if "last_file_name" not in st.session_state or st.session_state["last_file_name"] != uploaded_file.name:
        st.session_state["last_file_name"] = uploaded_file.name
        st.session_state.pop("chunks", None)
        st.session_state.pop("flashcards", None)
        st.session_state.pop("important_points", None)
        st.session_state.pop("raw_output", None)

# Extract text once and cache in session_state
if uploaded_file and "chunks" not in st.session_state:
    with st.spinner("🔍 Extracting text from PDF..."):
        try:
            st.session_state["chunks"] = extract_text_per_chunk(uploaded_file)
        except Exception as e:
            st.error(f"❌ Failed to read PDF: {e}")

# Generate Flashcards
if st.button("🚀 Generate Flashcards"):
    if "chunks" not in st.session_state:
        st.warning("⚠️ Please upload a PDF first.")
    else:
        st.session_state["flashcards"] = []
        st.session_state["important_points"] = []
        st.session_state["raw_output"] = ""

        chunks = st.session_state["chunks"]
        progress_bar = st.progress(0, text="🤔 Analyzing content...")
        important_points = []

        for idx, chunk in enumerate(chunks):
            try:
                prompt = f"""
                Dari teks berikut, identifikasi dan ringkas poin-poin penting yang memuat informasi utama, insight bermakna, atau fakta signifikan.

                • Sajikan dalam bentuk bullet point.
                • Gunakan bahasa Indonesia yang formal, jelas, dan mudah dipahami.
                • Setiap poin harus ringkas, padat, dan tidak mengulang informasi yang sama.
                • Jangan menambahkan informasi yang tidak terdapat dalam teks.

                Teks sumber:
                \"\"\"
                {chunk[:3000]}
                \"\"\"
                """
                result = ask_model(prompt)
                important_points.append(result.strip())
            except Exception:
                continue
            progress_bar.progress((idx + 1) / len(chunks))

        progress_bar.empty()

        combined_notes = "\n".join(important_points)
        max_chars = 6000
        if len(combined_notes) > max_chars:
            combined_notes = combined_notes[:max_chars].rsplit("\n", 1)[0]  # pastikan tidak memotong di tengah baris

        st.session_state["important_points"] = important_points

        with st.spinner("📚 Generating Flashcards..."):
            flashcard_prompt = f"""
Dari teks berikut, buatlah daftar flashcard. Setiap flashcard harus berisi satu poin atau konsep kunci, diringkas dalam satu kalimat singkat dan padat.

{combined_notes}

Pisahkan setiap flashcard dengan dua baris kosong.
Jangan gunakan format tanya jawab.
Jangan sertakan awalan atau pembuka.
Pastikan setiap flashcard hanya berisi satu kalimat.
Gunakan Bahasa Indonesia.
"""
            try:
                flashcard_result = ask_model(flashcard_prompt)
                st.session_state["raw_output"] = flashcard_result

                raw_blocks = flashcard_result.strip().split("\n\n")

                flashcards = []
                for block in raw_blocks:
                    block = block.strip()

                    # Buang card yang berupa pembuka (Card 1 palsu)
                    if re.match(r'^(here|berikut|this|these)\b', block.lower()):
                        continue

                    # Ambil hanya satu kalimat pertama
                    sentence = re.split(r'[.?!]', block)[0].strip()
                    if len(sentence) > 0:
                        flashcards.append(sentence + ".")

                if not flashcards:
                    st.error("❌ Tidak ada flashcard yang valid dihasilkan.")
                else:
                    st.session_state["flashcards"] = flashcards
                    st.success(f"✅ {len(flashcards)} flashcards berhasil dibuat!")

            except Exception as e:
                st.error(f"❌ Gagal membuat flashcards: {e}")

# PDF Generator
def wrap_text(text, max_width, canvas, font_name="Helvetica", font_size=11):
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip()
        if canvas.stringWidth(test_line, font_name, font_size) <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)
    return lines

def generate_pdf(flashcards):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    left_margin = 50
    right_margin = 50
    usable_width = width - left_margin - right_margin
    y = height - 50

    for idx, card in enumerate(flashcards):
        c.setFont("Helvetica-Bold", 12)
        c.drawString(left_margin, y, f"Card {idx+1}:")
        y -= 18

        c.setFont("Helvetica", 11)
        wrapped_lines = wrap_text(card, usable_width, c)

        for line in wrapped_lines:
            c.drawString(left_margin, y, line)
            y -= 15
            if y < 80:
                c.showPage()
                y = height - 50
                c.setFont("Helvetica", 11)

        y -= 25
        if y < 80:
            c.showPage()
            y = height - 50

    c.save()
    buffer.seek(0)
    return buffer

# Display Flashcards and Download Button
if "flashcards" in st.session_state and st.session_state["flashcards"]:
    st.subheader("📥 Download Flashcards")
    pdf_data = generate_pdf(st.session_state["flashcards"])
    st.download_button(
        label="📄 Download Flashcards as PDF",
        data=pdf_data,
        file_name="flashcards.pdf",
        mime="application/pdf"
    )

    st.subheader("🗂️ Your Flashcards")
    for idx, card in enumerate(st.session_state["flashcards"]):
            st.markdown(f"""
            <div style='
                padding: 20px;
                border-radius: 10px;
                border: 1px solid #F0F2F6;
                margin-bottom: 15px;
            '>
                <strong>Card {idx+1}</strong><br><br>
                <span>{card}</span>
            </div>
            """, unsafe_allow_html=True)



