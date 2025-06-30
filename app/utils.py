from pypdf import PdfReader

def extract_text_per_chunk(pdf_path, pages_per_chunk=10):
    reader = PdfReader(pdf_path)
    all_chunks = []
    for i in range(0, len(reader.pages), pages_per_chunk):
        chunk = ""
        for j in range(i, min(i + pages_per_chunk, len(reader.pages))):
            chunk += reader.pages[j].extract_text() or ""
        all_chunks.append(chunk.strip())
    return all_chunks