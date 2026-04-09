
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
import httpx
from config import (
    GROQ_API_KEY, GROQ_API_URL, GROQ_MODEL,
    VECTOR_STORE_PATH, EMBEDDING_MODEL,
    CHUNK_SIZE, CHUNK_OVERLAP, TOP_K_RESULTS
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )

def get_vector_store(embeddings=None) -> Chroma:
    if embeddings is None:
        embeddings = get_embeddings()
    return Chroma(persist_directory=VECTOR_STORE_PATH, embedding_function=embeddings)

def ingest_document(file_path: str, department: str, access_level: str = "internal", extra_metadata: Optional[Dict] = None) -> int:
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        loader = PyPDFLoader(str(file_path))
    elif suffix in [".txt", ".md"]:
        loader = TextLoader(str(file_path), encoding="utf-8")
    else:
        raise ValueError(f"Unsupported file type: {suffix}")
    pages = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    chunks = splitter.split_documents(pages)
    metadata = {"department": department.lower(), "access_level": access_level.lower(), "source": file_path.name}
    if extra_metadata:
        metadata.update(extra_metadata)
    for chunk in chunks:
        chunk.metadata.update(metadata)
    embeddings = get_embeddings()
    store = get_vector_store(embeddings)
    store.add_documents(chunks)
    store.persist()
    logger.info(f"Stored {len(chunks)} chunks | dept={department} | file={file_path.name}")
    return len(chunks)

def retrieve_documents(query: str, role: str, top_k: int = TOP_K_RESULTS) -> List[Document]:
    from rbac import build_chroma_filter
    chroma_filter = build_chroma_filter(role)
    logger.info(f"Searching with filter: {chroma_filter} for role='{role}'")
    store = get_vector_store()
    try:
        results = store.similarity_search(query=query, k=top_k, filter=chroma_filter)
    except Exception as e:
        logger.error(f"Search error: {e}")
        results = []
    logger.info(f"Found {len(results)} matching chunks")
    return results

def call_groq_llm(question: str, context: str) -> str:
    if not GROQ_API_KEY:
        return f"GROQ_API_KEY not set in .env file. Get a free key at https://console.groq.com\n\nRetrieved context:\n{context[:300]}..."
    system_prompt = """You are a secure enterprise AI assistant.
Answer questions ONLY using the context documents provided below.
If the context does not contain enough information, say: I don't have enough information in the accessible documents to answer this.
Never invent information. Be concise and professional."""
    user_message = f"Context documents:\n---\n{context}\n---\n\nQuestion: {question}\n\nAnswer:"
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                GROQ_API_URL,
                json={"model": GROQ_MODEL, "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_message}], "max_tokens": 1024, "temperature": 0.1},
                headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
    except httpx.HTTPStatusError as e:
        return f"LLM API error ({e.response.status_code}). Check your GROQ_API_KEY."
    except Exception as e:
        return f"Error calling LLM: {str(e)}"

def answer_question(question: str, user_role: str) -> Tuple[str, List[str]]:
    docs = retrieve_documents(question, user_role)
    if not docs:
        return ("I couldn't find any relevant information in the documents you have access to.", [])
    context_parts = []
    sources = []
    for i, doc in enumerate(docs, 1):
        src = doc.metadata.get("source", "unknown")
        dept = doc.metadata.get("department", "unknown")
        context_parts.append(f"[Document {i} | {src} | dept: {dept}]\n{doc.page_content}")
        if src not in sources:
            sources.append(src)
    context = "\n\n".join(context_parts)
    answer = call_groq_llm(question, context)
    return answer, sources