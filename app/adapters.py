from langchain_mongodb.vectorstores import MongoDBAtlasVectorSearch
from typing import Any, Dict, List, Optional


class MongoDBAtlasVectorSearchWithQueryTransformer(MongoDBAtlasVectorSearch):
    """MongoDB Atlas Vector Search with added query transformer support for PermitSelfQueryRetriever."""

    # Store the current retriever being used
    _current_retriever = None

    def as_query_transformer(self):
        """Create a query transformer compatible with PermitSelfQueryRetriever."""

        # Reference to the outer class from the inner function
        vector_store = self

        def transform_query(structured_query):
            """Transform a structured query to MongoDB filter format."""
            try:
                # Access the allowed_ids from the stored retriever
                allowed_ids = []
                if vector_store._current_retriever and hasattr(
                    vector_store._current_retriever, "_allowed_ids"
                ):
                    allowed_ids = vector_store._current_retriever._allowed_ids

                # Create filter with document IDs
                if allowed_ids:
                    clean_filter = {"document_id": {"$in": allowed_ids}}
                else:
                    clean_filter = {}

                # Set default k if not specified
                k = structured_query.limit if structured_query.limit else 4

                return {"pre_filter": clean_filter, "k": k}

            except Exception as e:
                print(f"Error in transform_query: {str(e)}")
                return {"pre_filter": {}, "k": 4}

        return transform_query
