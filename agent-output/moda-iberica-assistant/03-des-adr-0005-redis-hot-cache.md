# ADR-0005: Azure Cache for Redis (C1 Standard) for Hot Query Caching

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
> Date: 2025-07-01
> Deciders: Platform Engineering, AI Team

## 🔍 Context

Analysis of expected query patterns for the Moda Ibérica assistant reveals that a
significant proportion of queries are highly repetitive:

- "What are this week's promotions?" (asked by hundreds of customers daily)
- "Show me outfit recommendations for [popular category]" (seasonal repetition)
- "Where is my nearest store in [city]?" (store locator, rarely changes)
- "What is your returns policy?" (FAQ, static content)

These queries share a common characteristic: the AI-generated response is deterministic
for a given context window and does not change until the underlying data changes
(product catalogue, promotions, store data). Re-generating them via Azure OpenAI on
every request wastes tokens, adds latency, and increases cost.

The APIM semantic cache (see ADR-0002) covers some caching at the gateway layer, but
has a 300-second TTL and limited capacity. A dedicated Redis cache operated by the
RAG orchestrator provides application-level cache control with richer TTL policies
aligned to data freshness (promotions refresh daily; FAQ is quasi-static).

## ✅ Decision

**Deploy Azure Cache for Redis C1 Standard (1 GB, swedencentral) for hot query
response caching in the RAG orchestrator:**

- **C1 Standard tier**: 1 GB cache, SSL-only, replicated (Standard tier = primary +
  replica), suitable for ~200K cached response entries
- Cache key: `sha256(normalised_query + language + store_region)`
- TTL strategy:
  - Promotions / offers: 3,600 seconds (1 hour)
  - FAQ / policy content: 86,400 seconds (24 hours)
  - Outfit recommendations: 1,800 seconds (30 minutes) — higher freshness needed
  - Store locator: 43,200 seconds (12 hours)
- Cache miss: execute full RAG pipeline; write result to Redis before returning response
- Cache invalidation: Logic Apps runbook triggers Redis `FLUSHDB` on relevant key prefix
  when SAP Commerce sends product/promotion update webhook

## 🔄 Alternatives Considered

| Option | Pros | Cons | WAF Impact |
| --- | --- | --- | --- |
| Redis C1 Standard (selected) | Managed, replicated, SSL, private endpoint, ~$300/mo | Requires cache key design and invalidation logic | Performance: ↑↑, Cost: ↑ |
| APIM semantic cache only | No additional service | 300s fixed TTL; limited to gateway layer; no programmatic invalidation | Performance: ↑ (partial) |
| In-memory cache in Container App | Zero cost | Lost on restart; not shared across replicas; no persistence | Reliability: ↓ |
| Cosmos DB as cache (TTL on items) | Already provisioned | Cosmos is not optimised for sub-ms cache reads; higher cost per operation | Performance: ↓ |
| No caching | Zero cost | Repeated queries each cost ~$0.0003 in tokens; degrades performance at peak | Cost: ↓, Performance: ↓ |

## ⚖️ Consequences

### Positive

- Estimated 25–35% of queries served from cache during peak hours → ~$800–1,200/month
  OpenAI token saving (offsets Redis cost ~2.7×)
- Cache hit latency: <5ms vs 1,500–3,000ms for full RAG pipeline — dramatically
  improves perceived responsiveness
- Reduces AI Search query volume by same proportion, lowering Search RU consumption
- Logic Apps invalidation runbook ensures cache consistency when product data changes

### Negative

- Cache invalidation logic adds operational complexity (webhook handler + Logic App)
- Stale responses possible if invalidation webhook is delayed or fails; mitigated by
  conservative TTLs
- C1 Standard is 1 GB — monitor eviction rate at Black Friday peak; may need upgrade
  to C2 if cache thrashing occurs

### Neutral

- Redis private endpoint provisioned in `snet-privateendpoints` (consistent with ADR-0004)
- Cache observability: Redis Cache Insights in Azure Monitor shows hit rate, evictions,
  connected clients

## 🏛️ WAF Pillar Analysis

| Pillar | Impact | Notes |
| --- | --- | --- |
| Security | ↑ | SSL-only, private endpoint, managed identity auth via access key stored in Key Vault |
| Reliability | ↑ | Standard tier replication means cache survives primary node failure (60s failover) |
| Performance | ↑↑ | <5ms cache reads vs 1,500–3,000ms full RAG; 25–35% of traffic served from cache |
| Cost | ↑ | +$300/mo Redis; estimated -$800 to -$1,200/mo OpenAI token savings; net positive |
| Operations | → | Invalidation runbook adds one Logic Apps workflow; Redis Insights provides monitoring |

## 🔒 Compliance Considerations

- Redis cache stores AI-generated response text only — no raw PII (customer IDs,
  personal data) is stored in the cache key or value
- Cache keys are SHA-256 hashes of normalised queries — cannot be reversed to
  reconstruct original query text
- Redis access key stored in Key Vault; rotated every 90 days via Logic Apps runbook
- Data residency: Redis C1 Standard in swedencentral — all cached data remains in EU

## 📝 Implementation Notes

- Redis connection: `StackExchange.Redis` client in RAG orchestrator; connection string
  from Key Vault reference via Container Apps secret
- Cache key normalisation: lowercase, strip punctuation, language code suffix
  (e.g., `abc123...def456:es`)
- Eviction policy: `allkeys-lru` (evict least recently used when memory full)
- Monitor: set Azure Monitor alert on `used_memory_rss` > 800 MB → consider C2 upgrade
- Invalidation webhook endpoint: Container App route `/admin/cache/invalidate`
  (APIM-authenticated, Logic Apps caller identity)
- Bicep AVM: `br/public:avm/res/cache/redis`

---

> Generated by design agent | 2025-07-01

<div align="center">

| [⬅️ ADR-0004](03-des-adr-0004-hub-spoke-private-endpoints.md) | 🏠 [Project Index](README.md) |
| --- | --- |

</div>
