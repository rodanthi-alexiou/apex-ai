<!-- digest:auto-generated from SKILL.md — do not edit manually -->

# Azure AI Architect (Digest)

WAF-aligned architecture guidance for Azure AI and agentic workloads.

**Triggers**: `Azure OpenAI`, `AI Search`, `AI Services`, `Foundry`, `RAG`, `embedding`, `LLM`, `AI agent`, `Document Intelligence`.

## Quick Reference

| Decision Area                          | Reference                                | WAF Pillar             |
| -------------------------------------- | ---------------------------------------- | ---------------------- |
| PTU vs PAYG model deployment           | `references/ai-deployment-decisions.md`  | Cost Optimization      |
| Token cost projection                  | `references/ai-deployment-decisions.md`  | Cost Optimization      |
| RAG accuracy → infra sizing            | `references/ai-waf-checklist.md`         | Reliability            |
| Content safety filters                 | `references/ai-waf-checklist.md`         | Security               |
| Private endpoints (gate, not optional) | `references/ai-waf-checklist.md`         | Security               |
| AI resource naming + kind              | `references/ai-resource-model.md`        | Operational Excellence |
| RBAC roles for AI services             | `references/ai-resource-model.md`        | Security               |
| AI gateway (APIM, Access Contracts)    | `references/ai-gateway-patterns.md`      | Security, Cost         |
| Landing Zone patterns                  | `references/ai-landing-zone-patterns.md` | All pillars            |

## Key Decisions (Summary)

### PTU vs PAYG

| Signal                        | Choose     |
| ----------------------------- | ---------- |
| Predictable sustained load    | PTU        |
| Spiky / dev / experimentation | PAYG       |
| Latency-sensitive production  | PTU        |
| Multiple models / exploration | PAYG first |

### Landing Zone Pattern

| Context                                   | Pattern              |
| ----------------------------------------- | -------------------- |
| Existing Azure Landing Zone (hub-spoke)   | Brownfield: AI spoke |
| Greenfield / no existing enterprise infra | Dedicated AI zone    |
| Multiple teams sharing AI                 | AI gateway in hub    |

### AI Security Gates (Non-Negotiable)

- `publicNetworkAccess: Disabled` on AI Services + AI Search (production)
- Content safety enabled on all public-facing inference endpoints
- NSG deny-all inbound on AI service subnets
- Managed Identity → RBAC (no API keys in production)

### Resource Model (Current — post-2025)

- Use `kind: AIServices` (NOT deprecated `kind: Hub`)
- Foundry Project resources link to AI Services account
- AVM paths: `avm/res/cognitive-services/account`, `avm/res/machine-learning-services/workspace`

## WAF Augmentation for AI Workloads

| WAF Pillar             | AI-Specific Consideration                                           |
| ---------------------- | ------------------------------------------------------------------- |
| Security               | Content safety gates, private endpoints, zero-data-retention        |
| Reliability            | RAG accuracy NFR → AI Search tier + replicas, model failover        |
| Performance Efficiency | Token throughput (TPM), PTU capacity planning, batch vs real-time   |
| Cost Optimization      | Token cost projection, PTU commitment vs PAYG flexibility           |
| Operational Excellence | Model versioning, prompt drift monitoring, AI gateway observability |

## Workflows

1. **AI WAF Assessment** — check triggers → PTU/PAYG decision → token cost → security gates → reliability NFRs
2. **AI Resource Model** — confirm `kind: AIServices`, AVM paths, RBAC chain
3. **AI Gateway Decision** — multi-team signals → gateway required/optional → hub-spoke topology → Access Contracts

## Troubleshooting

| Symptom                          | Fix                                    |
| -------------------------------- | -------------------------------------- |
| IaC uses `kind: Hub`             | Replace with `kind: AIServices`        |
| Cost estimate omits token cost   | Use token pricing endpoint, not VM     |
| Accuracy NFR not mapped to infra | Map to AI Search tier + replica count  |
| Private endpoint "optional"      | It's a gate for production AI services |
| No APIM in multi-team design     | AI gateway required                    |

> _Load full `SKILL.md` or individual `references/*.md` for deep-dive content._
