# ADR-0001: Azure OpenAI PAYG with Tiered Model Routing

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
> Deciders: Platform Engineering, AI Team, Finance

## 🔍 Context

Moda Ibérica's RAG assistant handles a wide variety of queries: complex multi-turn
outfit consultations requiring deep reasoning (GPT-4o), and simple lookup queries
(store locator, stock status, promotion details) where a lightweight model suffices.

Azure OpenAI offers two billing models:
- **PAYG (Pay-As-You-Go)**: Token-based billing, no upfront commitment, instant
  provisioning, suitable for variable/unpredictable load.
- **PTU (Provisioned Throughput Units)**: Hourly reservation, guaranteed latency,
  best when load is constant and predictable at high volume.

At launch (Jul–Aug 2025), daily active users are estimated at 500–2,000 with
significant traffic spikes during Black Friday (~3× baseline) and seasonal sales.
The workload is not yet steady enough to justify PTU commitments.

Additionally, routing all queries through GPT-4o regardless of complexity would cost
~$10,350/month. A tiered routing approach using GPT-4o-mini for simple queries
reduces this to ~$7,950/month — a saving of ~$2,400/month (~$28,800/year).

## ✅ Decision

**Deploy Azure OpenAI on PAYG billing with tiered model routing:**

- **GPT-4o** (swedencentral): complex outfit consultations, multi-turn sessions,
  product recommendations requiring contextual reasoning
- **GPT-4o-mini** (swedencentral): simple lookups, FAQ responses, stock queries,
  store locator — routed via APIM policy rules based on intent classification
- **Re-evaluate PTU** at month 6 (Jan 2026) when usage patterns are stable and
  predictable; switch if monthly token volume exceeds PTU break-even threshold
- Intent classification uses APIM inbound policy to route based on query complexity
  score returned by a lightweight classifier Container App

## 🔄 Alternatives Considered

| Option | Pros | Cons | WAF Impact |
| --- | --- | --- | --- |
| GPT-4o PAYG only (single model) | Simplicity, best quality | ~$2,400/mo overspend; no cost optimisation | Cost: ↓ |
| GPT-4o PTU (reserved, 50 PTUs) | Guaranteed latency, predictable cost at scale | ~$7,300/mo fixed regardless of usage; wasted at low traffic | Reliability: ↑, Cost: ↓ at launch |
| GPT-4o + GPT-4o-mini PAYG tiered routing (selected) | ~$2,400/mo saving; flexible scaling; no commitment risk | Routing logic adds operational complexity; intent classifier is an additional service | Cost: ↑, Performance: ↑, Operations: neutral |
| GPT-4o-mini only | Cheapest option | Insufficient quality for outfit consultations; degrades UX | Performance: ↓ |

## ⚖️ Consequences

### Positive

- ~$2,400/month cost saving (~$28,800/year) retained in operating budget
- No PTU commitment risk during volatile ramp-up period
- PAYG scales automatically during Black Friday spikes without pre-purchased headroom
- Path to PTU is preserved — switchover requires only APIM backend update
- Tiered routing architecture is extensible (add GPT-4.5 or o1 in future)

### Negative

- Intent classifier Container App introduces an additional failure point
- Routing logic must be maintained in APIM policies and updated as model variants change
- PAYG costs are variable; Black Friday spend requires monitoring and budget alerts

### Neutral

- Both models (GPT-4o, GPT-4o-mini) are available in swedencentral — no additional
  region required
- Content Safety applies to both routing paths identically

## 🏛️ WAF Pillar Analysis

| Pillar | Impact | Notes |
| --- | --- | --- |
| Security | → | PAYG/PTU choice does not affect data plane security controls |
| Reliability | → | PAYG capacity is shared; risk of throttling at very high load mitigated by Retry + Circuit Breaker in APIM |
| Performance | ↑ | GPT-4o-mini responds 40–60% faster for simple queries; reduces median latency |
| Cost | ↑ | ~$2,400/month saving vs single-model approach; ~17.7% reduction in OpenAI spend |
| Operations | → | Intent classifier adds one monitored service; APIM policy versioning is manageable |

## 🔒 Compliance Considerations

- Both GPT-4o and GPT-4o-mini in swedencentral process data within EU boundaries
  (GDPR Article 44 data residency satisfied)
- Customer query content must not be used to train models — confirmed via Azure OpenAI
  data processing addendum (opt-out is default for API access)
- Audit logs of model invocations retained in Log Analytics (90-day retention)

## 📝 Implementation Notes

- APIM inbound policy evaluates `X-Query-Complexity` header (set by classifier app)
- Threshold: complexity score < 0.4 → GPT-4o-mini; ≥ 0.4 → GPT-4o
- Fallback: if classifier is unavailable, route all traffic to GPT-4o (fail safe)
- Budget alert: Azure Cost Management alert at 80% of €15K monthly ceiling
- PTU break-even review: month 6, if daily token volume > 50M tokens consistently

---

> Generated by design agent | 2025-07-01

<div align="center">

| ⬅️ [ADR Index](README.md) | 🏠 [Project Index](README.md) |
[ADR-0002 ➡️](03-des-adr-0002-apim-ai-gateway.md) |
| --- | --- | --- |

</div>
