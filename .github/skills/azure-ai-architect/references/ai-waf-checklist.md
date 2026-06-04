# AI WAF Checklist

WAF-aligned gates and NFR mappings for Azure AI workloads.
Apply during the Architect step (Step 2) when requirements include AI services.

> **AI Landing Zone note**: Items tagged with an AI LZ code (e.g., C-R1, N-R3) map to the
> [Azure AI LZ design checklist](https://azure.github.io/AI-Landing-Zones/architecture/design-checklist/).
> When AI LZ deployment is blocked by customer governance, apply the WAF/CAF fallback
> guidance in each section and record shared-service dependencies in `04-governance-constraints.md`.

---

## Compute

### PaaS Compute Standardization (C-R1)

Standardize compute options across models, orchestrators, self-hosted agents, and all application
tiers (frontend, backend, ingestion). Prefer PaaS options to optimize resource utilization
and simplify management.

| Component              | Recommended PaaS option                    | Notes                                                |
| ---------------------- | ------------------------------------------ | ---------------------------------------------------- |
| Orchestrators / agents | Azure Container Apps                       | Consumption or Dedicated plan; KEDA auto-scaling     |
| Backend API / ingress  | Azure Container Apps or Azure App Service  | ACA for cloud-native; App Service for lift-and-shift |
| Batch ingestion        | Azure Container Apps Jobs                  | Event-driven; scale to zero between runs             |
| Model hosting (BYOM)   | Azure Machine Learning Managed Compute     | Only if Foundry-hosted models are insufficient       |
| Frontend               | Azure Static Web Apps or Azure App Service | Azure Front Door + WAF in front of any public app    |

> Prefer Azure Container Apps for all new agent workloads — supports KEDA, Dapr, and Entra
> Workload Identity natively. Fall back to AKS only when orchestration complexity demands it.

---

## Security

### Gates (non-negotiable for production)

| Gate                                | Setting                          | Resource                     |
| ----------------------------------- | -------------------------------- | ---------------------------- |
| No public inference endpoint        | `publicNetworkAccess: Disabled`  | AI Services account          |
| No public search endpoint           | `publicNetworkAccess: Disabled`  | AI Search service            |
| Private endpoint required           | Deploy PE in workload subnet     | Both AI Services + AI Search |
| No shared key access on AI Services | Managed Identity only            | AI Services account          |
| No local auth on AI Search          | `disableLocalAuth: true`         | AI Search service            |
| HTTPS-only                          | `supportsHttpsTrafficOnly: true` | All cognitive endpoints      |

> **Escalation:** If requirements specify a public-facing chatbot or copilot endpoint,
> the inference call must still route through a private backend (e.g. Container Apps with
> egress to private AI endpoint). The user-facing surface ≠ the AI service endpoint.

### Content Safety

Content safety filters add latency (~100ms) and per-call cost.

| Condition                          | Requirement                                 |
| ---------------------------------- | ------------------------------------------- |
| Public-facing inference endpoint   | **Required** — flag as Security gate        |
| Internal-only, authenticated users | Recommended — document if explicitly waived |
| Jailbreak / prompt injection risk  | Required — also add to threat model         |

Verify available filter categories for the target region via the
[Azure AI Content Safety docs](https://learn.microsoft.com/azure/ai-services/content-safety/).

### Security Posture Management

| Control                                                              | Requirement                                                        |
| -------------------------------------------------------------------- | ------------------------------------------------------------------ |
| Defender for Cloud + AI threat protection (Defender for AI)          | **Required** — enable on AI Services and AI Search resources       |
| Microsoft Cloud Security Benchmark applied to AI Services            | Verify compliance posture in Defender for Cloud recommendations    |
| Purview Insider Risk Management for AI-processed data                | Required for regulated industries or PII-containing corpora        |
| Threat model includes MITRE ATLAS + OWASP Generative AI Top 10 risks | Required for public-facing AI apps; recommended for internal       |
| Prompt shielding + output monitoring on all inference calls          | **Required** for public endpoints — integrates with content safety |
| PII detection via Azure Language Service before forwarding to model  | Required for workloads processing user-provided unstructured text  |

---

## Reliability

### RAG Accuracy as a Reliability NFR

If requirements state an accuracy target (e.g., "80% answer relevance",
"< 5% hallucination rate"), this maps to WAF Reliability — not to the application layer.

| Accuracy target               | Architecture implication                                  |
| ----------------------------- | --------------------------------------------------------- |
| Any stated accuracy target    | AI Search tier ≥ Standard S1; document in NFR table       |
| > 80% answer relevance        | Standard S1 + 2 replicas minimum for consistent retrieval |
| > 90% answer relevance        | Standard S2 or semantic ranker enabled                    |
| < 5% hallucination rate       | Embedding model: `text-embedding-3-large` (not `ada-002`) |
| Low hallucination + citations | Hybrid search (keyword + vector) required                 |

**AI Search tier guidance:**

| Tier              | Max replicas | Semantic ranker | Use case                       |
| ----------------- | ------------ | --------------- | ------------------------------ |
| Basic             | 3            | No              | Dev/test only                  |
| Standard S1       | 12           | Yes (add-on)    | Production RAG                 |
| Standard S2       | 12           | Yes (included)  | High-accuracy RAG              |
| Storage Optimized | 12           | Yes             | Large document corpora > 100GB |

### OpenAI Reliability Patterns

| Pattern                                           | When to apply                             |
| ------------------------------------------------- | ----------------------------------------- |
| Retry with exponential backoff on HTTP 429        | Always — throttling is expected at scale  |
| Circuit breaker on model endpoint                 | Production workloads with SLA             |
| PTU + PAYG overflow                               | If P99 latency SLA stated in requirements |
| Multi-region active-active                        | RPO = 0 or RTO < 1 hour                   |
| Secondary AI Services instance in failover region | RTO < 4 hours                             |

---

## Cost Optimization

See [ai-deployment-decisions.md](ai-deployment-decisions.md) for full PTU vs PAYG decision tree
and token cost projection workflow.

### Cost Flags for Architecture Review

| Condition                                | Action                                                      |
| ---------------------------------------- | ----------------------------------------------------------- |
| AI Search Standard + semantic ranker     | ~€750/month baseline — include in cost estimate             |
| GPT-4o output tokens > 10M/month         | Evaluate PTU; calculate break-even with Pricing MCP         |
| Document Intelligence > 500K pages/month | High-volume pricing tier — get page count from requirements |
| Content safety enabled on all calls      | Add per-call overhead to token cost projection              |

### Auto-Shutdown for Non-Production Resources (CO-R4)

Define and enforce an auto-shutdown policy for all non-production AI compute resources:

- Azure Machine Learning compute instances: enable automatic shutdown after idle period
- Azure Container Apps dev/staging: set `minReplicas: 0` (scale to zero)
- Azure AI Foundry compute (if provisioned): schedule shutdown outside business hours
- Azure VMs (if any): enable auto-shutdown via Azure Policy or portal schedule

> **WAF/CAF fallback (AI LZ blocked)**: Document auto-shutdown as a manual governance
> control in `04-governance-constraints.md`. Enforce via Azure Policy `Audit` effect
> targeting `Microsoft.MachineLearningServices/workspaces` compute resources.

---

## Operational Excellence

### Monitoring Requirements

| Signal                           | Tool                                 | Why                                              |
| -------------------------------- | ------------------------------------ | ------------------------------------------------ |
| Token consumption per deployment | Azure Monitor metrics on AI Services | Throttle prediction and cost tracking            |
| Search latency (P99)             | AI Search diagnostic logs            | RAG accuracy degradation early warning           |
| Content safety block rate        | Application Insights                 | Detects adversarial prompt campaigns             |
| Embedding drift                  | Custom evaluation pipeline (FAOS)    | RAG accuracy over time                           |
| Model/data drift                 | Foundry evaluations + custom alerts  | Model output quality over time (M-R5)            |
| Baseline metric alerts           | Azure Monitor Baseline Alerts (AMBA) | Automated alerting for AI resources (M-R2)       |
| Network flow monitoring          | Network Watcher flow logs            | Detect unexpected AI service access (M-R6)       |
| Foundry request traces           | AI Foundry built-in tracing          | Per-request trace data for debugging (M-R3)      |
| Aggregated model metrics         | AI Foundry metrics dashboard         | Latency, throughput, error rate per model (M-R3) |
| User feedback                    | AI Foundry feedback API              | Correlate user ratings with model outputs (M-R3) |

All AI services must emit diagnostics to the Log Analytics workspace.
Add `Microsoft.CognitiveServices/accounts` and `Microsoft.Search/searchServices`
to the diagnostic settings module in the IaC plan.

### Model Version Management

| Practice                           | Guidance                                    |
| ---------------------------------- | ------------------------------------------- |
| Pin model version in deployment    | Never use `latest` alias in production      |
| Test model upgrades in dev first   | Schedule upgrade window; re-run eval suite  |
| Document model version in as-built | Required for compliance and reproducibility |

---

## Data

### Thread and Run State Storage (D-R1)

Use standard agent setup with customer-managed Azure resources for full data sovereignty.
See [ai-resource-model.md](ai-resource-model.md) for BYOS IaC patterns.

| Storage component      | Resource                  | Sovereignty note                              |
| ---------------------- | ------------------------- | --------------------------------------------- |
| Thread / message state | Azure Cosmos DB (BYOS)    | Required for EU data residency (GDPR Art. 44) |
| File uploads           | Azure Blob Storage (BYOS) | Per-project isolation; ZRS for durability     |
| Vector embeddings      | Azure AI Search (BYOS)    | Per-project index isolation                   |

### Storage Isolation per Project (D-R2)

Each distinct application or use case (Foundry Project) must use separate storage
components. Shared storage across projects breaks data isolation and complicates
compliance audits. See [ai-resource-model.md](ai-resource-model.md) for IaC patterns.

### Microsoft Fabric Data Integration (D-R3)

If the customer has Microsoft Fabric, surface data into AI Foundry via the
[Microsoft Fabric data agent](https://learn.microsoft.com/azure/ai-foundry/concepts/fabric-data-agent)
rather than copying datasets manually.

> **WAF/CAF fallback (no Fabric)**: Stage data into Azure Blob Storage using Azure Data
> Factory pipelines, then index via Azure AI Search for retrieval in RAG workflows.

---

## Governance

### AI Policy Governance

| Control                                       | Default effect | When to switch to Deny                       |
| --------------------------------------------- | -------------- | -------------------------------------------- |
| Azure Policy: model catalog governance        | Audit          | After baseline established in dev/staging    |
| Restrict allowed Azure OpenAI model versions  | Audit → Deny   | Before production sign-off                   |
| Require private endpoints on AI Services      | Audit → Deny   | Enforce at subscription scope for production |
| Require content safety filter ≥ Standard tier | Audit          | Escalate to Deny for regulated scopes        |

Apply these built-in Azure Policy initiatives at management group / subscription scope (G-R1).
Start with `Audit` effect on all; only switch to `Deny` after baseline is established:

| Initiative / Policy                                               | Category           |
| ----------------------------------------------------------------- | ------------------ |
| `[Preview]: Azure AI Services resources should use private links` | Network isolation  |
| Azure AI Foundry — built-in policy set                            | Foundry governance |
| Azure Machine Learning — built-in policy set (if applicable)      | ML governance      |
| Azure AI Search — require private endpoint                        | Network isolation  |
| Restrict allowed Azure OpenAI model catalog versions              | Model governance   |

> **Model governance (G-R5)**: Switching to `Deny` effect does **not** automatically remove
> already-deployed noncompliant models. Remediate existing deployments manually before
> switching. Use `Audit` first to understand usage and avoid blocking active workloads.

Map to NIST AI RMF and record compliance posture in `04-governance-constraints.md` (G-R2).

### Responsible AI Dashboard

For workloads surfacing model outputs to end users, deploy the
[Responsible AI Dashboard](https://learn.microsoft.com/azure/machine-learning/concept-responsible-ai-dashboard)
to generate model output reports (fairness, error analysis, data exploration) (G-R3).

Record `responsible_ai_dashboard: <deployed | waived with justification>` in the architecture assessment.

---

## Networking

Reference: [AI Landing Zone design checklist](https://azure.github.io/AI-Landing-Zones/architecture/design-checklist/)

### Network Gates (non-negotiable for production)

| Gate                                                              | Control                                          | Source |
| ----------------------------------------------------------------- | ------------------------------------------------ | ------ |
| Private endpoint for every PaaS AI service                        | Deploy PE in workload subnet; no public endpoint | N-R3   |
| NSG on all VNets in the AI Landing Zone                           | Deny-all inbound default; allow explicitly       | N-R4   |
| App Gateway or Azure Front Door + WAF for public-facing frontends | WAF policy in Prevention mode for production     | N-R5   |
| APIM as AI gateway for multi-team or enterprise workloads         | Required; optional for single-team internal apps | N-R6   |
| Azure Firewall + UDR for outbound traffic                         | Central (platform LZ preferred) or in AI LZ      | N-R7   |
| Private DNS Zones for all private endpoints                       | Central (platform LZ preferred) or in AI LZ      | N-R8   |
| Outbound traffic restricted by default                            | Allowlist required egress only                   | N-R9   |

### Supporting Network Controls

| Control                                    | Guidance                                                                  | Source |
| ------------------------------------------ | ------------------------------------------------------------------------- | ------ |
| DDoS protection                            | Enable at VNet level; reuse central DDoS plan from platform LZ if present | N-R1   |
| Bastion / jump box for AI developer access | Required for production; reuse central Bastion if platform LZ is present  | N-R2   |

> **Hub-spoke topology**: For enterprise deployments, place the AI gateway (APIM) in the
> hub VNet or a dedicated AI spoke peered to the hub. See
> [ai-gateway-patterns.md](ai-gateway-patterns.md) for topology decisions.
