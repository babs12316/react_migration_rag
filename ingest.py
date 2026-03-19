# ingest.py
# Run once: python ingest.py
# Scrapes React 19 upgrade guide, chunks it, embeds with Ollama, stores in ChromaDB

import os
import requests
from bs4 import BeautifulSoup
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
REACT_19_URL = "https://react.dev/blog/2024/04/25/react-19-upgrade-guide"
CHROMA_DIR = "api/chroma_db"
COLLECTION = "react19_docs"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def scrape_docs(url: str) -> str:
    """Scrape React 19 upgrade guide from react.dev."""
    print(f"Scraping {url}...")
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # react.dev puts content in <main> tag
    main = soup.find("main")
    if not main:
        raise ValueError("Could not find main content on page")

    # extract text, remove excessive whitespace
    text = main.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def chunk_text(text: str) -> list[str]:
    """Split text into overlapping chunks for better retrieval."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", " ", ""]
    )
    return splitter.split_text(text)


def ingest():
    # ── 1. Scrape ──
    raw_text = scrape_docs(REACT_19_URL)
    print(f"Scraped {len(raw_text)} characters")

    # ── 2. Save raw text for reference ──
    os.makedirs("api/data", exist_ok=True)
    with open("api/data/react_19_docs.txt", "w") as f:
        f.write(raw_text)
    print("Saved to data/react_19_docs.txt")

    # ── 3. Chunk ──
    chunks = chunk_text(raw_text)
    print(f"Split into {len(chunks)} chunks")

    # ── 4. Embed + store in ChromaDB ──
    print("Embedding with Ollama nomic-embed-text...")
    embeddings = HuggingFaceEmbeddings()

    Chroma.from_texts(
        texts=chunks,
        embedding=embeddings,
        collection_name=COLLECTION,
        persist_directory=CHROMA_DIR,
    )

    print(f"Stored {len(chunks)} chunks in ChromaDB at {CHROMA_DIR}")
    print("Ingestion complete.")


if __name__ == "__main__":
    ingest()
