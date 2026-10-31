# Aristos MVP Implementation Decisions

**Status:** Simplified single-user MVP scope approved. This document records the target choices and distinguishes them from what is implemented. It does not claim planned functionality is present.

## 1. Product and implementation status

Aristos is a single-user Engineering Knowledge Copilot. The MVP will accept PDF, TXT, and Markdown files, let the user ask questions, retrieve relevant passages, generate answers grounded in those passages with citations, and abstain when evidence is insufficient.

**Implemented today:** the repository has a FastAPI health endpoint, a minimal React landing screen, Qdrant client/lifecycle and connectivity health check, and a SQLite initialization foundation that creates the initial documents metadata table. Document upload, local source-file persistence, ingestion, retrieval, answer generation, citation validation, abstention, deletion, and user-facing workflow remain planned.

## 2. Approved architecture and technology

Use one modular-monolith Python/FastAPI application with Pydantic validation and synchronous ingestion. Keep a React, TypeScript, Vite, and Tailwind frontend. Run local infrastructure through Docker Compose. Use SQLite for metadata and document lifecycle state, local file storage for originals, Qdrant for derived vector data, and OpenAI for embeddings and answer generation.

| Area | Approved MVP decision | State |
|---|---|---|
| Product access | Single user; no managed authentication or workspace model | Planned |
| Frontend | React, TypeScript, Vite, Tailwind CSS | Scaffold exists; MVP workflow planned |
| Backend | Python, FastAPI, Pydantic; modular monolith | Health endpoint scaffolded; application modules planned |
| Ingestion | Synchronous within the API/application process | Planned |
| Metadata and lifecycle | SQLite | Connection initialization and initial table implemented; document workflow planned |
| Source documents | Local file storage under an application-controlled root | Planned |
| Vector search | Qdrant | Planned |
| Model calls | OpenAI embeddings and LLM, behind backend integration modules | Planned |
| Local orchestration | Docker Compose | Planned |

### Why SQLite and local file storage

The MVP is a single-user application, so SQLite is sufficient for durable metadata and lifecycle records without the operational overhead of a managed/server database or multi-user coordination. It provides transactions for local application state. Local files keep source documents easy to persist and inspect without GridFS or object-storage setup. These choices fit one application instance with access to its data directory and make local setup and backup straightforward.

This scope does not require horizontal replicas, shared file storage, organization isolation, or large concurrent write volumes. SQLite and local files do not provide those properties; reconsider them only if real deployment needs require it. Qdrant remains separate because it provides vector search. Its vectors are derived from originals and can be rebuilt.

### Initial SQLite metadata foundation

Use Python's built-in `sqlite3`. The default database path is `backend/data/aristos.db`, resolved from the backend project location rather than the process working directory. `ARISTOS_DATABASE_PATH` can override it; relative override paths are also resolved from the backend project location. Create the parent directory during initialization, and keep the generated `backend/data/` runtime directory out of version control.

The initial `documents` table contains exactly `id TEXT PRIMARY KEY`, `original_filename TEXT NOT NULL`, `storage_key TEXT NOT NULL`, and `status TEXT NOT NULL`. Store `storage_key` as a relative reference. The status column has no default or database-enforced value list. The lifecycle documentation describes ready, failed, and unavailable states, but does not specify an initial value for a newly accepted document or a complete status contract; resolve that before implementing the upload lifecycle rather than inventing states here.

## 3. Preserved input and chunking decisions

Continue to enforce the already approved limits, with server-side validation and configurable values:

| Limit or default | MVP value | Handling |
|---|---:|---|
| File formats | PDF, TXT, Markdown | Reject unsupported formats and archives |
| Upload bytes | 20 MiB maximum | Reject; never silently truncate |
| PDF pages | 300 maximum | Reject excess pages |
| Extraction duration | 60 seconds per document | Stop and report a safe failure |
| Normalized text | 1 MiB UTF-8 or 100,000 counted input tokens, whichever is reached first | Reject rather than present partial content as complete |
| Chunking | 700 tokens with 100-token overlap | Configurable experimental starting point, not an optimality claim |
| Embedding model | `text-embedding-3-small` starting choice | Configurable; verify access and dimensions when implemented |

Tokenizer selection remains an implementation detail to resolve before token-based limits and chunking are implemented. Extraction should preserve useful structure and PDF page references where feasible. OCR is out of scope.

## 4. Synchronous ingestion and lifecycle decisions

An upload request validates the file, stores its bytes locally, records metadata in SQLite, extracts and normalizes text, chunks it, requests embeddings, writes points to Qdrant, and records success/failure before returning. Do not dispatch work to a queue or worker. The established limits bound request work; provide safe timeout/error handling for provider and vector-store failures.

A document is searchable only after all expected vectors are written and metadata records a ready state. A partial index must not be represented as ready. Use stable document/chunk identifiers so cleanup is targeted and repeatable. Index versioning and concurrent re-index cutover are not MVP requirements; re-indexing can be deferred.

Deletion is required. Mark the document unavailable, remove its Qdrant points and local source, then record completion. Make steps idempotent. SQLite and Qdrant do not share a transaction, so preserve a minimal cleanup-failure state and report incomplete deletion if either store cannot be cleaned. Do not claim success until both source and vectors are removed. A background cleanup service is out of scope; implement an appropriate user-visible retry/recovery path in the application.

## 5. Retrieval, answers, citations, and abstention

Start with dense Qdrant vector retrieval and basic metadata filtering by document identity/state. Reranking is excluded. The answer flow uses retrieved passages as evidence for the configured OpenAI LLM. Document content is untrusted input and must not override system instructions; the MVP exposes no model tools or actions.

Validate generated citation IDs against the passages retrieved for that question. Build citation labels and page references from server-side metadata. Return structured citations with the answer. If retrieval yields no useful support or the available evidence is insufficient, return a clear abstention instead of asserting an unsupported answer. Add core pipeline tests for citation validation and abstention.

Use ordinary JSON request/response behavior; SSE streaming is excluded. Conversation history is not required for the MVP unless added through a later scope decision.

The embedding model has an initial configurable choice. A specific chat-model identifier and context/output/token/cost budgets remain unresolved and must be selected before enabling answer generation. Provider timeouts, safe error mapping, and bounded inputs are required; detailed numeric model budgets should not be invented in these docs.

## 6. Security, configuration, and testing

- Validate request schemas, file type and size, filenames, PDF pages, extracted text, and question input. Do not trust client-supplied MIME type or file paths.
- Use Pydantic Settings for environment-based configuration and document required variables with a non-secret example. Keep OpenAI keys in backend-only environment configuration, exclude real secrets from source control, and fail safely if required credentials are missing.
- Require explicit permission to send a document to an external provider before making OpenAI calls. Exact UX/copy and recording details can be finalized during implementation; upload itself is not consent.
- Treat uploaded and retrieved text as untrusted. Do not expose secrets, stack traces, document contents, or raw provider bodies in errors/logs.
- Implement safe error handling and deletion/vector cleanup.
- Add API and core pipeline tests for input limits, failures, ingestion, retrieval, citations, abstention, and deletion cleanup. These tests are planned; the current scaffold's health test does not establish coverage of these behaviors.

Advanced observability is excluded. Basic application logs and safe error codes are implementation needs, not an observability subsystem.

## 7. Explicitly superseded or excluded decisions

Older architecture/decision text described a team application with MongoDB/GridFS, Redis/ARQ, separate workers, managed authentication, workspaces, asynchronous jobs, SSE, and larger operational infrastructure. Those choices are superseded by the approved MVP scope and must not be treated as active requirements.

Excluded from MVP: MongoDB, GridFS, Redis, ARQ, managed authentication, multi-workspace support, background workers, reranking, SSE streaming, microservices, Kubernetes, and advanced observability. Also out of scope: OCR, hybrid retrieval, additional model providers, answer caching, production deployment, and organization administration. Do not add dependencies or services for these features.

## 8. Seven-day implementation roadmap

1. **Day 1 — Foundation:** configure environment/secret handling; establish modular monolith boundaries, SQLite access, local storage paths, and Docker Compose for Qdrant.
2. **Day 2 — Upload and validation:** implement API schemas and metadata; validate PDF/TXT/Markdown, safe filenames, 20 MiB uploads, PDF pages, and persist source files.
3. **Day 3 — Ingestion:** add extraction and normalized-text limits, page-aware chunking with 700/100 defaults, OpenAI embeddings, Qdrant indexing, and ready/failed state handling.
4. **Day 4 — Question answering:** add query validation, vector retrieval, configured OpenAI LLM answers, citation validation, and basic abstention.
5. **Day 5 — Frontend:** connect document upload/list/delete and question/answer/citation screens with loading and error states.
6. **Day 6 — Lifecycle and tests:** finish recoverable deletion and vector cleanup; add API and core pipeline tests for validation, failures, ingestion, citations, and abstention.
7. **Day 7 — Integration review:** exercise the complete local workflow, fix MVP blockers, review secret/configuration handling, document limitations, and report actual completion evidence.

This is a plan, not a status report. Planned features must not be described as implemented until code and relevant checks demonstrate that they are.

## 9. Remaining implementation decisions

- Select a specific OpenAI chat model and bounded context, output, and cost budgets before enabling generation.
- Select and validate a tokenizer for chunk sizing and the 100,000-token input limit.
- Define and obtain owner approval for a bounded overall ingestion-request budget before implementation. It must bound the synchronous upload-to-index path in addition to the existing extraction limit and provider timeouts; do not change those existing limits or invent timeout values here.
- Choose Qdrant collection configuration and client timeout values during implementation. The SQLite path and initial metadata schema are recorded above. Keep secrets out of committed configuration.
- Define the initial document status when the upload lifecycle is implemented; the current schema intentionally has no status default or enumerated constraint.
- Finalize the minimal consent prompt/recording behavior before sending user documents to OpenAI.
- Define concrete API response/error shapes and a cleanup retry interaction while implementing the workflow.

These details do not change the approved architecture or reintroduce excluded infrastructure. The current documentation does not claim they have already been decided or implemented.
