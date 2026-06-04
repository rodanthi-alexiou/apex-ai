# ADR-0004: Hub-Spoke Network Topology with Private Endpoints

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
> Deciders: Network Engineering, Security Team, Platform Engineering

## 🔍 Context

The Moda Ibérica assistant processes customer queries containing personal data
(customer ID, purchase history, location). All services — AI Search, Cosmos DB,
Azure OpenAI, Blob Storage, Key Vault, ACR — must be reachable from the RAG
orchestrator without traversing the public internet.

Moda Ibérica's corporate network team already operates a hub VNet for shared
services (DNS, bastion, firewall) per their existing Azure Landing Zone.
The assistant workload must integrate with this hub without creating a flat
network that exposes AI services to all other workloads.

A spoke VNet dedicated to the Moda Ibérica assistant workload, peered to the
existing hub, provides the required isolation and connectivity model.

## ✅ Decision

**Adopt hub-spoke VNet topology with private endpoints for all PaaS services:**

- **Hub VNet** (existing, corporate): Azure Firewall, Bastion, central DNS resolver,
  VNet peering hub. No changes to hub required.
- **Workload Spoke VNet** (`10.1.0.0/16`, swedencentral): new VNet peered to hub
  - `snet-containerapp` (`10.1.1.0/24`): Container Apps Environment (Dedicated)
  - `snet-privateendpoints` (`10.1.2.0/24`): Private endpoints for all PaaS services
  - `snet-apim` (`10.1.3.0/28`): APIM Standard v2 VNet injection subnet
- **Private endpoints** (all in `snet-privateendpoints`):
  - Azure OpenAI (`openai.azure.com`)
  - AI Search (`search.windows.net`)
  - Cosmos DB (`documents.azure.com`)
  - Blob Storage (`blob.core.windows.net`)
  - Key Vault (`vaultcore.azure.net`)
  - ACR (`azurecr.io`)
- **Private DNS Zones**: one zone per service, linked to both hub and spoke VNets
- **NSG on every subnet**: deny-all inbound default, allow only required flows

## 🔄 Alternatives Considered

| Option | Pros | Cons | WAF Impact |
| --- | --- | --- | --- |
| Hub-spoke with private endpoints (selected) | Aligns with ALZ; private data path; isolation between workloads | VNet peering cost; DNS zone management; more IPs required | Security: ↑↑ |
| Flat single VNet (no hub-spoke) | Simpler initially | No isolation from other workloads; violates corporate ALZ policy | Security: ↓ |
| Service endpoints only (no private endpoints) | Cheaper than private endpoints | Traffic still leaves VNet; no private DNS; weaker isolation | Security: ↓ |
| Public access with IP firewall rules | Zero networking cost | Customer PII transits public internet; fails GDPR audit | Security: ↓↓ |

## ⚖️ Consequences

### Positive

- All AI service calls remain on Microsoft backbone — zero public internet exposure
- Spoke isolation: compromise of another workload cannot directly reach AI services
- Hub-spoke model is approved by Moda Ibérica's network team — no exception required
- NSG flow logs in Log Analytics provide full network audit trail
- Private DNS zones enable seamless name resolution for all clients in spoke and hub

### Negative

- ~$90/month additional cost for VNet peering, private endpoints, and DNS zones
- Private endpoint provisioning adds ~10 minutes to initial deployment
- DNS zone management is an operational overhead — 6 zones to maintain
- Breaking glass (emergency public access for troubleshooting) requires policy exception

### Neutral

- DR region (germanywestcentral) will require a mirrored spoke VNet when activated;
  not required at launch

## 🏛️ WAF Pillar Analysis

| Pillar | Impact | Notes |
| --- | --- | --- |
| Security | ↑↑ | No public endpoints on any PaaS service; full NSG coverage; aligns with Zero Trust |
| Reliability | ↑ | VNet-level redundancy; no dependency on public DNS for service discovery |
| Performance | → | Private endpoint adds ~0.1ms RTT vs public endpoint; negligible |
| Cost | ↓ | ~$90/mo for peering + private endpoints + DNS zones |
| Operations | → | DNS zones are operational overhead; offset by NSG flow log observability gain |

## 🔒 Compliance Considerations

- Private endpoints satisfy GDPR requirement that customer PII (query content,
  session chat history) does not traverse public networks
- NSG flow logs fulfil network access audit evidence for ISO 27001 A.13.1 controls
- All private DNS zones scoped to subscription — no cross-tenant DNS leakage risk
- Azure Policy `deny-public-endpoint-for-paas` enforced at subscription level
  (governance constraint confirmed in `04-governance-constraints.md`)

## 📝 Implementation Notes

- VNet address space: `10.1.0.0/16` (avoid overlap with hub `10.0.0.0/16`)
- Private DNS zone naming follows Microsoft standard (e.g., `privatelink.openai.azure.com`)
- DNS resolver: hub Azure DNS Private Resolver forwards `privatelink.*` to hub DNS
- NSG rules: allow HTTPS (443) inbound to `snet-privateendpoints` from
  `snet-containerapp` only; block all other inbound
- Bicep AVM modules: `br/public:avm/res/network/virtual-network`,
  `br/public:avm/res/network/private-endpoint`

---

> Generated by design agent | 2025-07-01

<div align="center">

| [⬅️ ADR-0003](03-des-adr-0003-container-apps-dedicated.md) | 🏠 [Project Index](README.md) |
[ADR-0005 ➡️](03-des-adr-0005-redis-hot-cache.md) |
| --- | --- | --- |

</div>
