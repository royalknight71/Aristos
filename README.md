# Aristos — Engineering Knowledge Copilot

Aristos is an engineering knowledge copilot in early development. The initial scaffold contains a FastAPI health endpoint and a minimal React landing screen; document processing, search, chat, authentication, and infrastructure integrations remain planned.

## Problem statement

Engineering teams often need to find trustworthy details across specifications, runbooks, design documents, and other technical references. Aristos is intended to make that knowledge easier to search while keeping answers tied to source passages and abstaining when the available evidence is insufficient.

## Core features

Planned capabilities include:

- Upload and process PDF, Markdown, and plain-text documents.
- Search document content and answer questions using retrieved evidence.
- Show validated citations with document names, page numbers where available, and relevant passages.
- Maintain conversations and stream answers.
- Evaluate retrieval quality, groundedness, citation correctness, and abstention behavior.

Only the initial web landing screen and API health endpoint are scaffolded. The capabilities above are not yet implemented.

## High-level architecture

The planned system uses a React web client and a Python/FastAPI modular monolith. The initial MVP architecture also calls for an asynchronous ingestion worker, MongoDB with GridFS for application records and original files, Qdrant for vector retrieval, and Redis with ARQ as the ingestion job broker. Redis is not intended for answer caching. OpenAI integrations will sit behind provider adapters.

These infrastructure services and AI integrations are not part of the current scaffold.

## Technology stack

| Area | Selected technology |
| --- | --- |
| Frontend | React, TypeScript, Vite, Tailwind CSS, npm |
| Backend | Python 3.14, FastAPI, Pydantic, Pydantic Settings |
| Backend dependency management | uv with `pyproject.toml` and `uv.lock` |
| Application data and source files (planned) | MongoDB and GridFS |
| Vector search (planned) | Qdrant |
| Ingestion jobs (planned) | Redis and ARQ |
| Model integrations (planned) | OpenAI through provider adapters |

The initial proposed embedding model is `text-embedding-3-small`, configurable through provider settings. The chat model and its token and cost budget remain open decisions. The experimental chunk defaults are 700 tokens with 100-token overlap.

## RAG workflow

The planned retrieval-augmented generation workflow is:

1. A user uploads an allowed document and has permission to share its contents with external API providers.
2. The backend validates the file, stores the original in GridFS, records metadata and job state in MongoDB, and dispatches an ingestion job through Redis and ARQ.
3. A worker extracts and normalizes text, preserves PDF page references and useful structure where possible, chunks the text, and requests embeddings through a provider adapter.
4. The worker stores versioned chunk vectors and metadata in Qdrant. Only a complete active index is eligible for retrieval.
5. The backend applies workspace and active-index filters, then retrieves relevant chunks for a question.
6. The backend constructs a grounded answer using retrieved context, validates citation IDs against the retrieved chunks, and returns citations based on server-side metadata.
7. The system abstains when retrieved evidence is insufficient.

No part of this workflow is implemented yet.

## Repository structure

```text
Aristos/
├── backend/
│   ├── .env.example
│   ├── .python-version
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── app/
│   │   ├── api/routes/health.py
│   │   ├── core/config.py
│   │   └── main.py
│   └── tests/test_health.py
├── docs/
│   ├── ARCHITECTURE.md
│   └── IMPLEMENTATION_DECISIONS.md
├── frontend/
│   ├── .nvmrc
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   ├── src/
│   ├── tsconfig.json
│   └── vite.config.ts
├── .gitignore
└── README.md
```

## Prerequisites

- Python 3.14 (use the latest compatible patch available for your platform).
- Node.js 24 LTS and npm.
- uv for backend dependency management. The repository lockfile is generated with uv.

Docker is not needed to run the current scaffold. It will be used when local infrastructure is added in a later milestone.

## Local development setup

The following commands use the repository's approved runtime versions.

### Backend

From the repository root:

```powershell
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

The API runs at `http://127.0.0.1:8000`; `GET /health` returns `{"status":"ok"}`.

Run backend tests with:

```powershell
uv run python -m pytest -p no:cacheprovider
```

### Frontend

In a second terminal, from the repository root:

```powershell
cd frontend
npm ci
npm run dev
```

Run the TypeScript check and production build with:

```powershell
npm run typecheck
npm run build
```

## Configuration and environment variables

The backend reads `ARISTOS_APP_NAME` through Pydantic Settings. A non-secret example is in `backend/.env.example`; settings may also be supplied through the process environment. No credentials or external service settings are needed by this scaffold.

## Security and data privacy

- Public access must remain disabled until a vetted authentication mechanism and workspace authorization are implemented. A development-only identity is not configured in this scaffold.
- Document content may be sent to an external provider only when the user is permitted to share it; provider calls must check consent.
- Workspace authorization and isolation must be enforced by the backend for application data and vector retrieval.
- Provider credentials must stay out of browser code and source control.
- Documents are untrusted input. Retrieved text is evidence, not instructions; citation IDs must be validated against retrieved chunks.
- Deletion and re-indexing must handle partial failures across MongoDB/GridFS and Qdrant with retryable cleanup.

These are architecture requirements, not claims that their controls have been implemented. The scaffold is not ready for public use.

## Testing and evaluation strategy

The scaffold includes backend tests for application startup and `GET /health`. The frontend provides TypeScript and production-build checks. Retrieval and answer evaluation is planned for a small labeled set covering answerable, ambiguous, and unanswerable questions, using Recall@5, Recall@10, Precision@5, MRR, and nDCG@10 alongside manual review of relevance, groundedness, citation correctness, and abstention behavior. Security tests, including cross-workspace isolation, must block release if they fail.

The retrieval and answer evaluation suite is not implemented yet.

## Roadmap

The approved roadmap remains sequential, with each milestone verified before its Definition of Done is claimed:

1. **Repository baseline and decisions:** establish the repository, runtime compatibility, and remaining owner decisions.
2. **Local infrastructure and backend foundation:** add the API and worker foundation with MongoDB, Qdrant, and Redis services.
3. **Document upload and ingestion:** implement validation, GridFS storage, ARQ jobs, extraction, chunking, embeddings, indexing, retries, re-indexing, and deletion cleanup.
4. **Grounded question answering:** add workspace-filtered retrieval, conversations, validated citations, abstention, and streaming.
5. **Minimal usable frontend:** implement upload, document status, chat, conversation history, and citation display.
6. **Evaluation and hardening:** measure retrieval and citation quality, address security and reliability, and document operational limits.
7. **Evidence-driven improvements:** consider reranking, OCR, hybrid retrieval, or other extensions only when evaluation or user feedback demonstrates a need.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and [docs/IMPLEMENTATION_DECISIONS.md](docs/IMPLEMENTATION_DECISIONS.md) for details and open decisions.

## License

No `LICENSE` file is present, and a project license has not yet been selected.
