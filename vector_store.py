# vector_store.py

from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.utils import embedding_functions
from anime_docs import documents

# 1. Use new client format
chroma_client = chromadb.PersistentClient(path="./anime_vector_db")  # <- updated

# 2. Setup embedding function
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="BAAI/bge-small-en-v1.5"
)

# 3. Create or get collection
collection = chroma_client.get_or_create_collection(
    name="anime_bios",
    embedding_function=embedding_fn
)

# 4. Prepare data
texts = [doc["text"] for doc in documents]
metadatas = [{"name": doc["name"]} for doc in documents]
ids = [f"char-{i}" for i in range(len(documents))]

# 5. Add to Chroma
collection.add(documents=texts, metadatas=metadatas, ids=ids)

print(f"✅ Indexed {len(documents)} anime character bios.")
