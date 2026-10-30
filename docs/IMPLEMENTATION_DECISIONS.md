# Aristos Implementation Decisions

**Status:** The owner-approved MVP baseline is recorded below. Chat model/budget, external-processing consent details, and retention/deletion policy remain open. Other unapproved recommendations are labeled as proposals and are not implementation defaults.

**Prepared:** 2026-10-30

## 1. Purpose and scope

This document records owner-approved MVP implementation decisions and distinguishes them from implementation details that remain open in [the approved architecture](ARCHITECTURE.md) and [README](../README.md). It preserves rationale and operational implications before application scaffolding begins.

It does not authorize implementation, select a chat model, claim any planned capability is implemented, or change the approved technology stack. Do not treat an open decision or a recommendation explicitly labeled as a proposal as approved.

## 2. Existing approved architectural constraints

The following are treated as approved constraints, not recommendations made here:

- Frontend: React, TypeScript, Vite, and Tailwind CSS.
- Backend: Python and FastAPI in a modular monolith, with an ingestion worker.
- MongoDB is the application system of record; GridFS stores original documents in the MVP.
- Qdrant stores derived chunk vectors and payloads.
- Redis + ARQ is used only to dispatch asynchronous ingestion work. It is not an answer cache. MongoDB remains authoritative for job and document state.
- OpenAI calls stay behind provider adapters. `text-embedding-3-small` is the owner-approved initial embedding model and remains configurable; the chat model is configurable and no chat model identifier is selected.
- The initial upload limit is 20 MiB and is configurable. PDF, Markdown, and TXT are the supported initial formats.
- 700-token chunks and 100-token overlap are experimental initial settings, not proven optimal values.
- Retrieval starts with dense vector search and metadata filters. Add reranking only if evaluation shows a need.
- Citation IDs are validated against retrieved chunks, and the system abstains when retrieved evidence is insufficient.
- External AI processing requires permission to share the document. Upload alone is not consent.
- Public access is gated on vetted authentication and workspace authorization. A development identity is local-only.
- Re-indexing and deletion must be idempotent, recover from partial failures, and clean up MongoDB/GridFS and Qdrant consistently.

### Owner-approved MVP implementation baseline

The project owner has approved these decisions for the MVP:

- Python 3.14, using the latest compatible patch after dependency compatibility checks.
- Node.js 24 LTS, npm, and a committed `package-lock.json`.
- Managed authentication direction, with Supabase Auth as the leading candidate and Auth0 as an alternative. Validate the final provider integration before implementation.
- MongoDB memberships as the source of truth for workspace roles; initial roles are `owner` and `member`.
- `text-embedding-3-small`, configurable through the provider abstraction.
- PDF, Markdown, and TXT uploads; a configurable 20 MiB maximum upload size; a 300-page PDF limit; a 60-second extraction timeout; and a normalized text limit of 1 MiB UTF-8 and 100,000 counted input tokens per document. Reject oversized documents; do not silently truncate.
- ARQ job timeout of 900 seconds, five total attempts, retry delays of 5, 10, 20, and 40 seconds with bounded exponential backoff, jitter, and `Retry-After` handling; initial worker concurrency of 2; a 60-second shutdown grace period; and MongoDB reconciliation at startup and every 60 seconds.
- An evaluation baseline of 8–10 documents and approximately 30 labeled answerable, ambiguous, and unanswerable questions; retrieval metrics of Recall@5, Recall@10, Precision@5, MRR, and nDCG@10; and manual review of answer relevance, groundedness, citation correctness, and abstention behavior.

These approvals do not select a chat model or approve a numeric chat-generation budget, consent UX/policy details, or a final retention/deletion policy.

### Existing-document discrepancy

`ARCHITECTURE.md` includes an earlier repository snapshot saying the branch was `feature/architecture-blueprint` and that README/`.gitignore` still contained PowerShell here-strings. That snapshot is stale relative to the current project context and the reviewed README. It does not affect the architecture decisions above. The repository's current branch is supplied as `chore/implementation-decisions`; no Git state was inspected for this document.

## 3. Decision analysis

### 3.1 Runtime versions and frontend package manager

**Decision topic:** Python, Node.js, and frontend package manager.

**Available options:** Use the newest released runtime lines immediately; use the latest mature supported lines; or pin older runtimes for broad compatibility.

**Approved option:** Python 3.14 using the latest compatible patch after dependency compatibility checks, and Node.js 24 LTS with npm. Commit `package-lock.json`; use npm as shipped with Node rather than managing a separate global npm. Keep the approved major/minor runtime selections in repository version files when scaffolding is authorized; update patches for security fixes, subject to compatibility.

As of 2026-10-30, Python 3.14.10 is the latest 3.14 patch and the 3.14 series is in bug-fix support through October 2030. Python 3.15.2 has just been released, so 3.14 is the more conservative dependency-compatibility baseline for a new project. [Python 3.14.10 release](https://www.python.org/downloads/release/python-31410/), [Python version status](https://devguide.python.org/versions/). Node 24.22.2 is a supported LTS patch, with the line scheduled for support through April 2028. Node 26 has also just entered LTS; choosing 24 favors additional ecosystem maturity while still having meaningful support runway. The current Vite guide requires Node 20.19+ or 22.12+, which Node 24 satisfies. [Node release schedule](https://nodejs.org/en/about/previous-releases), [Vite requirements](https://vite.dev/guide/). npm is available with the Node.js distribution; use that bundled version and lock the project dependency graph instead of independently managing a global npm version. [Node.js downloads](https://nodejs.org/en/download).

FastAPI and Pydantic v2 are the planned Python web/validation stack. Python 3.14 is a stable bug-fix series, but the final dependency set (including PyMuPDF and Qdrant/MongoDB clients) must be smoke-tested on it before locking. Do not fall back to an older Python line without recording the compatibility reason.

**Reasoning:** Supported runtime lines avoid end-of-life releases; the selected versions meet current Vite requirements and balance support runway with ecosystem maturity. npm is the lowest-friction package manager for an individual developer. The owner approved these runtime lines; the compatibility check is a technical prerequisite, not a request to change the baseline silently.

**Trade-offs:** Python 3.15 and Node 26 offer newer runtime features but are newer dependency targets. Node 24's published support window is shorter than Node 26's. npm is familiar but less disk-efficient than pnpm for large monorepos; Aristos has one frontend package, so pnpm's workspace benefits do not justify another tool yet.

**Human approval required:** No further approval for the selected runtime lines or package manager. If the dependency compatibility check fails, report the conflict and request owner direction before changing the baseline.

**Configurable:** Runtime line is pinned per repository after approval, not changed by application settings. Patch versions should be updated regularly.

### 3.2 Authentication and workspace authorization

**Decision topic:** Managed authentication provider versus self-managed FastAPI authentication.

**Available options:** A managed OIDC/auth provider such as Supabase Auth or Auth0; a self-managed login/session flow implemented in the FastAPI application using vetted libraries; or local development identity only, which is not suitable for public use.

**Approved direction:** Use managed authentication, with Supabase Auth as the leading candidate and Auth0 as an alternative. Final provider integration must be validated before implementation. The React client obtains the provider session; FastAPI verifies tokens with a maintained library and trusted signing keys; MongoDB `memberships` remains the authoritative workspace/role authorization source. The identity provider authenticates a person; it does not decide which Aristos documents or conversations that person may access. Initial approved workspace roles are `owner` and `member`.

Supabase currently lists 50,000 monthly active users in its Free plan, but Free projects pause after one week of inactivity and have shorter log retention. Auth0 currently lists up to 25,000 MAUs in Free and five Organizations, while per-organization RBAC appears in its paid Essentials tier. These plan details can change and should be rechecked at provider selection. [Supabase pricing](https://supabase.com/pricing), [Supabase billing details](https://supabase.com/docs/guides/platform/billing-on-supabase), [Auth0 pricing](https://auth0.com/pricing). Supabase documents asymmetric JWKS-based JWT verification and recommends a trusted verification library rather than hand-rolled signature logic. [Supabase JWT verification](https://supabase.com/docs/guides/auth/jwts).

**Reasoning:** Managed authentication reduces password handling, reset flows, email verification, MFA, abuse defenses, and session lifecycle work. It leaves the portfolio project focused on authorization boundaries and the RAG system. Keeping workspace ownership and roles in MongoDB avoids making vendor-specific organization features the authorization source.

**Trade-offs:** A managed provider adds an external dependency, provider configuration, possible free-tier limitations, and some vendor coupling. Supabase's paused-project behavior may be inconvenient for an infrequently used demo. Auth0's per-organization role feature may require payment. Self-managed FastAPI auth avoids a provider account and per-MAU pricing, but makes the project responsible for password storage, account recovery, verification, session/token security, rate limiting, MFA decisions, and ongoing security maintenance. A local development identity is useful for isolated development but cannot be exposed publicly.

**Human approval required:** The managed-auth direction and initial roles are approved. Validate provider integration before implementation and return to the owner if compatibility, provider terms, or required capabilities conflict with this direction. Defer finer-grained roles.

**Configurable:** Provider issuer/audience and client settings are deployment configuration. Workspace roles and authorization rules are application policy, not arbitrary runtime toggles.

### 3.3 AI model configuration, token budgets, and failures

**Decision topic:** Embedding/chat model configuration and provider-call behavior.

**Available options:** Use the architecture's proposed `text-embedding-3-small` with a configurable chat model; or select different models later based on evaluation, price, and quality. Keep provider SDK calls in the approved OpenAI adapters; do not add a second provider or a generalized multi-provider framework for the MVP.

**Approved embedding / open chat choice:** Use the approved `text-embedding-3-small` setting and validate availability/account access during implementation. OpenAI's current API model documentation lists this model, 1,536 default vector dimensions, an 8,192-token input limit, and usage-based input pricing; the model name, dimensions, and price are provider facts to re-check at implementation and index creation. [Embedding model documentation](https://developers.openai.com/api/docs/models/text-embedding-3-small), [Embeddings guide](https://developers.openai.com/api/docs/guides/embeddings). Do not choose a chat-model identifier in this document. Require one through validated configuration before enabling chat.

Chat-generation model, context/output/question token budgets, and cost limits remain open; this document does not set numeric values for them. Once a chat model is selected, derive configurable application caps from its then-current documented limits and the owner's budget. Keep the 700-token/100-token chunk defaults configurable and experimental. The separately approved ingestion cap is 100,000 counted input tokens and 1 MiB of normalized UTF-8 text per document, whichever is reached first. Use one tokenizer consistently for chunking and ingestion token accounting; tokenizer choice remains open.

Set explicit provider timeouts instead of inheriting long SDK defaults. Proposed, not yet owner-approved starting bounds: 5-second connect timeout; up to 60 seconds for an embedding request; for streamed chat, 30 seconds to first response and 60 seconds with no stream activity. On 408/429/5xx and connection failures, respect `Retry-After` when reasonable and use bounded exponential backoff with jitter. Do not retry invalid request, authentication, permission, or other permanent 4xx failures. The current OpenAI Python SDK documentation describes two automatic retries by default and a 10-minute default timeout; explicitly configure SDK retries so they do not multiply ARQ retries. Proposed SDK policy: let the approved ARQ job policy own ingestion retries and set provider-level retries to zero or one. For chat, allow at most one retry before the first streamed token; never silently replay after tokens have been sent. [OpenAI Python SDK retries and timeouts](https://github.com/openai/openai-python/blob/main/README.md).

**Reasoning:** Explicit caps bound context size, latency, and variable token cost. Provider adapters centralize model configuration, timeouts, retries, usage extraction, and error translation. Capturing request IDs and usage supports incident review without logging document contents.

**Trade-offs:** Conservative caps can reject large documents or omit useful context. A tokenizer dependency and model-specific budget checks add implementation work. Retrying streaming generation after partial output risks duplicate or contradictory text, so a failed stream should terminate with a stable error and let the user retry the turn.

**Human approval required:** Chat model selection and all chat-generation cost/token budgets remain open and require explicit approval. Provider timeout/SDK retry values above are proposals to validate during integration. The embedding model is owner-approved; verify provider access, dimensions, and current settings before implementation. The per-document ingestion limits are owner-approved.

**Configurable:** Yes: model identifiers, dimensions/index version, token caps, request timeouts, and retry settings. Do not hardcode a chat model ID.

### 3.4 Explicit external-provider sharing permission

**Decision topic:** How users authorize sending document content to OpenAI.

**Available options:** Per-upload consent; workspace-wide policy; an explicit document-level `external_processing_allowed` state; or a combination. Uploading by itself is never consent.

**Open decision; candidate approach only:** The implementation must fail closed and must obtain permission before any external provider call; upload alone is never consent. Options include an unchecked per-upload confirmation, a workspace-level allow/deny policy, and a document-level external-processing restriction. One candidate is to combine per-upload confirmation with a workspace-level veto and document-level denial, but this flow, exact UI, wording, policy precedence, and resulting state are not approved. Until those details are approved and implemented, no content may be sent externally.

An auditable record of the permission decision is required, but its fields, retention, consent wording/versioning, revocation behavior, and external-processing policy remain open. Do not store file contents in an audit event. Check current permission immediately before every provider call and fail closed when permission is absent or denied. The handling of existing indexes and previously processed content after a revocation requires owner approval. Documents that must never leave the user's environment cannot be indexed by this OpenAI-only MVP; explain the limitation and do not silently process them.

**Reasoning:** A per-document confirmation prevents a broad workspace setting or upload action from being mistaken for consent. A separate workspace policy gives administrators a way to disable external processing for all members. Document-level denial is fail-closed.

**Trade-offs:** Consent prompts add friction and a permission state complicates retries/re-indexing. Consent does not establish that the user has legal authority to share a file, and this design makes no legal compliance claim. A local-only processing mode would require a separately approved provider/architecture and is deferred.

**Human approval required:** Yes. Exact consent UX and copy/versioning, workspace policy and precedence, denial behavior, revocation effects on already indexed data, and audit retention all remain open owner decisions.

**Configurable:** The exact settings and persisted policy schema remain open with the consent UX decision. Do not hardcode consent policy or provide a production bypass; record the approved provider/purpose and permission decision without storing document content.

### 3.5 Upload and document limits

**Decision topic:** File types, file size, PDF pages, extraction time, and extracted text cap.

**Available options:** Enforce only the architecture's 20 MiB file limit; add page/text/time ceilings; or accept larger inputs and depend on provider/API timeouts. Continue to support only PDF, Markdown, and TXT initially.

**Approved option:** Use the following owner-approved, configurable limits:

| Limit | Owner-approved MVP limit | Reason |
|---|---:|---|
| Supported formats | PDF, Markdown, TXT | Approved initial scope; no archive, OCR, or office-file parsing. |
| PDF pages | 300 pages per file | Bounds CPU, memory, extraction time, and embedding volume while handling typical engineering manuals. |
| Extraction wall time | 60 seconds per document | Extraction happens in a worker, so it does not occupy an upload request; pathological files still terminate. |
| Normalized text | 1 MiB UTF-8 and 100,000 counted input tokens, whichever comes first | Bounds memory and maximum embedding calls/cost. |
| Upload bytes | 20 MiB | Approved architecture default; enforce at ingress and application layers. |

Reject a file that exceeds any cap with a stable error code and a clear message; do not silently truncate technical content and then present the result as complete. Count PDF pages before extraction when possible, check extracted size while streaming/processing, and stop work promptly when a limit is reached. These limits are approved; the exact user-facing error wording remains an implementation detail.

**Reasoning:** A small portfolio MVP can process typical engineering docs without risking unbounded CPU, memory, queue time, or embedding spend. Worker-side extraction avoids holding an HTTP request open. The token cap controls cost more directly than bytes alone.

**Trade-offs:** Some long manuals will be rejected and need splitting by the user. Tokenization adds a dependency or implementation decision. PDF text extraction may still lose table structure or reading order; caps do not solve OCR or layout fidelity.

**Human approval required:** No; formats and all limits in this section are owner-approved. Any proposed increase or silent-truncation behavior would require renewed approval.

**Configurable:** Yes, with validated bounds. Persist the effective values/version used on ingestion records to explain results and support re-indexing.

### 3.6 Retention and deletion

**Decision topic:** How long each stored category remains and how deletion works across stores.

**Available options:** Retain until explicit deletion; set fixed automatic expiration; or combine user deletion with bounded retention of minimal audit/tombstone metadata. The stores do not share a transaction, so deletion is a retryable saga, as specified in the architecture.

**Open decision; recommended policy principles, with periods and user-visible behavior still subject to approval:**

| Data | Recommended MVP policy |
|---|---|
| Original file in GridFS | Retain while the document is active. On user/workspace deletion, immediately make it unavailable and enqueue deletion. Retry until GridFS removal is confirmed. Failed-ingestion source retention period remains open; retain only while an approved retry policy allows recovery. |
| Document metadata | Keep while active. During incomplete cleanup, retain only the minimum tombstone needed for reconciliation (IDs, cleanup state, timestamps, safe error code). When to purge completed tombstones remains open. Never retain names/content hashes longer than the approved purpose requires. |
| Qdrant chunks | Keep only active versions; remove all old/partial/active versions on document deletion. Retry cleanup until point counts/filters confirm removal. Never treat Qdrant as the source of truth. |
| Conversations and messages | Retention period and user controls remain open. Decide whether document deletion removes stored citation passages, preserves references as deleted, or cascades to conversations. Explain that answer text may itself contain document-derived content. |
| Failed jobs | Keep only safe operational state and error code; never store document text, credentials, or full provider payloads in job records. Purge timing remains open and must allow cleanup/reconciliation to finish. |
| Consent/security audit events | Retain metadata-only events, never document contents or secrets. Retention period and deletion behavior remain open; no legal retention requirement is assumed. |

Deletion order is an approved safety constraint: mark the document unavailable in MongoDB; cancel/supersede pending ingestion jobs; delete Qdrant points for every index version; remove GridFS bytes; update cleanup progress after each successful operation; retain a minimal tombstone while cleanup is incomplete. If any step fails, leave `deleting` or `cleanup_pending`, log a safe error, and retry idempotently. Reconciliation must find missing queue deliveries and incomplete cleanup. The final purge timing and treatment of citation snapshots/messages after document deletion remain open.

**Reasoning:** Source and vector cleanup is essential to make deletion meaningful; minimal tombstones enable recovery without keeping content. Explicitly handling citation snapshots avoids silently retaining deleted source passages in chat history.

**Trade-offs:** Preserving answer text after removing citations can still retain document-derived information. Cascading conversation deletion is simpler for privacy but can remove unrelated context. Any fixed retention period can surprise users and must be explained. No retention duration is selected here and no legal retention requirement is assumed.

**Human approval required:** Yes. Final retention periods and deletion policy remain open, including failed-file retention, tombstone purge, chat/citation redaction, audit retention, and whether account deletion cascades to owned workspace data.

**Configurable:** Retention durations and deletion policies should be settings. A user-level deletion request must not be disabled by a configuration toggle.

### 3.7 Redis + ARQ operational settings

**Decision topic:** Queue timeout, attempts/backoff, idempotency, concurrency, shutdown, failed jobs, and reconciliation.

**Available options:** Use ARQ defaults; configure bounded retry and job settings; or build a separate queue/stream. The architecture approves Redis + ARQ, with MongoDB authoritative.

**Approved option:** Use this configurable policy:

| Setting | Owner-approved MVP setting |
|---|---:|
| ARQ per-attempt job timeout | 900 seconds |
| Attempts | 5 total (first attempt plus at most 4 retries) |
| Retry delays | Exponential: 5, 10, 20, 40 seconds; add jitter, respect reasonable `Retry-After` values, and use a configurable ceiling (ceiling value not selected) |
| Worker concurrency | 2 simultaneous jobs locally; configurable by available memory/CPU |
| Shutdown grace | 60 seconds to stop claiming work and finish/cleanly cancel active tasks; interrupted work is re-enqueued after lease recovery |
| Reconciliation | At startup and every 60 seconds, in bounded MongoDB batches |
| Idempotency key | Stable document ID + target index version; deterministic Qdrant point IDs per chunk |

Persist each state transition, attempt count, lease/heartbeat, next-attempt time, and safe failure code in MongoDB. Claim jobs atomically with a lease. Treat ARQ as at-least-once delivery: duplicate jobs must not duplicate active vectors or switch a partial index into service. MongoDB is authoritative if Redis loses queued jobs or ARQ results. Reconciliation re-enqueues eligible MongoDB jobs missing from Redis, recovers expired `running` leases, and retries incomplete deletion/index cleanup. A terminal ARQ failure updates the MongoDB job to `failed`; expose a manual retry as a new recorded attempt. Keep ARQ results short-lived or disabled; do not store document contents in Redis.

Retry transient Redis/network/provider/5xx/timeouts and partial storage failures. Do not retry unsupported file, consent denial, invalid input, auth/configuration errors, or other permanent 4xx failures. ARQ's documented defaults include `job_timeout=300`, `max_tries=5`, and `max_jobs=10`; its retry mechanism supports a deferred retry interval, so configure explicit values instead of inheriting defaults. [ARQ worker settings and retry docs](https://arq-docs.helpmanual.io/).

The owner-approved limit is five total executions: one initial execution plus at most four retries. Before implementation, verify the selected ARQ version's actual `max_tries` semantics and configure it to produce exactly five total executions. Do not assume that `max_tries=5` means five total attempts or five retries without checking the installed version and confirming behavior with a focused retry test.

**Reasoning:** Fifteen minutes allows bounded extraction and several provider batches without allowing jobs to run forever. Low local concurrency keeps student hardware responsive. Mongo-led reconciliation handles Redis/worker interruption without a second queue system.

**Trade-offs:** A five-attempt ceiling can still leave jobs failed during a long provider outage; manual retry and visibility are required. Frequent reconciliation adds Mongo reads, so use indexes and bounded batches. A 60-second shutdown grace will not finish every large ingestion; correctness relies on idempotent restart, not keeping a process alive indefinitely.

**Human approval required:** No further approval for the listed timeout, five-attempt limit, 5/10/20/40-second retry delays, jitter/`Retry-After` behavior, local concurrency, shutdown grace, or reconciliation cadence. Select a finite configurable retry ceiling during implementation and record the value. Alert thresholds are also unspecified.

**Configurable:** Yes. MongoDB remains the source of truth even when settings change.

### 3.8 Evaluation and observability

**Decision topic:** Minimum useful quality and operations measurement without building a large evaluation platform.

**Available options:** Manual ad hoc review; a small fixed labeled set run locally; or a larger evaluation service/model-judge pipeline.

**Approved option:** Begin with 8–10 permitted documents and approximately 30 labeled questions covering answerable, ambiguous, and unanswerable cases. Label relevant chunks and expected citation spans by hand. Report Recall@5, Recall@10, Precision@5, MRR, and nDCG@10. Manually evaluate answer relevance, groundedness, citation correctness, and abstention behavior using a short rubric. Do not use an LLM judge as the MVP acceptance authority.

Proposed observability signals (thresholds remain open): p50/p95 ingestion duration, retrieval latency, first-token and total generation latency, embedding/generation token use, estimated provider cost, job age/failure/retry counts, and stream completion/disconnect counts. Use structured logs with request ID, job ID, workspace/document IDs where access-controlled, provider request ID, model/index/prompt version, latency, token counts, and stable error code. Never log document content, prompts (complete or partial), access tokens, API keys, secrets, or raw provider bodies. Cross-workspace isolation and citation authorization/validation remain release-blocking integration tests, not just aggregate metrics.

**Reasoning:** A small fixed set is feasible for one student and catches regressions in retrieval, grounding, citations, and abstention. Operational metrics reveal whether quality changes come with unacceptable latency or spend.

**Trade-offs:** Thirty questions do not establish general performance. Human rubric scoring costs time and may vary between reviewers. Estimated cost can differ from invoices; compare usage counters with provider billing.

**Human approval required:** The baseline size, coverage, metrics, and manual evaluation dimensions are approved. The actual documents must be permitted for evaluation, and numerical release-blocking quality/latency/cost thresholds remain to be defined.

**Configurable:** Evaluation k-values and latency/cost budgets should be recorded with each run; core metrics should stay stable between comparisons.

## 4. Owner-approved MVP baseline and remaining defaults

| Area | Baseline | Status |
|---|---|---|
| Runtime | Python 3.14 latest compatible patch after dependency checks; Node.js 24 LTS; npm; committed `package-lock.json` | Owner-approved; compatibility check remains required |
| Authentication and authorization | Managed authentication direction; Supabase Auth leading candidate, Auth0 alternative; MongoDB memberships; `owner` and `member` roles | Owner-approved direction; validate final provider integration before implementation |
| Embeddings | `text-embedding-3-small`, configurable through provider abstraction | Owner-approved; verify provider access and dimensions at implementation |
| Chat generation | No identifier or numeric token/cost budget selected; model and budgets must be configurable | Open; requires owner decision |
| Upload formats and size | PDF, Markdown, TXT; maximum 20 MiB | Owner-approved; size remains configurable |
| PDF and extraction | 300 pages; 60-second extraction timeout | Owner-approved; configurable |
| Normalized document text | 1 MiB UTF-8 and 100,000 counted input tokens per document; reject, do not truncate | Owner-approved; configurable |
| Chunking | 700 tokens / 100 overlap, configurable and experimental | Previously owner-approved; not asserted optimal |
| Ingestion worker | ARQ timeout 900 seconds; 5 total attempts; 5/10/20/40-second retry schedule with bounded backoff, jitter, and `Retry-After`; concurrency 2; shutdown grace 60 seconds | Owner-approved; settings remain configurable |
| MongoDB reconciliation | At startup and every 60 seconds | Owner-approved; use bounded batches |
| Evaluation | 8–10 documents; approximately 30 labeled answerable/ambiguous/unanswerable questions; Recall@5, Recall@10, Precision@5, MRR, nDCG@10; manual answer/grounding/citation/abstention review | Owner-approved baseline; actual data must be permitted; release thresholds remain open |
| Consent details | Explicit permission required before each provider call; exact UX, wording/version, policy, and revocation behavior not selected | Open; requires owner decision |
| Retention and deletion | Safe, idempotent cleanup remains required; retention periods and final chat/audit/deletion policy not selected | Open; requires owner decision |

Owner-approved values are the MVP baseline, not claims that implementation exists. Keep approved limits configurable as specified, validate them server-side, and do not change them without recording owner approval. Do not assign final values to open chat budgets, consent details, or retention policy.

## 5. Security and privacy implications

- Keep all public user routes disabled until the vetted identity provider, token verification, and MongoDB workspace authorization checks are implemented and tested.
- Authenticate identity in the provider; authorize workspace membership and roles in Aristos. Every MongoDB, GridFS, Qdrant, conversation, and citation lookup must be scoped to the authorized workspace.
- Require explicit document sharing permission before any OpenAI call. Recheck it before embedding and before using document passages for answer generation. Fail closed if the permission record is missing or revoked. The exact consent mechanism and revocation effects remain open; until approved and implemented, no content may be sent externally.
- Keep provider secrets server-side. Use allowlisted configuration, secret storage, request limits, and redacted structured logs.
- Treat uploaded content and retrieved passages as untrusted. No tools/actions are exposed to the model in the MVP; validate all returned citation IDs and abstain when evidence is insufficient.
- Use bounded uploads, extraction time, extracted text, job concurrency, query/context/output tokens, and provider retries to limit resource and cost exposure.
- Do not claim a regulatory compliance posture. Consent copy, retention, and provider data handling need owner review before public launch.

## 6. Operational implications

- **Configuration:** Runtime settings, models, budgets, upload/extraction caps, queue policy, and retention values should come from validated configuration. Exact environment variable names are not defined by the approved docs and should be selected in the implementation plan; this document does not invent them.
- **Compatibility:** Before scaffolding is considered ready, run a minimal dependency compatibility check on the approved Python and Node lines, including PyMuPDF, FastAPI/Pydantic, MongoDB/Qdrant clients, OpenAI SDK, React, TypeScript, and Vite. Pin dependency ranges and lock frontend dependencies.
- **Cost:** Capture embedding and chat token use by workspace/document/request. Set operational quotas and provider-account alerts/limits where available. A model's price and account tier may change, so review provider pricing at implementation and before release.
- **Failure handling:** Distinguish retryable provider/network errors from permanent validation/auth/consent failures. Return safe stable API errors; do not expose prompts, file content, or provider response bodies.
- **Deletion:** Model cleanup as a persisted state machine with idempotent operations and reconciliation, not a best-effort sequence hidden in a request handler.
- **Release gate:** Public deployment requires approved authentication, workspace isolation tests, explicit consent handling, retention behavior, operational limits, and an evaluation baseline.

## 7. Decisions requiring human approval

The following remain open and must be decided before the related feature begins:

1. **Chat model and generation budgets:** Select the chat model and set context, output, question, and cost controls after reviewing the selected model's current limits and pricing. No numeric chat-generation budget is approved here.
2. **External-processing permission:** Approve consent UX and wording/versioning, workspace/document policy precedence, denial behavior, revocation effects on already indexed content, and consent audit details. The requirement to check permission before every provider call is already approved.
3. **Retention and deletion:** Approve final retention periods and deletion semantics for failed uploads/jobs, document tombstones, citation snapshots and chat history, consent/security audit records, and workspace/account deletion.

The managed-auth direction and runtime baseline are approved, but final provider integration and Python dependency compatibility must be validated before implementation. Evaluation baseline and release metrics are approved; actual evaluation data must be permitted, and numerical pass/fail thresholds remain to be defined.

## 8. Deferred decisions

- Exact FastAPI, Pydantic, React, TypeScript, Vite, Tailwind, OpenAI SDK, PyMuPDF, MongoDB/Qdrant client, and ARQ package versions. Select compatible current releases when dependency manifests are created; do not prematurely pin package versions here.
- Exact environment variable names and local secret injection mechanism.
- Fine-grained roles, organization administration, invitations, and enterprise SSO.
- Local/on-prem AI processing for documents that cannot be sent externally.
- OCR, table extraction, hybrid retrieval, reranking, model fine-tuning, answer caching, and additional AI providers.
- Production hosting, object storage migration, backups, dashboards, and deployment automation.
- Automatic conversation expiry beyond the proposed user-initiated deletion policy.

## 9. Readiness checklist for application scaffolding

The owner-approved baseline is recorded in Sections 2–4. Open decisions gate the features they affect; they do not all block repository scaffolding or independent foundational infrastructure. After runtime/dependency compatibility validation and a separate owner implementation instruction, work may begin on the repository skeleton, shared configuration/logging/error foundations, and local infrastructure that does not expose public routes or send document content to an external provider.

- [ ] Verify the selected dependency set is compatible with Python 3.14 and record the latest compatible patch. Use Node.js 24 LTS/npm and commit `package-lock.json` when scaffolding is authorized.
- [ ] Scaffold independent repository/backend/frontend foundations and local infrastructure under the owner's implementation instruction. Keep public user routes disabled until managed authentication and MongoDB workspace authorization are validated.
- [ ] Validate the selected managed authentication provider integration; preserve MongoDB memberships and the approved `owner`/`member` roles as the authorization source before enabling authenticated user routes.
- [ ] Keep external document processing disabled until the owner approves the exact consent UX, wording/versioning, workspace/document policy, and revocation behavior. Local foundations may proceed, but no document content may be sent to OpenAI before approval and implementation of these checks.
- [ ] Keep chat generation disabled until the owner selects the chat model and approves its configurable token and cost budgets.
- [ ] Decide the tokenizer and verify it supports the approved chunk and per-document token limits before implementing token-based chunking and embedding limits.
- [ ] Implement safe, idempotent lifecycle state handling, but do not finalize retention periods, citation-history behavior, or deletion policy until the owner approves them. Final cleanup and retention behavior must follow that approval.
- [ ] Implement the approved ARQ timeout, five-total-attempt semantics (after verifying the selected ARQ version), backoff, idempotency, failed-job recovery, graceful shutdown, and reconciliation; test worker/Redis interruptions.
- [ ] Prepare permitted evaluation documents/questions and define numerical release thresholds; retain the approved baseline metrics and manual evaluation rubric.
- [ ] Reconcile the stale repository snapshot note in `ARCHITECTURE.md` during a later documentation update; do not change that approved file as part of this decision record.

**Scaffolding status:** This document records the approved baseline but does not itself authorize implementation. After a separate owner instruction and runtime/dependency compatibility validation, foundational scaffolding can proceed without resolving every open feature decision. Chat generation, external document processing, and final retention/deletion behavior remain gated on their respective owner approvals.
