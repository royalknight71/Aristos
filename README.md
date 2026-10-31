# Aristos — Engineering Knowledge Copilot

Aristos is a single-user Engineering Knowledge Copilot. Its MVP lets one user upload PDF, TXT, and Markdown documents, ask questions, retrieve relevant passages, and receive answers grounded in those passages with citations. It abstains when the available evidence is insufficient.

## MVP status

The current scaffold contains a FastAPI health endpoint and a minimal React landing screen. Upload, ingestion, retrieval, question answering, citations, abstention, and document deletion are **planned**; they are not yet implemented. The roadmap below describes planned work, not completed functionality.

## MVP technology

| Area | Technology |
|---|---|
| Web client | React, TypeScript, Vite, Tailwind CSS |
| API and application | Python, FastAPI, Pydantic |
| Metadata and document state | SQLite |
| Original files | Local file storage |
| Vector retrieval | Qdrant |
| Embeddings and answer generation | OpenAI embeddings and LLM |
| Local services | Docker Compose |

The backend is a modular monolith. Ingestion runs synchronously in the API process; the MVP has no background worker or job broker. SQLite and local files keep a single-user local deployment simple to run, inspect, and back up. Qdrant holds derived vectors and can be rebuilt from retained source files. OpenAI credentials are backend-only configuration and must not be committed or sent to the browser.

## Planned document and question flow

1. Validate the upload type, size, PDF page count, and extracted content limits.
2. Store the source file locally and its metadata/state in SQLite.
3. Extract text, preserve PDF page references where available, split it into chunks, request OpenAI embeddings, and synchronously write vectors to Qdrant. Report the document ready only after indexing succeeds.
4. For a question, embed the query, retrieve relevant Qdrant passages, and ask the OpenAI LLM for an answer grounded in those passages.
5. Validate every cited passage against the retrieved results. Return answer text and structured citations; abstain if evidence is insufficient.
6. On deletion, remove the document's Qdrant vectors and local source, and update SQLite state. Surface cleanup failures rather than reporting successful deletion while vectors remain.

These flows are planned, not implemented. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for module boundaries, failure handling, and detailed data flow.

## Preserved processing defaults

- Accept PDF, TXT, and Markdown only; maximum upload size is 20 MiB.
- Maximum PDF length is 300 pages; extraction timeout is 60 seconds.
- Maximum normalized text is 1 MiB UTF-8 and 100,000 counted input tokens per document, whichever comes first. Reject over-limit files; do not silently truncate them.
- Start with 700-token chunks and 100-token overlap. These remain configurable experimental defaults, not a claim of optimal retrieval quality.
- Start with OpenAI `text-embedding-3-small`; keep the embedding model configurable. Select the chat model and generation budgets before enabling answer generation.

## Local development

The repository currently has a backend health endpoint and a frontend scaffold. Docker Compose is the planned way to run local infrastructure such as Qdrant; the exact compose configuration is part of implementation work.

### Backend scaffold

```powershell
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

The API scaffold runs at `http://127.0.0.1:8000`; `GET /health` returns `{"status":"ok"}`. These commands describe the current scaffold only.

### Frontend scaffold

```powershell
cd frontend
npm ci
npm run dev
```

## Security and quality

The MVP must validate all input, enforce configured upload and extraction limits, return safe errors, and keep OpenAI secrets out of source control and browser code. Require explicit user consent before sending document content to OpenAI for embedding or answer generation; uploading a file alone is not consent. Uploaded documents and retrieved passages are untrusted content. Citation identifiers must be checked against retrieved passages, and the answer path must abstain when evidence is inadequate.

Document deletion must clean up both local source files and Qdrant vectors, with recoverable state for partial failures. Planned verification includes API tests and core pipeline tests for validation, ingestion, retrieval, citations, abstention, errors, and deletion cleanup. The current scaffold only includes a health endpoint test; the MVP tests are not yet implemented.

## Seven-day MVP roadmap

1. **Day 1 — Foundation:** confirm configuration and secret handling; establish modular-monolith boundaries, SQLite access, local storage paths, and Docker Compose for Qdrant.
2. **Day 2 — Upload and validation:** define document API/schema and SQLite metadata; validate PDF/TXT/Markdown, size, page count, and safe filenames; persist source files.
3. **Day 3 — Synchronous ingestion:** implement extraction, normalization, chunking with preserved defaults, OpenAI embeddings, Qdrant indexing, and accurate ready/failed states.
4. **Day 4 — Retrieval and answers:** implement question validation, vector retrieval, grounded LLM answers, citation validation, and basic abstention.
5. **Day 5 — User workflow:** connect the React UI for upload, document listing/deletion, question entry, answers, citations, loading, and error states.
6. **Day 6 — Lifecycle and tests:** implement deletion with vector cleanup and failure reporting; add API and core pipeline tests for limits, errors, citations, abstention, and cleanup.
7. **Day 7 — Integration and review:** run the end-to-end local workflow, fix MVP blockers, review configuration/secret handling and documentation, and record known limitations.

The roadmap is a plan; no day or feature should be marked complete until implementation and its relevant checks are actually done.

## License

No `LICENSE` file is present, and a project license has not yet been selected.
