# ADR-0006: RAG Orchestrator Strategy — Agentic Retrieval vs Classic RAG

![Step](https://img.shields.io/badge/Step-3-blue?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Accepted-green?style=for-the-badge)
![Type](https://img.shields.io/badge/Type-ADR-purple?style=for-the-badge)

<details open>
<summary><strong>📑 Decision Contents</strong></summary>

- [🔍 Context](#-context)
- [✅ Decision](#-decision)
- [🔄 Alternatives Considered](#-alternatives-considered)
- [⚖️ Consequences](#%EF%B8%8F-consequences)
- [🏛️ WAF Pillar Analysis](#%EF%B8%8F-waf-pillar-analysis)
- [🔒 Compliance Considerations](#-compliance-considerations)
- [📝 Implementation Notes](#-implementation-notes)

</details>

> Status: Accepted
> Date: 2026-06-04
> Deciders: Platform Engineering, AI Team

## 🔍 Context

Moda Ibérica's AI assistant handles conversational product discovery, outfit recommendations,
and multi-turn fashion consultations grounded in a private knowledge base (~85,000 documents:
product catalogue, brand guidelines, lookbooks, FAQ). Effective RAG orchestration determines
both answer quality and end-to-end latency.

Two orchestration patterns are available on Azure:

**Classic RAG**: Application code owns the full pipeline. A single query is sent to Azure
AI Search, the top-k chunks are returned, and the orchestrator passes them to the LLM.
Simple, fully GA, and gives fine-grained control over every stage of the pipeline.

**Agentic Retrieval** (Azure AI Search + AI Foundry Agent Service): An LLM within AI Search
decomposes the user query into multiple focused subqueries, executes them in parallel against
the index, applies semantic ranking, and returns a structured grounding response with citations
and execution metadata. The orchestrator only needs to pass the grounding response to the
generative LLM — no custom query-decomposition logic is required.

Moda Ibérica's query patterns are predominantly conversational and multi-turn
(e.g., "What goes with the navy blazer I saw earlier? Do you have it in petite?"),
which are the scenarios where agentic retrieval provides the highest accuracy uplift.
The platform also includes Azure AI Foundry Agent Service, making the integration
surface available without additional provisioning.

The key trade-offs assessed were: relevance accuracy, orchestrator complexity,
latency, security (prompt injection from retrieved content), and preview/GA status.

## ✅ Decision

**Adopt Agentic Retrieval as the primary RAG orchestration pattern**, implemented via
Azure AI Search knowledge sources connected to Azure AI Foundry Agent Service:

- **Query planning**: AI Search LLM decomposes conversational queries into parallel subqueries
  using conversation history for context continuity across turns
- **Retrieval**: Parallel subquery execution across the product catalogue index with hybrid
  search (BM25 + vector, fused via RRF) and semantic reranking
- **Grounding response**: Structured output including ranked chunks, citations, and query
  activity log — passed directly to the generative LLM (GPT-4o / GPT-4o-mini per ADR-0001)
- **Reasoning effort**: Set to `medium` for outfit consultations; `low` for simple lookups
  to balance latency against retrieval depth
- **Security**: Retrieved content treated as untrusted input; Content Safety system message
  enforces Prompt Shields for indirect injection from document passages (per ADR-0002)
- **Fallback**: Classic RAG path retained in the Container Apps orchestrator service for
  queries routed to GPT-4o-mini (simple lookups) where agentic overhead is unnecessary

## 🔄 Alternatives Considered

| Option | Pros | Cons | WAF Impact |
|---|---|---|---|
| **Classic RAG only** | Fully GA, simple, developer-controlled pipeline, low latency for single-turn | Custom multi-turn context management required; no parallel subquery execution; lower relevance for conversational queries | Reliability: neutral, Performance: ↓ for multi-turn, Operations: ↑ |
| **Agentic Retrieval only (all queries)** | Highest relevance across all query types; no routing logic | Adds ~200–400 ms LLM query-planning overhead on every request; excessive for simple lookups | Performance: ↓ for simple queries, Reliability: ↑ |
| **Agentic Retrieval for complex + Classic RAG for simple (selected)** | Optimal relevance where it matters; low latency retained for lookups; aligns with existing intent routing (ADR-0001) | Two retrieval paths increase operational complexity; must maintain hybrid routing logic | Performance: ↑, Reliability: ↑, Operations: neutral |
| **LangChain / Semantic Kernel custom orchestration** | Framework abstractions; portable | Adds dependency; duplicate query-planning logic already in AI Search; more surface area to secure | Operations: ↓, Security: ↓ |
| **Foundry IQ (knowledge endpoint)** | Single endpoint to knowledge layer; simplest integration surface | Preview feature; not recommended for GDPR-sensitive production data until GA | Reliability: risk, Security: risk |

## ⚖️ Consequences

### Positive

- Multi-turn conversational queries achieve higher relevance without custom context-management code
  — conversation history is passed to the AI Search retrieval call, which handles intent continuity
- Parallel subquery execution reduces p95 retrieval latency for complex queries versus sequential
  multi-query approaches
- Built-in citations and query activity log simplify brand compliance tracing
  (which catalogue item was retrieved for which recommendation)
- Orchestrator codebase is thinner: no custom query-decomposition or re-ranking logic to maintain
- Aligns with intent-routing decision (ADR-0001): complex queries → agentic retrieval + GPT-4o;
  simple queries → classic RAG + GPT-4o-mini

### Negative

- Agentic retrieval is still preview (not GA) as of June 2026 — Microsoft SLA and feature
  stability commitments are not yet at production tier; requires monitoring for breaking changes
- Additional LLM call within AI Search for query planning adds cost (~$0.002–0.005 per complex query)
  and ~200–400 ms latency overhead
- Two retrieval paths (agentic + classic) increase testing surface and require separate
  observability instrumentation
- Prompt injection risk surface is broader: indirect attacks via retrieved product descriptions
  must be covered by Content Safety system message (dependency on ADR-0002 controls)

## 🏛️ WAF Pillar Analysis

| WAF Pillar | Assessment | Notes |
|---|---|---|
| **Reliability** | ✅ Improved | Parallel subquery execution reduces single-point query failure; classic RAG fallback path available |
| **Security** | ⚠️ Requires controls | Retrieved content treated as untrusted; Prompt Shields (indirect injection) mandatory; AI Search private endpoint required |
| **Performance Efficiency** | ✅ Improved | Agentic path: parallel queries, semantic ranking, adjustable reasoning effort; classic path: ms-level latency for simple lookups |
| **Cost Optimization** | ⚠️ Manageable | Extra LLM call per complex query adds ~5–10% retrieval cost; offset by higher relevance reducing retry rate and abandoned sessions |
| **Operational Excellence** | ⚠️ Complexity increase | Two retrieval paths; query activity log in grounding response aids observability; reasoning effort tuning is operationally sensitive |

## 🔒 Compliance Considerations

| Concern | Control |
|---|---|
| **GDPR data residency** | AI Search deployed in `swedencentral`; all retrieval within EU boundary; no data leaves the region |
| **Prompt injection (indirect)** | Content Safety Prompt Shields enabled for `DocumentAttack` classification on all retrieved passages before LLM context assembly |
| **Data access control** | Azure AI Search document-level security trimming via Entra ID metadata; hospital/brand data segmented at index level |
| **Audit trail** | Query activity log from agentic retrieval response stored in Log Analytics for retrieval-chain auditability |
| **LOPDGDD / EU AI Act** | Grounding citations logged per recommendation event, enabling transparency obligation fulfilment under AI Act Article 13 |

## 📝 Implementation Notes

### Retrieval Configuration

```python
# Agentic retrieval call (complex queries — routed by APIM intent classifier)
response = search_client.retrieve(
    knowledge_source_id=KNOWLEDGE_SOURCE_ID,
    query=user_message,
    conversation_history=session_history,   # enables multi-turn context
    reasoning_effort="medium",              # low | medium — tune per use case
    max_docs_for_reranker=50,
    top=5
)
grounding_data = response.results          # structured chunks + citations
query_log = response.activity             # log to Application Insights
```

```python
# Classic RAG path (simple queries — GPT-4o-mini route)
results = search_client.search(
    search_text=user_query,
    vector_queries=[VectorizedQuery(...)],
    query_type=QueryType.SEMANTIC,
    top=3
)
chunks = [r["chunk"] for r in results]
```

### Routing Integration

Builds on the intent classifier in ADR-0001. The APIM policy routes:
- `complexity_score >= 0.6` → agentic retrieval + GPT-4o
- `complexity_score < 0.6` → classic RAG + GPT-4o-mini

### Observability

- Log `response.activity` (query activity log) to Application Insights custom events
- Track `reasoning_effort` and subquery count per request for latency attribution
- Alert on retrieval p95 > 2 s (agentic path) or > 300 ms (classic path)

### Review Trigger

Re-evaluate agentic retrieval GA status at Q4 2026. If still in preview, assess:
1. Production incident rate attributable to preview instability
2. Whether Foundry IQ has reached GA as an alternative integration surface
