import os
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

PDF_PATH = "car_database.pdf"
VECTORSTORE_PATH = "vectorstore/db_faiss"


class RAGProcessor:
    def __init__(self):
        # Używamy modelu open-source do tworzenia embeddingów
        # **POPRAWKA:** Dodajemy 'model_kwargs', aby jawnie ustawić urządzenie na 'cpu'
        # i uniknąć błędu "NotImplementedError: Cannot copy out of meta tensor".
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        self.vector_store = None
        if os.path.exists(VECTORSTORE_PATH):
            self.load_vector_store()

    def create_vector_store(self):
        """Wczytuje PDF, dzieli na fragmenty i tworzy bazę wektorową."""
        print("Tworzenie bazy wektorowej z pliku PDF...")
        loader = PyPDFLoader(PDF_PATH)
        documents = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        docs = text_splitter.split_documents(documents)

        self.vector_store = FAISS.from_documents(docs, self.embeddings)
        self.vector_store.save_local(VECTORSTORE_PATH)
        print("Baza wektorowa została utworzona i zapisana.")

    def load_vector_store(self):
        """Ładuje istniejącą bazę wektorową."""
        self.vector_store = FAISS.load_local(VECTORSTORE_PATH, self.embeddings, allow_dangerous_deserialization=True)
        print("Baza wektorowa załadowana.")

    def find_relevant_context(self, query: str, k: int = 20) -> str:
        """Wyszukuje relevantne fragmenty tekstu dla danego zapytania."""
        if not self.vector_store:
            print("Baza wektorowa nie jest załadowana. Utwórz ją najpierw.")
            return ""

        retriever = self.vector_store.as_retriever(search_kwargs={"k": k})
        docs = retriever.invoke(query)

        # Formatowanie kontekstu do wstawienia w prompt
        context = "\n\n---\n\n".join([doc.page_content for doc in docs])
        return context

# Aby zainicjować bazę, uruchom ten plik lub wywołaj z shella:
# from fleet.services.rag_processor import RAGProcessor
# processor = RAGProcessor()
# processor.create_vector_store()
