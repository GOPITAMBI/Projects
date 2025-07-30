# app.py
import os
import asyncio
import streamlit as st
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader

# --- Load environment variables ---
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# --- Ensure asyncio loop is ready ---
try:
    asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

# --- Initialize LLM model ---
def get_model():
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=API_KEY,
        temperature=0.2
    )

# --- Build RAG pipeline from PDF ---
def process_pdf(file_path):
    loader = PyPDFLoader(file_path)
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50,
        separators=["\n\n", "\n", " "]
    )
    chunks = splitter.split_documents(documents)

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=API_KEY,
    )

    vector_store = Chroma.from_documents(documents=chunks, embedding=embeddings)
    retriever = vector_store.as_retriever(search_kwargs={"k": 8})

    model = get_model()

    rag = RetrievalQA.from_chain_type(
        llm=model,
        retriever=retriever,
        return_source_documents=True
    )

    return rag

# --- Streamlit App UI ---
st.set_page_config(page_title="PDF Chat with Gemini", layout="centered")
st.title("Ask Questions from Your PDF")

uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

# Store the RAG chain in session
if uploaded_file is not None:
    with st.spinner("Processing PDF..."):
        temp_path = "temp_uploaded.pdf"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        try:
            rag_chain = process_pdf(temp_path)
            st.session_state["rag"] = rag_chain
            st.success("PDF processed and ready for Q&A!")
        finally:
            os.remove(temp_path)

# Ask questions
if "rag" in st.session_state:
    user_query = st.text_input("Ask a question about the PDF:")
    if user_query:
        with st.spinner("Generating answer..."):
            result = st.session_state["rag"]({"query": user_query})
            st.subheader("🧠 Answer")
            st.write(result["result"])

            with st.expander("📄 Source Document(s)"):
                for i, doc in enumerate(result["source_documents"], 1):
                    st.markdown(f"**Source {i}:**")
                    st.write(doc.page_content)
