from functools import partial
from pathlib import Path

from google.ai.generativelanguage_v1beta import TaskType
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from envs import Env


# 2. PDF loading & chunking
def load_and_split_pdf(path: Path) -> list[Document]:
    loader = PyPDFLoader(str(path))
    pdf = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    return splitter.split_documents(pdf)


# # 3. Build vector store with embeddings
# def create_vectorstore(docs, persist_dir="chroma_store", dim=768):
#     embedder = GeminiEmbeddings(output_dimension=dim)
#     vectordb = Chroma.from_documents(docs, embedder, persist_directory=persist_dir)
#     return vectordb
#
#
# # 4. Local LLM (choose a model that fits your GPU)
# def load_local_llm():
#     model_id = "google/flan-t5-base"  # light, but decent performance
#     tokenizer = AutoTokenizer.from_pretrained(model_id)
#     model = AutoModelForCausalLM.from_pretrained(
#         model_id, device_map="auto", torch_dtype="auto"
#     )
#     pipe = pipeline(
#         "text-generation", model=model, tokenizer=tokenizer, max_new_tokens=256
#     )
#     return HuggingFacePipeline(pipeline=pipe)
#
#
# # 5. Build QA chain
# def build_qa_chain(vectordb, llm):
#     retriever = vectordb.as_retriever(search_kwargs={"k": 4})
#     return RetrievalQA.from_chain_type(llm=llm, retriever=retriever)
#
#


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

    # config={"output_dimensionality": self.output_dim},
    docs = load_and_split_pdfs(pdf_dir)

    vectordb = create_vectorstore(docs, persist_dir="chroma_gemini", dim=768)

    llm = load_local_llm()
    qa = build_qa_chain(vectordb, llm)

    answer = qa.run("Was sagt das österreichische Recht zum Datenschutz?")
    print(answer)


if __name__ == "__main__":
    main()
