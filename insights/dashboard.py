from collections import defaultdict
from langchain_core.documents import Document
import streamlit as st

from rag import get_db


db = get_db()
st.title("PDF Search")

query = st.text_input("Enter your search query:")
search_button = st.button("Search")

if search_button and query:
    results: list[tuple[Document, float]] = db.similarity_search_with_score(query, k=10)

    if not results:
        st.write("No results found.")
    else:
        pdf_scores = defaultdict(list)
        pdf_chunks = defaultdict(list)
        for doc, score in results:
            filename = doc.metadata["source"]
            pdf_scores[filename].append(score)
            pdf_chunks[filename].append(doc.page_content)

        sorted_scores = sorted(
            pdf_scores.items(), key=lambda x: len(x[1]) * 10 + sum(x[1]), reverse=True
        )
        top3 = sorted_scores[:3]

        st.subheader("Top 3 Most Similar PDFs")
        for i, (filename, scores) in enumerate(top3, start=1):
            scores_str = ", ".join(f"{f:.2f}" for f in scores)
            chunks = pdf_chunks[filename]
            st.write(
                f"{i}. {filename.rsplit('/', 1)[1]} (matched chunks: {len(chunks)}), (scores: {scores_str})"
            )

        top_filename, top_scores = top3[0]
        top_chunks = pdf_chunks[top_filename]
        top_pdf_name = top_filename.rsplit("/", 1)[1]
        st.subheader(f"Content preview: {top_pdf_name}")
        content = "\n\n---\n\n".join(top_chunks)
        st.text_area("PDF Content", content, height=800)
