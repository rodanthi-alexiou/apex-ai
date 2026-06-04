# AI Landing Zone Patterns

Reference architectures and deployment patterns for enterprise Azure AI workloads.
Source: [Azure/AI-Landing-Zones](https://github.com/Azure/AI-Landing-Zones)
Design checklist: https://azure.github.io/AI-Landing-Zones/architecture/design-checklist/

---

## Two Reference Architectures

| Architecture      | When to use                                                                              |
| ----------------- | ---------------------------------------------------------------------------------------- |
| AI LZ for Foundry | Direct AI Apps & Agents workloads using Foundry; single team or business unit            |
| AI LZ for APIM    | Centralized AI gateway for multiple teams; cross-team token governance; cost attribution |
| Both (combined)   | Enterprise platform — Foundry for individual workloads, APIM for central governance      |

> The two architectures are complementary. Start with AI LZ for Foundry for a single
> team; add AI LZ for APIM when a second team onboards or when cost attribution is required.

---

## Deployment Patterns

### Greenfield (Standalone with New Resources)

- Provisions a new VNet, new Log Analytics workspace, and all AI resources from scratch
- Use when: no existing Azure Landing Zone or CAF Enterprise-Scale platform
- All networking, DNS, and firewall are self-contained in the AI LZ

### Brownfield (Standalone with Existing Resources)

- Integrates with existing enterprise LZ — reuses central VNet, firewall, DNS zones, and monitoring
- Use when: a CAF/Enterprise-Scale platform landing zone is already in place
- The AI LZ delegates to shared services (DNS, firewall, monitoring) via platform team hand-off

**Key question to ask in requirements:** "Does the customer have an existing Azure Landing Zone?"

If YES → brownfield pattern; identify which shared services the AI LZ will reuse.
If NO → greenfield pattern; the AI LZ must provision all networking dependencies.

### When AI LZ Cannot Be Deployed

Enterprise customers may have restrictions that block adopting the AI Landing Zone reference
architecture (centralized governance mandates, existing platform LZ policies, subscription
lockdowns). When AI LZ deployment is blocked, apply the WAF/CAF fallback controls below and
record shared-service dependencies in `04-governance-constraints.md` under
`## Platform Team Dependencies`.

| AI LZ Control           | Item | WAF/CAF Fallback                                                                  |
| ----------------------- | ---- | --------------------------------------------------------------------------------- |
| AI LZ VNet + NSGs       | N-R4 | Use customer's existing platform LZ VNet; coordinate NSG rules with platform team |
| AI LZ DDoS              | N-R1 | Reuse platform LZ DDoS Standard plan; document as platform team dependency        |
| AI LZ Azure Firewall    | N-R7 | Route AI egress through central hub firewall via UDR; document required FQDNs     |
| AI LZ Private DNS Zones | N-R8 | Use central Private DNS Zones from platform LZ; add AI service DNS records        |
| AI LZ Bastion           | N-R2 | Reuse central Bastion service; AI developer access via existing jump box          |
| AI LZ APIM gateway      | N-R6 | Deploy APIM in platform hub or reuse existing APIM; see ai-gateway-patterns.md    |
| Greenfield AI LZ        | —    | Brownfield pattern; all shared services delegated to platform team hand-off       |

**Minimum WAF baseline — applies regardless of whether AI LZ is deployed:**

- ✅ Private endpoints for all PaaS AI services (`publicNetworkAccess: Disabled`) — N-R3
- ✅ Managed Identity on all AI services + `disableLocalAuth: true` — I-R3, I-R6
- ✅ Defender for AI enabled on AI Services and AI Search — S-R1
- ✅ Diagnostic settings to Log Analytics workspace for all AI resources — M-R4
- ✅ Content safety filters configured on all public-facing inference endpoints — G-R4
- ✅ RBAC with least privilege; no API key distribution — I-R5
- ✅ Azure Policy `Audit` effect for model catalog governance — G-R1, G-R5

---

## Resource Organization

| Decision                       | Recommendation                                                  | Source   |
| ------------------------------ | --------------------------------------------------------------- | -------- |
| How many AI Services accounts? | One per billing boundary (per team, BU, or environment)         | R-R4     |
| How many Foundry Projects?     | One per distinct application or use case                        | R-R4     |
| Storage isolation              | Separate Cosmos DB + blob storage + AI Search index per Project | D-R2     |
| Environment separation         | Separate AI Services accounts for dev / staging / prod          | Security |

---

## Pre-Deployment Quota Checks

Always verify before deploying (source: AI-LZ R-R2, R-R3):

1. **TPM quota** for the target model in the target region
   - Check: Azure Portal → AI Services → Quota → Global Standard or Provisioned
   - Or: `az cognitiveservices usage list --location <region>`
2. **PTU availability** if using provisioned throughput
   - PTU capacity is reserved per region; verify availability before committing
3. **AI Search limits** in target region
   - Partition and replica limits vary by region and tier
4. **Cognitive Services account limit** per subscription (default: 15 per region for S0)
   - Request increase if deploying per-team accounts across many teams

**Regions with Azure OpenAI Evaluation support** (required for Foundry eval runs):
`eastus2`, `northcentralus`, `swedencentral`, `switzerlandwest`, `uaenorth`

> Default APEX region `swedencentral` supports Azure OpenAI Evaluation. ✓

---

## Region Selection

| Service                         | Availability constraint                                       | Source |
| ------------------------------- | ------------------------------------------------------------- | ------ |
| Azure OpenAI model availability | Not all models available in all regions; check model cards    | R-R1   |
| AI Foundry Evaluation           | Limited regions (see above)                                   | R-R1   |
| PTU capacity                    | PTU reservations are region-specific; pre-check before deploy | R-R2   |
| Content Safety                  | Available in most regions; verify for swedencentral           | R-R1   |

When requirements specify a model (e.g., `o1`, `gpt-4.5`), verify it is available in
`swedencentral` before proceeding. Fallback regions: `eastus2` or `northcentralus`.

---

## Design Checklist Areas (Summary)

Full checklist: https://azure.github.io/AI-Landing-Zones/architecture/design-checklist/

| Area                  | Key recommendations                                                     |
| --------------------- | ----------------------------------------------------------------------- |
| Networking            | Private endpoints, NSGs, APIM gateway, Azure Firewall, private DNS      |
| Security              | Defender for AI, Purview, MITRE ATLAS threat modeling, prompt shielding |
| Governance            | Built-in AI policies, NIST AI RMF, Responsible AI dashboard             |
| Identity              | Managed identity, PIM, Entra ID, Conditional Access, disable keys       |
| Monitoring            | Azure Monitor, Foundry evals, diagnostic settings, drift detection      |
| Cost                  | PTU + PAYG combined, Global Deployment type, auto-shutdown non-prod     |
| Data                  | Thread/run storage decision, per-project isolation                      |
| Reliability           | Multi-region DR for AI Services, AI Search, Cosmos DB                   |
| Resource Organization | Region selection, quota pre-checks, Foundry per billing boundary        |

---

## IaC Implementation

Bicep and Terraform implementations of the AI Landing Zone patterns:

- Repository: https://github.com/Azure/AI-Landing-Zones
- Both use AVM (Azure Verified Modules) as the module source
- Bicep: `br/public:avm/res/` module paths
- Terraform: `registry.terraform.io/Azure/avm-res-` module paths
