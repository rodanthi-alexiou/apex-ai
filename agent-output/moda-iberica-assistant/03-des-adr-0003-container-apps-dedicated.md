# ADR-0003: Container Apps Dedicated over AKS for RAG Orchestrator

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
> Deciders: Platform Engineering, Infrastructure Team

## 🔍 Context

The Moda Ibérica RAG orchestrator is a containerised Python/LangChain application that:
- Receives user queries via APIM
- Retrieves relevant product/policy chunks from AI Search
- Calls Azure OpenAI (routed via APIM) for generation
- Writes session state to Cosmos DB

The team evaluated compute platforms to host this workload. Primary drivers:
- The orchestrator is a single-container, stateless HTTP service
- Traffic is variable (daytime peak, overnight quiet, Black Friday 3× spike)
- Team has no Kubernetes expertise; maintaining cluster infrastructure is undesirable
- Private networking is mandatory (no public endpoint on orchestrator)
- VNet integration required for private endpoint connectivity to AI Search and Cosmos DB

## ✅ Decision

**Deploy the RAG orchestrator on Azure Container Apps (Dedicated plan, D4 profile)**
within a Container Apps Environment injected into the workload VNet subnet:

- **Dedicated plan** (not Consumption): required for VNet injection with private endpoints
  and predictable memory allocation for the LangChain process (~3 GB RSS at peak)
- **D4 workload profile** (4 vCPU, 8 GB): sized for concurrent RAG chains
- **KEDA-based autoscale**: scale 2→20 replicas on HTTP RPS metric; scale-to-zero
  disabled on dedicated plan (minimum 2 replicas for availability)
- **Dapr disabled**: direct HTTP communication is sufficient; Dapr overhead not justified
- Container image stored in Azure Container Registry (admin disabled, managed identity pull)

## 🔄 Alternatives Considered

| Option | Pros | Cons | WAF Impact |
| --- | --- | --- | --- |
| Container Apps Dedicated (selected) | Managed plane, VNet injection, KEDA, low ops burden | Slightly higher cost than Consumption; less fine-grained node control | Operations: ↑↑ |
| AKS Standard | Full Kubernetes control, custom networking | Requires cluster management, upgrades, node pool sizing; team has no K8s expertise | Operations: ↓↓ |
| Container Apps Consumption | Cheapest, scale-to-zero | No VNet injection → private endpoints unavailable; cold-start latency unacceptable | Security: ↓, Reliability: ↓ |
| Azure App Service Premium | Familiar, easy VNet integration | Not container-native; KEDA-style autoscale not built-in; worse bin-packing | Performance: ↓ |

## ⚖️ Consequences

### Positive

- Platform team manages container runtime, OS patching, and cluster upgrades automatically
- KEDA scales to absorb Black Friday traffic (up to 20 replicas = 80 vCPU, 160 GB)
- VNet injection enables private endpoint access to AI Search, Cosmos DB, and Storage
- Managed identity pull from ACR eliminates registry credential rotation
- Deployment via Container Apps revision model enables zero-downtime blue-green deploys

### Negative

- Dedicated plan minimum cost ~$580/month (2 D4 replicas running 24/7)
- Less control over underlying node selection vs AKS (acceptable trade-off)
- Maximum 20 replicas per Container App — may need increase if user base grows beyond
  current projections

### Neutral

- Container Apps Environment can host additional apps in future (intent classifier,
  A/B test variants) without additional environment cost

## 🏛️ WAF Pillar Analysis

| Pillar | Impact | Notes |
| --- | --- | --- |
| Security | ↑↑ | VNet injection + private endpoints keep all data traffic off public internet |
| Reliability | ↑ | Minimum 2 replicas, KEDA autoscale, health probes, zone-redundant environment |
| Performance | ↑ | D4 profile avoids memory contention; KEDA scales before latency degrades |
| Cost | → | Dedicated plan ~$580/mo baseline vs AKS ~$800+/mo for equivalent; comparable |
| Operations | ↑↑ | No Kubernetes expertise required; managed control plane |

## 🔒 Compliance Considerations

- Container Apps Dedicated in VNet satisfies requirement that PII (query content,
  session state) does not traverse public network
- ACR with managed identity pull removes shared credential exposure risk
- Container image scanning via Microsoft Defender for Containers (enabled on ACR)

## 📝 Implementation Notes

- Environment subnet: `/24` in workload VNet (minimum `/27` required for Dedicated)
- Workload profile: `D4` (4 vCPU, 8 GB) — upgrade to `D8` if P99 latency degrades
- Autoscale rule: `http` trigger, concurrent requests threshold = 10 per replica
- Health probe: HTTP GET `/health` on port 8080, initial delay 10s, period 15s
- Deployment: Bicep AVM `br/public:avm/res/app/container-app`
- Image build: GitHub Actions CI pipeline → push to ACR → rolling update via revision

---

> Generated by design agent | 2025-07-01

<div align="center">

| [⬅️ ADR-0002](03-des-adr-0002-apim-ai-gateway.md) | 🏠 [Project Index](README.md) |
[ADR-0004 ➡️](03-des-adr-0004-hub-spoke-private-endpoints.md) |
| --- | --- | --- |

</div>
