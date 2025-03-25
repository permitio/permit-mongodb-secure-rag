# Secure RAG Demo with MongoDB, Permit.io, and LangChain

This project demonstrates a Secure Retrieval-Augmented Generation (RAG) system using MongoDB, Permit.io, and LangChain. It provides a secure AI agent that retrieves and generates responses based on user identity and permissions, ensuring sensitive data is only accessed by authorized users.

## Table of Contents

- [Project Overview](#project-overview)
- [Architecture Diagram](#architecture-diagram)
- [Prerequisites](#prerequisites)
- [Setup Instructions](#setup-instructions)
  - [MongoDB Atlas Setup](#mongodb-atlas-setup)
  - [Permit.io Setup (Manual Configuration)](#permitio-setup-manual-configuration)
  - [Environment Variables](#environment-variables)
- [Running the Project](#running-the-project)
- [ReBAC Policy Demo in Permit.io](#rebac-policy-demo-in-permitio)
- [How Permissions Enable Secure RAG](#how-permissions-enable-secure-rag)
- [Contributing](#contributing)
- [License](#license)

## Project Overview

Secure RAG combines Retrieval-Augmented Generation with Role-Based Access Control (ReBAC) to ensure that an AI agent only retrieves and generates responses from data a user is authorized to access. This project integrates:

- **MongoDB Atlas**: Stores documents and their embeddings for RAG, with vector search and database indexing for efficient retrieval.

- **Permit.io**: Manages access control using a ReBAC model to enforce permissions based on user identity and department.

- **LangChain**: Provides the framework for building the RAG pipeline, connecting MongoDB for retrieval and OpenAI for generation.

- **Docker Compose**: Orchestrates the services (MongoDB, Permit PDP, LangChain app, and file-watcher).

## Key Features

- **Secure Retrieval**: Retrieves only documents a user is permitted to access, based on their identity and department.

- **File Syncing**: A file-watcher service monitors the docs directory for changes (additions, updates, deletions) and syncs Markdown files to MongoDB.

- **Policy Tagging**: Syncs document metadata to Permit.io as resource instances (e.g., document:api_design_3d08a90b) with attributes like department and confidential.

- **Immediate RAG Availability**: Newly added files are synced to MongoDB and immediately available for RAG queries.

## Architecture Diagram

The following diagram illustrates how the components interact:

![image](https://github.com/user-attachments/assets/4bf0f315-9b5e-47e4-be58-491684f214a4)

## Architecture Components

- **File-Watcher**: Monitors the docs directory and syncs files to MongoDB.
- **MongoDB Atlas**: Stores documents and embeddings, enabling vector search for RAG.
- **Permit.io**: Enforces ReBAC policies to filter documents based on user permissions.
- **LangChain App**: Queries MongoDB for permitted documents and uses OpenAI to generate answers.
- **OpenAI API**: Provides the LLM for answer generation.

## Prerequisites

Before setting up the project, ensure you have the following:

- Docker and Docker Compose installed.
- MongoDB Atlas account (free tier is sufficient).
- Permit.io account (free tier available).
- OpenAI API Key for embeddings and generation.
- Python 3.11 or higher (for running manual scripts).
- Git to clone the repository.

## Setup Instructions

### MongoDB Atlas Setup

1. **Create a MongoDB Atlas Cluster**:

   - Sign up/login to MongoDB Atlas.
   - Create a new cluster (e.g., Cluster0) in your preferred region (e.g., AWS Singapore).
   - Use the free tier (M0 Sandbox) for this demo.

2. **Create the Database and Collection**:

   - In your cluster, go to the "Collections" tab.
   - Create a database named `secure_rag`.
   - Add a collection named `documents`.

3. **Set Up Vector Search Index**:
   - Go to the "Atlas Search" tab in your cluster.
   - Click "Create Search Index" and select "Vector Search".
   - Use the JSON editor to create an index named `vector_index` with the following configuration:

```json
{
  "fields": [
    {
      "type": "vector",
      "path": "vector_embedding",
      "numDimensions": 1536,
      "similarity": "cosine"
    },
    {
      "type": "filter",
      "path": "metadata.department"
    }
  ]
}
```

**Explanation**:

- `vector_embedding`: Field storing document embeddings (1536 dimensions for OpenAI embeddings).
- `cosine`: Similarity metric for vector search.
- `metadata.department`: Enables pre-filtering by department.

4. Click "Next" and "Create Index". Wait for the index status to show as "READY".

5. **Set Up Database Index on document_id**:
   - Go to the "Indexes" tab in the `secure_rag.documents` collection.
   - Click "Create Index" (not "Create Search Index").
   - Use the following configuration:
     - Field: `document_id`
     - Type: 1 (asc)
     - Options:
       - Check "Create unique index".
       - Index name: `document_id_index`.
       - Leave "Create TTL" unchecked.
   - Click "Create Index".

**Explanation**:

- This index improves performance for lookups and updates on `document_id`, which is used as a unique identifier.

6. **Get MongoDB Connection URI**:
   - In the Atlas UI, click "Connect" on your cluster.
   - Choose "Connect your application".
   - Copy the connection string (e.g., `mongodb+srv://<username>:<password>@cluster0.mongodb.net/secure_rag?retryWrites=true&w=majority`).
   - Replace `<username>` and `<password>` with your Atlas credentials.

### Permit.io Setup (Manual Configuration)

Since we're not using scripts for setup, we'll configure Permit.io manually via the UI. This includes setting up the ReBAC model, departments, users, and role derivations.

1. **Sign Up/Login to Permit.io**:

   - Go to Permit.io and sign up/login.
   - Create a new project (e.g., SecureRAGDemo).

2. **Define Resources and Roles**:

   - Go to the "Policy Editor" in the Permit.io UI.
   - Define the following resources and roles:
     - Resource: `department`
       - Actions: None needed for this demo.
     - Resource: `document`
       - Actions: `read`
     - Role: `viewer`
       - Permissions: `document:read`

3. **Create Department Instances**:

   - Go to "Resources" > "department".
   - Add the following department instances:
     - `department:engineering` (Attributes: name: "Engineering Department")
     - `department:marketing` (Attributes: name: "Marketing Department")
     - `department:finance` (Attributes: name: "Finance Department")

   **Steps**:

   - Click "Create Resource Instance".
   - Set key to `engineering`, tenant to `default`, and add the attribute `name: "Engineering Department"`.
   - Repeat for `marketing` and `finance`.

4. **Create Users**:

   - Go to "Users" in the Permit.io UI.
   - Add the following users:
     - User: `alice` (email: alice@example.com)
     - User: `bob` (email: bob@example.com)

   **Steps**:

   - Click "Create User".
   - Set key to `alice`, email to alice@example.com.
   - Repeat for `bob`.

5. **Assign Roles to Users**:

   - Go to "Role Assignments".
   - Assign roles:
     - `alice` → `viewer` in `department:engineering`
     - `bob` → `viewer` in `department:marketing`

   **Steps**:

   - Click "Assign Role".
   - Select user `alice`, role `viewer`, and resource `department:engineering`.
   - Repeat for `bob` with `department:marketing`.

6. **Define Role Derivations (Policy)**:

   - Go to "Policy Editor".
   - Add a role derivation to inherit permissions:
     - If a user has the `viewer` role in `department:X`, they inherit `document:read` for documents where department is the parent of the document.

   **Steps**:

   - In the "Policy Editor", add a derivation rule:
     - Resource: `document`
     - Role: `viewer`
     - Condition: User has role `viewer` in `department` AND department is parent of document.

7. **Get Permit API Key and PDP URL**:
   - Go to "Settings" > "API Keys" in Permit.io.
   - Generate an API key and copy it.
   - The PDP URL is typically `http://permit-pdp:7000` (as defined in docker-compose.yml).

## Automating Your Permit.io Setup with Scripts

If you prefer to automate the setup of resources, roles, departments, users, and relationships in Permit.io, you can use the provided scripts instead of configuring everything manually via the UI. After running these scripts, you’ll only need to define the role derivation manually in the Permit.io UI.

1. **Install Script Dependencies**:

   - The scripts require the `permit` package. Install it using:
     ```bash
     pip install permit
     ```

2. **Set Environment Variables for Scripts**:

   - Ensure `PERMIT_API_KEY` and `PERMIT_PDP_URL` are set in your `.env` file:
     ```
     PERMIT_API_KEY=<your-permit-api-key>
     PERMIT_PDP_URL=http://permit-pdp:7000
     ```
   - You can get the `PERMIT_API_KEY` from the Permit.io UI under "Settings" > "API Keys".

3. **Run the Setup Scripts**:

   - **Set Up ReBAC Model**:
     - Run `setup_rebac.py` to define resources (`department`, `document`), roles (`viewer`), and relationships:
       ```bash
       python setup_rebac.py
       ```
   - **Create Departments**:
     - Run `setup_departments.py` to create department instances (`department:engineering`, `department:marketing`, `department:finance`):
       ```bash
       python setup_departments.py
       ```
   - **Create Users and Assign Roles**:
     - Run `setup_users.py` to create users (`alice`, `bob`) and assign roles (e.g., `alice` as `viewer` in `department:engineering`):
       ```bash
       python setup_users.py
       ```

4. **Manually Define Role Derivation in Permit.io UI**:

   - The scripts set up resources, roles, and relationships, but you need to define the role derivation manually.
   - Go to the "Policy Editor" in the Permit.io UI.
   - Add a role derivation:
     - Resource: `document`
     - Role: `viewer`
     - Condition: User has role `viewer` in `department` AND `department` is `parent` of `document`.
   - **Explanation**:
     - This derivation ensures that a user with the `viewer` role in a department (e.g., `department:engineering`) can read documents where that department is the `parent`.

5. **Verify Setup**:
   - In the Permit.io UI, check:
     - "Resources" > "department" for department instances.
     - "Resources" > "document" for document instances (after syncing documents).
     - "Users" for `alice` and `bob` with their role assignments.
     - "Policy Editor" for the role derivation.

### Environment Variables

**Create a .env File**:

- In the project root, create a `.env` file.
- Add the following variables:

```
MONGODB_URI=<your-mongodb-atlas-uri>
OPENAI_API_KEY=<your-openai-api-key>
PERMIT_API_KEY=<your-permit-api-key>
PERMIT_PDP_URL=http://permit-pdp:7000
```

## Running the Project

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/<your-username>/secure-rag-demo.git
   cd secure-rag-demo
   ```

2. **Install Dependencies**:

   - **For Dockerized Services (LangChain App and File-Watcher)**:
     - Dependencies are automatically installed when you build the Docker containers using `docker-compose up --build`. The `Dockerfile` and `Dockerfile.watcher` handle installing `requirements.txt` and `requirements.watcher.txt`, respectively.
   - **For Manual Scripts (Embedding Generation and Permit.io Syncing)**:
     - To run any of the script in the `scripts` folder, install their dependencies manually:
       ```bash
       pip install -r requirements.embeddings.txt
       pip install -r requirements.txt
       ```

3. **Spin Up Services with Docker Compose**:

   - Run the following command to start all services:

     ```bash
     docker-compose up --build
     ```

   - This will start:
     - `permit-pdp`: Permit.io Policy Decision Point.
     - `file-watcher`: Monitors the `docs` directory and syncs files to MongoDB.
     - `langchain-app`: The Secure RAG API, accessible at `http://localhost:8000`.

4. **Sync Documents to Permit.io**:

   - The `file-watcher` will sync documents in the `docs` directory to MongoDB.
   - Manually sync documents to Permit.io using the `sync_documents.py` script:

     ```bash
     python sync_documents.py
     ```

   - **Note**: Update the `file_path` in `sync_documents.py` to the document you want to sync (e.g., `./docs/engineering/api_design.md`).

5. **Generate Embeddings for Documents**:

   - Run the `generate_embeddings.py` script to generate embeddings for documents in MongoDB:

     ```bash
     python generate_embeddings.py --all
     ```

   - This generates embeddings for all documents and stores them in the `vector_embedding` field.

6. **Test the Secure RAG API**:

   - Query the API with a user ID to test Secure RAG:

     ```bash
     curl -X POST http://localhost:8000/query \
     -H "Content-Type: application/json" \
     -d '{"query": "What is API design?", "user_id": "alice"}'
     ```

   - **Expected Behavior**:
     - `alice` (in `engineering`) can access documents in the `engineering` department.
     - `bob` (in `marketing`) cannot access `engineering` documents.

## ReBAC Policy Demo in Permit.io

Here's a simple ReBAC policy configured in Permit.io:

### Resources:

- **department**: Represents departments (e.g., department:engineering).
- **document**: Represents documents (e.g., document:api_design_3d08a90b).

### Roles:

- **viewer**: Has document:read permission.

### Relationships:

- department:engineering is parent of document:api_design_3d08a90b.

### Role Derivation:

- A user with the viewer role in department:engineering inherits document:read for all documents where department:engineering is the parent.

### Example

- **Document**: document:api_design_3d08a90b (attributes: department: "engineering")
- **User**: alice (role: viewer in department:engineering)

#### Policy Result:

- alice can read document:api_design_3d08a90b because she has the viewer role in department:engineering, and department:engineering is the parent of the document.
- bob (role: viewer in department:marketing) cannot read this document.

## How Permissions Enable Secure RAG

### User Identity:

- The API receives a user_id (e.g., alice) in the query request.

### Permission Check:

- The LangChain app queries Permit.io to determine which documents alice can read.
- Permit.io evaluates the ReBAC policy and returns a list of accessible document IDs.

### Filtered Retrieval:

- LangChain queries MongoDB Atlas, filtering by the permitted document IDs and the user's query (e.g., "What is API design?").
- MongoDB performs a vector search on the vector_embedding field to retrieve relevant documents.

### Answer Generation:

- The retrieved documents are passed to OpenAI to generate a context-aware answer.
- Only content from permitted documents is used in the response.

This ensures that sensitive data (e.g., engineering documents) is only accessible to authorized users (e.g., alice), making the RAG system secure.

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository.
2. Create a new branch (git checkout -b feature/your-feature).
3. Make your changes and commit (git commit -m "Add your feature").
4. Push to your branch (git push origin feature/your-feature).
5. Open a pull request.
