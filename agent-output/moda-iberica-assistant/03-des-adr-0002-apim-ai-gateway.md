# ADR-0002: Azure API Management Standard v2 as AI Gateway

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
> Deciders: Platform Engineering, Security Team

## 🔍 Context

The Moda Ibérica assistant surfaces AI capabilities to web, mobile, and store tablet
clients. All client traffic must pass through a single, hardened ingress that enforces:

1. **Token rate limiting** — prevent individual tenants or rogue clients from exhausting
   Azure OpenAI token quotas
2. **Prompt injection / content safety routing** — pre-screen requests before forwarding
   to AI backends
3. **Model routing** — forward to GPT-4o or GPT-4o-mini based on intent classification
   (see ADR-0001)
4. **Retry and circuit breaker** — automatic retry on 429 throttle responses; fail fast
   when backends are unhealthy
5. **Observability** — emit per-API token consumption metrics to Azure Monitor

A dedicated AI Gateway layer provides these capabilities without baking them into the
RAG orchestrator application code, enabling policy changes without redeployment.

## ✅ Decision

**Deploy Azure API Management (APIM) Standard v2 as the AI Gateway** sitting between
Azure Front Door and the Container Apps RAG orchestrator:

- **APIM Standard v2** (swedencentral) — selected for VNet injection support
  (enabling private endpoint access to OpenAI), built-in token-rate-limit policy, and
  semantic caching capability
- All inbound RAG requests pass through APIM regardless of client type
- APIM enforces: JWT validation, token-per-minute quota per subscription key, model
  routing header injection, and Content Safety pre-screen call
- APIM uses **managed identity** to authenticate to Azure OpenAI — no API keys
- Retry policy: 3 attempts with exponential backoff on 429/503; circuit breaker trips
  after 5 consecutive failures within 30 seconds

## 🔄 Alternatives Considered

| Option | Pros | Cons | WAF Impact |
| --- | --- | --- | --- |
| APIM Standard v2 (selected) | VNet injection, token rate-limit policy, semantic cache, Azure OpenAI built-in backends | ~$750/month; policy complexity | Security: ↑↑, Reliability: ↑, Cost: ↓ |
| APIM Consumption tier | Pay-per-call, lower cost | No VNet injection → OpenAI must use public endpoint; no token-rate-limit built-in | Security: ↓ |
| Custom gateway in Container App | Full control, lower licensing cost | Significant engineering effort; no built-in AI policies; operational burden | Operations: ↓ |
| Azure Front Door only (no APIM) | Simplicity | No AI-specific policies; token limiting requires custom code | Security: ↓, Reliability: ↓ |

## ⚖️ Consequences

### Positive

- Token rate limiting prevents OpenAI quota exhaustion from single abusive client
- Model routing centralised in APIM — no application code changes needed to adjust routing
- Semantic caching in APIM can reduce OpenAI calls for repeated queries by ~15–20%
- Managed identity removes API key rotation risk
- Standard v2 VNet injection keeps OpenAI traffic on private network (no public egress)

### Negative

- APIM Standard v2 costs ~$750/month (~5.6% of total monthly budget)
- APIM policy XML is a specialist skill — team must maintain proficiency
- Warm-up latency after APIM restart: ~30 seconds before policies are active

### Neutral

- APIM does not terminate TLS — Front Door WAF handles SSL offload upstream
- APIM API versioning is available if RAG API schema changes

## 🏛️ WAF Pillar Analysis

| Pillar | Impact | Notes |
| --- | --- | --- |
| Security | ↑↑ | JWT auth, managed identity, no public OpenAI endpoint, prompt pre-screening |
| Reliability | ↑ | Built-in retry, circuit breaker, and health probes reduce cascading failures |
| Performance | ↑ | Semantic caching reduces OpenAI latency for repeat queries |
| Cost | ↓ | +$750/month APIM licence; partially offset by caching savings (~$300–400/mo) |
| Operations | ↑ | Centralised token metrics, per-API dashboards in Azure Monitor |

## 🔒 Compliance Considerations

- APIM Standard v2 with VNet injection keeps all AI traffic within the Azure private
  network — satisfies GDPR data-in-transit requirements
- APIM audit logs (gateway logs) sent to Log Analytics for 90-day retention
- JWT token validation ensures only authenticated sessions reach AI backends;
  reduces risk of anonymous data exposure

## 📝 Implementation Notes

- APIM backend pool: two backends — `openai-gpt4o` and `openai-gpt4o-mini`; routing
  via `set-backend-service` policy on `X-Query-Complexity` header value
- Token rate limit policy: `azure-openai-token-limit` (2,000,000 TPM per subscription)
- Semantic caching: enabled on `/chat/completions` endpoint; TTL 300 seconds
- Health check: APIM health probe hits `/v1/models` on OpenAI every 30 seconds
- Deployment: Bicep AVM module `br/public:avm/res/api-management/service`

---

> Generated by design agent | 2025-07-01

<div align="center">

| [⬅️ ADR-0001](03-des-adr-0001-openai-payg-tiered-routing.md) | 🏠 [Project Index](README.md) |
[ADR-0003 ➡️](03-des-adr-0003-container-apps-dedicated.md) |
| --- | --- | --- |

</div>
