import os
import streamlit as st
import pandas as pd
from langchain.docstore.document import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate

CSV_DIR = "csv_files"
VECTOR_DB_DIR = "faiss_csv_index"

# 1. Read and convert CSV rows into LangChain Documents (row-based chunking)
def load_csv_documents(csv_dir):
    documents = []
    for filename in os.listdir(csv_dir):
        if filename.endswith(".csv"):
            path = os.path.join(csv_dir, filename)
            df = pd.read_csv(path)
            library_name = filename.replace("_methods.csv", "").lower()
            for idx, row in df.iterrows():
                if "Method" in df.columns and "Description" in df.columns:
                    method = str(row["Method"]).strip()
                    description = str(row["Description"]).strip()
                    content = f"Method: {method}\nDescription: {description}"
                    metadata = {
                        "source": filename,
                        "method": method.lower(),
                        "library": library_name,
                        "row_index": idx
                    }
                else:
                    content = " | ".join(str(x) for x in row.values)
                    metadata = {"source": filename, "library": library_name, "row_index": idx}
                documents.append(Document(page_content=content, metadata=metadata))
            print(f"✅ Successfully indexed: {filename}")
    return documents

# 2. Vector store
def create_csv_vectorstore(documents, api_key):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=api_key)
    texts = [doc.page_content for doc in documents]
    metadatas = [doc.metadata for doc in documents]
    db = FAISS.from_texts(texts, embedding=embeddings, metadatas=metadatas)
    db.save_local(VECTOR_DB_DIR)
    return db

# 3. Load QA Chain
def get_chain(api_key):
    prompt_template = """
    Use the CSV context to answer the question. If the answer is not found, say "Answer not available in context."

    Context:
    {context}

    Question:
    {question}

    Answer:
    """
    model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.2, google_api_key=api_key)
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    return load_qa_chain(model, chain_type="stuff", prompt=prompt)

# 4. Streamlit App
def main():
    st.set_page_config("CSV Q&A Chat")
    st.title("Chat with Your CSV Files")

    api_key = st.sidebar.text_input("Enter Google API Key", type="password")
    if not api_key:
        st.warning("Please enter your Google API key.")
        return

    # Build vector DB if not already present
    if not os.path.exists(VECTOR_DB_DIR):
        st.info("Reading CSV files and building vector DB...")
        docs = load_csv_documents(CSV_DIR)
        if not docs:
            st.error("No CSV files found in the directory.")
            return
        create_csv_vectorstore(docs, api_key)
        st.success("CSV files processed and stored!")

    # Load vector DB
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=api_key)
    db = FAISS.load_local(VECTOR_DB_DIR, embeddings, allow_dangerous_deserialization=True)

    # User Inputs
    question = st.text_input("🔍 Ask a question about your CSV files:")
    library_input = st.text_input("📚 Enter the library name (e.g., list, stack, hashmap):").strip().lower()

    if question:
        chain = get_chain(api_key)

        if library_input:
            docs = db.similarity_search(question, k=10, filter={"library": library_input})
        else:
            docs = db.similarity_search(question, k=10)

        if not docs:
            st.warning("No relevant chunks found. Try a different question or library.")
            return

        response = chain({"input_documents": docs, "question": question}, return_only_outputs=True)
        st.write("🧠 Answer:", response['output_text'])

if __name__ == "__main__":
    main()
