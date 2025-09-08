import hashlib
from itertools import chain
from functools import cache
from pathlib import Path
from typing import Any

from google.ai.generativelanguage_v1beta import TaskType
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from loguru import logger

from envs import Env, SECRETS_DIR


DOCUMENTS_PATH = Path("../documents")
DB_PATH = Path(".db")
SCRIPTS_PATH = Path("../scripts")
NDIMS = 768


class GoogleGenerativeAIEmbeddingsNDims(GoogleGenerativeAIEmbeddings):
    def embed_documents(self, texts, *args, **kwargs) -> list[list[float]]:
        return super().embed_documents(
            texts, *args, **kwargs, output_dimensionality=NDIMS
        )

    def embed_query(self, text, *args, **kwargs) -> list[float]:
        return super().embed_query(text, *args, **kwargs, output_dimensionality=NDIMS)


def load_and_split_pdf(path: Path) -> list[Document]:
    """load and chunk pdfs"""
    loader = PyPDFLoader(path.as_posix())
    pdf = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    return splitter.split_documents(pdf)


def calculate_content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@cache
def get_hashes(db: Chroma) -> set[str]:
    metadatas = db.get(include=["metadatas"])["metadatas"]
    return {m["content_hash"] for m in metadatas}


def is_unique(db: Chroma, doc: Document) -> bool:
    return doc.metadata["content_hash"] not in get_hashes(db)


def get_embedding_model() -> GoogleGenerativeAIEmbeddings:
    return GoogleGenerativeAIEmbeddingsNDims(
        model="models/embedding-001",
        google_api_key=Env().google_api_key,
        task_type=TaskType.RETRIEVAL_DOCUMENT.name.lower(),
        transport="rest",
    )


def get_db() -> Chroma:
    return Chroma(
        embedding_function=get_embedding_model(), persist_directory=DB_PATH.as_posix()
    )


def embed_documents():
    if not DOCUMENTS_PATH.exists():
        logger.error(f"Scrape documents with {SCRIPTS_PATH / 'find_documents.py'}")
        exit()

    if Env().google_api_key is None:
        logger.error(f"Create a file '{SECRETS_DIR}/google_api_key' with your api key")
        exit()
    paths = list(DOCUMENTS_PATH.rglob("*.pdf"))
    if len(paths) == 0:
        logger.error(
            f"No documents found... scrape documents with {SCRIPTS_PATH / 'find_documents.py'}"
        )
        exit()
    split_documents = [load_and_split_pdf(path) for path in paths[:20]]
    documents: list[Document] = list(chain(*split_documents))
    for doc in documents:
        doc.metadata["content_hash"] = calculate_content_hash(doc.page_content)

    db = get_db()
    unique_documents = [doc for doc in documents if is_unique(db, doc)]
    if len(unique_documents) > 0:
        db.add_documents(documents=unique_documents)
    else:
        logger.info("No new documents to add.")
    existing: dict[str, Any] = db.get(include=["metadatas", "documents"])
    texts = existing["documents"]
    logger.info(f"n_docs: {len(texts)}")


if __name__ == "__main__":
    embed_documents()
