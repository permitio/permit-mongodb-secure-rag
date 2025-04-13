# Secure RAG Demo with MongoDB, Permit.io & LangChain

> A fully configured, secure RAG system that runs out-of-the-box—just add your API keys and go.

## Quickstart: 2-Min Plug & Play

### Requirements:

- [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) cluster (Free Tier is fine)
- [Permit.io account](https://www.permit.io/) (Free Tier is fine)
- [OpenAI API Key](https://platform.openai.com/account/api-keys)
- Docker & Docker Compose installed on your machine
- Python 3.11+ (recommended for running manual scripts, e.g., setup_users.py)

> You can check your version with `python3 --version` or install Python from [Python Official Website](https://www.python.org/)

### 1. Set Up Vector Search in MongoDB Atlas

1. Go to MongoDB Atlas and log in or sign up.
2. Create a new project, then create a new cluster (Free M0 tier works).
3. Once your cluster is ready:
   Click "Browse Collections" → Create a new database named secure_rag and a collection named documents.
4. Go to the "Search Indexes" tab and click "Create Search Index".
5. Select Vector Search as the search type.
6. Choose your secure_rag database and documents collection.
7. Select JSON Editor under "Configuration Method" and paste the following:

```json
{
  "fields": [
    {
      "numDimensions": 1536,
      "path": "vector_embedding",
      "similarity": "cosine",
      "type": "vector"
    },
    {
      "path": "metadata.department",
      "type": "filter"
    },
    {
      "path": "document_id",
      "type": "filter"
    }
  ]
}
```

- Click Save. Let the index finish building before continuing.
- You're done with MongoDB Vector Search setup!

> [Learn more about vector search indexing](https://www.mongodb.com/docs/atlas/atlas-search/vector-search/)

### 2. Clone the Project Repository & Add Your .env File

#### Clone the repository:

```bash
git clone https://github.com/permitio/permit-mongodb-secure-rag.git
cd permit-mongodb-secure-rag
```

Create a `.env` file in the root of the project and add your credentials::

```
MONGODB_URI=<your-mongodb-uri>
OPENAI_API_KEY=<your-openai-api-key>
PERMIT_API_KEY=<your-permit-api-key>
PERMIT_PDP_URL=http://permit-pdp:7000
```

### 3. Run It All

```bash
docker-compose up --build
```

This will:

This command will:

- Start Permit PDP locally
- Sync markdown docs in the docs/ folder to MongoDB
- Generate embeddings for each document
- Sync metadata, users, departments & ReBAC policies to Permit.io
- Start the LangChain FastAPI server so you can begin querying securely

Once all services are healthy, the app will be fully running and query-ready!

---

## Test the RAG Query API

Query endpoint:

```bash
curl -X POST http://localhost:8000/query \
 -H "Content-Type: application/json" \
 -d '{"query": "Tell me about 2024 budget", "user_id": "user_marketing_1"}'
```

Try querying with:

- `carol` → `user_marketing_1` viewer in `marketing`
- `alice` → `user_engineering_1` → viewer in `engineering`

---

## Project Structure

- `docs/` → Markdown documents grouped by department
- `watcher/` → Syncs docs to MongoDB + triggers embeddings generation for each document
- `scripts/` → Permit ReBAC setup (policies, departments, users)
- `app/` → LangChain API logic (FastAPI powered)
- `Dockerfile*` → Docker setup for each service

---

## How Permissions Work

- Each markdown file contains frontmatter metadata (e.g. department, confidential)
- This metadata is synced to Permit.io as resource instances
- When a user makes a query, LangChain asks Permit.io which documents they can access
- MongoDB vector search filters based on permitted IDs only
- Final response is generated using OpenAI from **only** allowed docs

---

## Want Full Control? [See `MANUAL_SETUP.md`](./MANUAL_SETUP.md)

If you want to:

- Define policies manually in the UI
- Customize user/dept/resource mappings
- Manage ReBAC setup yourself

Use the manual route instead.

---
