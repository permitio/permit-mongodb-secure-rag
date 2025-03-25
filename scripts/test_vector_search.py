# import os
# from dotenv import load_dotenv
# from pymongo import MongoClient, ASCENDING
# from langchain_mongodb.vectorstores import MongoDBAtlasVectorSearch
# from langchain_openai import OpenAIEmbeddings

# load_dotenv()

# MONGODB_URI = os.getenv("MONGODB_URI")
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# mongo_client = MongoClient(MONGODB_URI)
# db = mongo_client.secure_rag
# collection = db.documents
# embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

# ========> Testing Vector Search <========
# vector_store = MongoDBAtlasVectorSearch(
#     collection=collection,
#     embedding=embeddings,
#     index_name="vector_index",
#     text_key="content",
#     embedding_key="vector_embedding",
# )

# results = vector_store.similarity_search(
#     query="Tell me about the budget",
#     k=4,
#     pre_filter={
#         "document_id": {
#             "$in": [
#                 "eoy_marketing_c891085e",
#                 "product_roadmap_ddd85fe3",
#                 "marketing_plan_307c8659",
#             ]
#         }
#     },
# )
# print("Search Results:")
# for doc in results:
#     print(f"Document ID: {doc.metadata.get('document_id')}")
#     print(f"Content Snippet: {doc.page_content[:200]}...")
#     print("---")

# =====> End of Testing Vector Search <=======

# <====== Verify embeddings <==========

# doc = collection.find_one({"document_id": "budget_2024_c34ced42"})
# print("doc", doc)
# print(doc.get("vector_embedding"))

# <======= End of Verify embeddings <=======


# <=======   generate_embeddings.py <=======

# document_ids = [
#     "eoy_marketing_c891085e",
#     "product_roadmap_ddd85fe3",
#     "marketing_plan_307c8659",
# ]
# documents = collection.find({"document_id": {"$in": document_ids}})

# for doc in documents:
#     content = doc["content"]
#     vector_embedding = embeddings.embed_query(content)
#     collection.update_one(
#         {"_id": doc["_id"]}, {"$set": {"vector_embedding": vector_embedding}}
#     )
#     print(f"Updated embedding for document_id: {doc['document_id']}")

# for doc_id in document_ids:
#     doc = collection.find_one({"document_id": doc_id})
#     print(
#         f"vector_embedding for {doc_id}: {doc.get('vector_embedding')[:5]}... (first 5 values)"
#     )

#  ======> End of generate_embeddings.py <=======

# <======== Run Index =======>

# Retrieve MongoDB URI from environment

# mongo_client = MongoClient(MONGODB_URI)
# db = mongo_client.secure_rag
# collection = db.documents

# try:
#     collection.create_index(
#         [("document_id", ASCENDING)], name="document_id_index", unique=True
#     )
#     print("Index 'document_id_index' created successfully on secure_rag.documents")
# except Exception as e:
#     print(f"Error creating index: {str(e)}")

# mongo_client.close()

# <======== End of Run Index =======>
