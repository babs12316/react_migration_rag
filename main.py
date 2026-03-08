from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_classic.storage import LocalFileStore, create_kv_docstore
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_classic.retrievers import ParentDocumentRetriever
from langchain_community.document_loaders import TextLoader

embeddings = OllamaEmbeddings(model="nomic-embed-text")

vectorstore = Chroma(
    collection_name="react_migration_local",
    embedding_function=embeddings,
    persist_directory="./chroma_db"
)

root_path = Path.cwd() / "parent_docs_data"
root_path.mkdir(exist_ok=True)
fs = LocalFileStore(root_path)
store = create_kv_docstore(fs)

parent_splitter = RecursiveCharacterTextSplitter(chunk_size=1000)
child_splitter = RecursiveCharacterTextSplitter(chunk_size=200)

retriever = ParentDocumentRetriever(
    vectorstore=vectorstore,
    docstore=store,
    child_splitter=child_splitter,
    parent_splitter=parent_splitter
)

print(f"🚀 Storage Engine Live at: {root_path}")


def add_react_19_docs():
    # Load and store it
    loader = TextLoader("./data/react_19_upgrade.txt")
    docs = loader.load()
    retriever.add_documents(docs)
    print("✅ Memory Populated with React 19 Rules")


def get_docs():
    docs = retriever.invoke("how to fix forwardRef in React 19")
    print(f"docs returned: {docs}")


if __name__ == "__main__":
    add_react_19_docs()
    get_docs()
