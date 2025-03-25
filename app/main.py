# app/main.py
import os
import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from permit import Permit
from langchain_mongodb.vectorstores import MongoDBAtlasVectorSearch
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

from .models import QueryRequest, QueryResponse, HealthResponse
from .adapters import MongoDBAtlasVectorSearchWithQueryTransformer
from langchain_permit.retrievers import PermitSelfQueryRetriever
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UserPermissionsRequest(BaseModel):
    user_id: str
    resource_types: Optional[List[str]] = None


class UserPermissionsResponse(BaseModel):
    permissions: dict


app = FastAPI(
    title="Secure RAG Demo",
    description="A secure RAG application using MongoDB Atlas, Permit.io, and LangChain",
    version="0.1.0",
)

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://root:example@mongodb:27017")
PERMIT_PDP_URL = os.getenv("PERMIT_PDP_URL")
PERMIT_API_KEY = os.getenv("PERMIT_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


mongo_client = MongoClient(MONGODB_URI)
db = mongo_client.secure_rag
collection = db.documents

permit_client = Permit(token=PERMIT_API_KEY, pdp=PERMIT_PDP_URL)

embeddings = OpenAIEmbeddings()

llm = ChatOpenAI(temperature=0)

vector_store = MongoDBAtlasVectorSearchWithQueryTransformer(
    collection=collection,
    embedding=embeddings,
    index_name="vector_index",
    text_key="content",
    embedding_key="vector_embedding",
)

rag_prompt_template = """
Answer the question based on the following context:

Context:
{context}

Question:
{question}

Provide a comprehensive and accurate answer based only on the provided context.
If the information isn't in the context, say "I don't have enough information to answer this question."
"""

rag_prompt = ChatPromptTemplate.from_template(rag_prompt_template)


def create_rag_chain(retriever):
    """Create a RAG chain with the given retriever."""

    async def retrieve_docs(query):
        docs = await retriever.invoke(query)
        return "\n\n".join(doc.page_content for doc in docs)

    return (
        {"context": RunnableLambda(retrieve_docs), "question": RunnablePassthrough()}
        | rag_prompt
        | llm
        | StrOutputParser()
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    mongodb_ok = False
    permit_ok = False

    try:
        mongo_client.admin.command("ping")
        mongodb_ok = True
    except Exception as e:
        logger.error(f"MongoDB health check failed: {str(e)}")

    try:
        await permit_client.check("user_marketing_1", "read", "document")
        permit_ok = True
    except Exception as e:
        logger.error(f"Permit.io health check failed: {str(e)}")

    return {
        "status": "ok" if mongodb_ok and permit_ok else "degraded",
        "mongodb": mongodb_ok,
        "permit": permit_ok,
    }


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Process a RAG query with permission-based document filtering.

    The query will only return documents that the user has permission to access
    based on their department and the document's department and confidentiality.
    """
    try:
        user = {
            "key": request.user_id,
        }

        retriever = await PermitSelfQueryRetriever.from_permit_client(
            permit_client=permit_client,
            user=user,
            resource_type="document",
            action="read",
            llm=llm,
            vectorstore=vector_store,
            enable_limit=True,
        )

        rag_chain = create_rag_chain(retriever)

        answer = await rag_chain.ainvoke(request.query)

        docs = await retriever.invoke(request.query)

        # Check if the LLM returned the default message due to irrelevant documents
        if answer.strip() == "I don't have enough information to answer this question.":
            allowed_ids = (
                retriever._allowed_ids if hasattr(retriever, "_allowed_ids") else []
            )
            answer = f"No documents match your query due to permission restrictions. You only have access to documents: {allowed_ids}."
            logger.warning(
                "Retrieved documents are irrelevant to the query due to permissions"
            )
            sources = []  # Set sources to empty since no relevant documents were found
        else:
            # Populate sources only if the answer is based on relevant documents
            sources = []
            for doc in docs:
                if not isinstance(doc.metadata, dict):
                    logger.error(
                        f"Unexpected metadata type: {type(doc.metadata)} for doc: {doc}"
                    )
                    continue
                metadata = doc.metadata.get("metadata", {})
                source = {
                    "document_id": doc.metadata.get("document_id", "unknown"),
                    "filename": doc.metadata.get("filename", "unknown"),
                    "department": metadata.get("department", "unknown"),
                    "author": metadata.get("author", "unknown"),
                    "confidential": metadata.get("confidential", False),
                    "snippet": (
                        doc.page_content[:200] + "..."
                        if len(doc.page_content) > 200
                        else doc.page_content
                    ),
                }
                sources.append(source)

        if not docs:
            logger.warning("No documents found for the query")
        response = {"answer": str(answer), "sources": sources}

        if not isinstance(response, dict):
            logger.error(f"Response is not a dictionary: {response}")
            return {"answer": "Error: Failed to construct response", "sources": []}
        return response

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")
    finally:
        logger.info("Endpoint execution completed")


@app.post("/user-permissions", response_model=UserPermissionsResponse)
async def get_user_permissions(request: UserPermissionsRequest):
    try:
        user = {"key": request.user_id}

        permissions = await permit_client.get_user_permissions(
            user=user, resource_types=request.resource_types
        )

        logger.info(f"User permissions for {request.user_id}: {permissions}")
        return {"permissions": permissions}

    except Exception as e:
        logger.error(f"Error fetching user permissions: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error fetching user permissions: {str(e)}"
        )


@app.delete("/delete-documents-collection")
async def delete_documents_collection():
    try:
        db = mongo_client.secure_rag
        db.documents.drop()
        return {"message": "Documents collection deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error deleting collection: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
