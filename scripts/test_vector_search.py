# # test_vector_search.py
# from pymongo import MongoClient
# from langchain_mongodb.vectorstores import MongoDBAtlasVectorSearch
# from langchain_openai import OpenAIEmbeddings

# # MongoDB connection
# MONGODB_URI = (
#     "mongodb+srv://"
# )
# mongo_client = MongoClient(MONGODB_URI)
# db = mongo_client.secure_rag
# collection = db.documents

# # Initialize embeddings
# embeddings = OpenAIEmbeddings(
#     openai_api_key="sk-proj-xxxx"
# )  # Update with your API key

# # Initialize vector store
# vector_store = MongoDBAtlasVectorSearch(
#     collection=collection,
#     embedding=embeddings,
#     index_name="vector_index",
#     text_key="content",
#     embedding_key="vector_embedding",
# )

# # Test vector search
# results = vector_store.similarity_search(
#     query="Tell me about the budget",
#     k=4,
#     pre_filter={
#         "document_id": {"$in": ["budget_2024_a2c7ca81", "revenue_forecast_fdabf74e"]}
#     },
# )

# # Print results
# print("Search Results:")
# for doc in results:
#     print(f"Document ID: {doc.metadata.get('document_id')}")
#     print(f"Content Snippet: {doc.page_content[:200]}...")
#     print("---")

# <====== Verify embeddings <==========
# from pymongo import MongoClient

# client = MongoClient(
#     "mongodb+srv://taofiqaiyelabegan45:YIqBRTAM2tTxtwFB@cluster0.ki6xb.mongodb.net/"
# )
# db = client.secure_rag
# collection = db.documents

# doc = collection.find_one({"document_id": "budget_2024_a2c7ca81"})
# print("doc", doc)
# print(doc.get("vector_embedding"))


# <=======   generate_embeddings.py <=======
# from pymongo import MongoClient
# from langchain_openai import OpenAIEmbeddings

# # MongoDB connection
# client = MongoClient(
#     "mongodb+srv://taofiqaiyelabegan45:YIqBRTAM2tTxtwFB@cluster0.ki6xb.mongodb.net/"
# )
# db = client.secure_rag
# collection = db.documents

# # Initialize embeddings
# embeddings = OpenAIEmbeddings(
#     openai_api_key="sk-proj-pLasv...."
# )  # Update with your API key

# # Fetch documents
# document_ids = ["budget_2024_a2c7ca81", "revenue_forecast_fdabf74e"]
# documents = collection.find({"document_id": {"$in": document_ids}})

# # Generate and update embeddings
# for doc in documents:
#     content = doc["content"]
#     vector_embedding = embeddings.embed_query(content)  # Generate embedding
#     collection.update_one(
#         {"_id": doc["_id"]}, {"$set": {"vector_embedding": vector_embedding}}
#     )
#     print(f"Updated embedding for document_id: {doc['document_id']}")

# # Verify the update
# for doc_id in document_ids:
#     doc = collection.find_one({"document_id": doc_id})
#     print(
#         f"vector_embedding for {doc_id}: {doc.get('vector_embedding')[:5]}... (first 5 values)"
#     )

# <======== Run Index =======>
# import os
# from pymongo import MongoClient, ASCENDING

# # Retrieve MongoDB URI from environment
# MONGODB_URI = os.environ.get("MONGODB_URI")
# if not MONGODB_URI:
#     raise ValueError("MONGODB_URI environment variable is not set")

# # Initialize MongoDB client
# mongo_client = MongoClient(MONGODB_URI)
# db = mongo_client.secure_rag
# collection = db.documents

# # Create the index on document_id
# try:
#     collection.create_index(
#         [("document_id", ASCENDING)], name="document_id_index", unique=True
#     )
#     print("Index 'document_id_index' created successfully on secure_rag.documents")
# except Exception as e:
#     print(f"Error creating index: {str(e)}")

# # Close the MongoDB connection
# mongo_client.close()
