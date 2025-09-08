from itertools import chain
from pathlib import Path

from google.ai.generativelanguage_v1beta import TaskType
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from envs import Env


DOCUMENTS_PATH = Path("../documents")
DB_PATH = Path(".db")


def load_and_split_pdf(path: Path) -> list[Document]:
    """load and chunk pdfs"""
    loader = PyPDFLoader(str(path))
    pdf = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    return splitter.split_documents(pdf)


def main():
    pdf_dir = Path("../documents")
    if not pdf_dir.exists():
        print("documents dir doesnt exist")
        exit()

    env = Env()
    assert env.google_api_key is not None
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=env.google_api_key,
        task_type=TaskType.RETRIEVAL_DOCUMENT.name.lower(),
        client_options={"output_dimensionality": 768},
    )
    paths = list(DOCUMENTS_PATH.rglob("*.pdf"))
    split_documents = [load_and_split_pdf(path) for path in paths[:10]]
    documents: list[Document] = list(chain(*split_documents))

    db = Chroma.from_documents(
        documents, embeddings=embeddings, persist_directory=DB_PATH.as_posix()
    )

    answer = qa.run("Was sagt das österreichische Recht zum Datenschutz?")
    print(answer)


if __name__ == "__main__":
    main()
