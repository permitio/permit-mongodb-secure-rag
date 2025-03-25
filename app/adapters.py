from langchain_mongodb.vectorstores import MongoDBAtlasVectorSearch
from typing import Any, Dict, List, Optional


class MongoDBAtlasVectorSearchWithQueryTransformer(MongoDBAtlasVectorSearch):
    """MongoDB Atlas Vector Search with added query transformer support for PermitSelfQueryRetriever."""

    def as_query_transformer(self):
        """Create a query transformer compatible with PermitSelfQueryRetriever."""

        def transform_query(structured_query):
            """Transform a structured query to MongoDB filter format."""
            mongo_filter = structured_query.filter if structured_query.filter else {}
            print("🔐 Mongo filter", mongo_filter)
            k = structured_query.limit if structured_query.limit else 4
            print("💃 k", k)
            return {"pre_filter": mongo_filter, "k": k}

        return transform_query
