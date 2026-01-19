from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from PyPDF2 import PdfReader
import nltk
from nltk.tokenize import sent_tokenize

nltk.download('punkt')

# ---------------- LOAD RAG ----------------
def load_rag():
    loader = PyPDFLoader("data/medical.pdf")
    documents = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    docs = splitter.split_documents(documents)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    db = FAISS.from_documents(docs, embeddings)
    return db

# ---------------- LOAD PDF TEXT ----------------
reader = PdfReader("data/medical.pdf")
full_text = ""
for page in reader.pages:
    full_text += page.extract_text() + " "

# ---------------- TEXT SIMPLIFIER ----------------
def simplify_text(text, num_sentences=2):
    """Return 2–3 short sentences from long medical text."""
    sentences = sent_tokenize(text)
    return " ".join(sentences[:num_sentences]).strip()

# ---------------- SYMPTOM CHECKER ----------------
def get_disease_with_explanation(symptoms, rag_db=None):
    """
    Returns a dict { disease_name: combined_simplified_explanation }
    Combines multiple symptom info for the same disease.
    """
    text_lower = full_text.lower()
    results = {}

    for symptom in symptoms:
        symptom_lower = symptom.lower()
        sentences = [s for s in text_lower.split(".") if symptom_lower in s]

        for s in sentences:
            diseases = []
            if "may cause" in s:
                parts = s.split("may cause")
                diseases = [d.strip().title() for d in parts[1].replace(".", "").split(",")]
            elif ":" in s:
                parts = s.split(":")
                diseases = [d.strip().title() for d in parts[1].replace(".", "").split(",")]

            for d in diseases:
                simple_explanation = simplify_text(s)
                simple_explanation = simple_explanation.replace(symptom_lower, symptom.title())

                if d in results:
                    # Combine explanations for same disease
                    if simple_explanation not in results[d]:
                        results[d] += " " + simple_explanation
                else:
                    results[d] = simple_explanation

    if not results:
        results["No exact match found"] = "Consult a doctor for accurate diagnosis."

    return results
