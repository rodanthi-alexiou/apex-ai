<!-- ref:adversarial-checklist-ai-architecture-v1 -->

# Adversarial Checklist — AI Architecture Lens

Domain-specific checklist for the `ai-architecture` review lens.
Loaded by `challenger-review-subagent` when `review_focus = "ai-architecture"`.

**Activation condition**: Requirements or architecture contain AI keywords:
`Azure OpenAI`, `AI Search`, `AI Services`, `Foundry`, `RAG`, `embedding`,
`LLM`, `AI agent`, `Copilot`, `Document Intelligence`.

**Skill reference**: `.github/skills/azure-ai-architect/SKILL.md` and its `references/` subdirectory.

---

## Resource Model & Naming

| #     | Check                                                                     | Expected Evidence                                                                                                | Severity     |
| ----- | ------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- | ------------ |
| AI-01 | AI Services uses `kind: AIServices` (not deprecated `kind: Hub`)          | Resource definition shows `kind: 'AIServices'` or AVM module `cognitive-services/account`                        | `must_fix`   |
| AI-02 | Resource naming follows CAF with `aisa-` prefix for AI Services           | Naming section or resource names use `aisa-{project}-{env}` pattern                                              | `should_fix` |
| AI-03 | AI Search naming uses `srch-` prefix                                      | Resource names use `srch-{project}-{env}`                                                                        | `should_fix` |
| AI-04 | AVM modules specified for all AI resources (not raw resource definitions) | Module paths reference `br/public:avm/res/cognitive-services/account`, `br/public:avm/res/search/search-service` | `should_fix` |

## Deployment Model & Cost

| #     | Check                                                                         | Expected Evidence                                                                                | Severity     |
| ----- | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | ------------ |
| AI-05 | PTU vs PAYG decision explicitly documented with rationale                     | Section or decision record states deployment type with justification (token volume, latency SLA) | `must_fix`   |
| AI-06 | Token cost projection as separate line item in cost estimate                  | Monthly token cost estimate (input/output tokens × price per 1K tokens)                          | `should_fix` |
| AI-07 | Model deployment SKU specified (GlobalStandard, Standard, ProvisionedManaged) | Deployment configuration includes SKU name and capacity                                          | `should_fix` |
| AI-26 | EU-regulated workloads (GDPR / data residency mandate) use `DataZoneStandard` or `DataZoneProvisioned`, not `GlobalStandard` | When compliance requirements include GDPR or EU data residency: deployment SKU is `DataZoneStandard` (PAYG) or `DataZoneProvisioned` (PTU); `GlobalStandard` explicitly rejected with documented rationale | `must_fix`   |

## Security & Content Safety

| #     | Check                                                                       | Expected Evidence                                                                                                         | Severity     |
| ----- | --------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- | ------------ |
| AI-08 | `publicNetworkAccess: Disabled` on AI Services and AI Search                | Resource config or plan explicitly states public access disabled for production                                           | `must_fix`   |
| AI-09 | Private endpoints planned for AI Services, AI Search, and Cosmos DB         | Private endpoint + DNS zone configuration for `privatelink.cognitiveservices.azure.com`, `privatelink.search.windows.net` | `must_fix`   |
| AI-10 | Content safety filters enabled for public-facing inference endpoints        | Content safety configuration mentioned, or explicit statement that endpoint is internal-only                              | `should_fix` |
| AI-11 | Microsoft Defender for AI enabled (or explicitly scoped out with rationale) | Defender plan reference or documented exception                                                                           | `should_fix` |
| AI-12 | Outbound network restriction (Azure Firewall or NSG) for AI compute         | Firewall/NSG rules limiting AI service egress, or VNet integration with service endpoints                                 | `should_fix` |
| AI-27 | Threat model references MITRE ATLAS and OWASP Generative AI Top 10 for public-facing inference endpoints | Architecture assessment or threat model section acknowledges AI-specific attack vectors (prompt injection, model inversion, data poisoning) for any public-facing endpoint | `should_fix` |
| AI-28 | Prompt shielding + output monitoring explicitly enabled on public inference endpoints | Architecture states prompt shields configured via Azure AI Content Safety (distinct from standard category filters); output monitoring referenced | `should_fix` |

## Identity & Access

| #     | Check                                                                  | Expected Evidence                                                                                                                 | Severity     |
| ----- | ---------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | ------------ |
| AI-13 | Managed Identity for all AI service access (no API keys in code)       | RBAC role assignments listed; no connection strings or key references                                                             | `must_fix`   |
| AI-14 | Specific RBAC roles identified (not generic Contributor)               | Roles like `Cognitive Services OpenAI User`, `Search Index Data Contributor`, `Search Index Data Reader` with role definition IDs | `should_fix` |
| AI-15 | AI Services → AI Search grounding uses `Search Index Data Reader` role | Cross-service RBAC for on-your-data / RAG grounding access                                                                        | `should_fix` |
| AI-25 | `disableLocalAuth: true` set on AI Services AND AI Search (key-based access explicitly disabled) | Resource definitions or IaC explicitly set `disableLocalAuth: true` on AI Services and `disableLocalAuth: true; authOptions: null` on AI Search — Managed Identity usage alone is insufficient | `must_fix`   |

## AI Gateway & Traffic Management

| #     | Check                                                                  | Expected Evidence                                                                                    | Severity     |
| ----- | ---------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- | ------------ |
| AI-16 | AI gateway pattern evaluated (APIM or direct) with documented decision | If multi-team or rate-limiting needed: APIM AI gateway; if single-team: direct access with rationale | `should_fix` |
| AI-17 | Token rate limiting and quota management addressed                     | Token-per-minute limits, retry policies, or APIM token-limit policy                                  | `should_fix` |
| AI-18 | DDoS protection for public-facing AI endpoints                         | DDoS Protection Standard or WAF in front of inference endpoints                                      | `should_fix` |

## Reliability & Performance

| #     | Check                                                                           | Expected Evidence                                                                | Severity     |
| ----- | ------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- | ------------ |
| AI-19 | AI Search replica count ≥ 2 for production (99.9% SLA requirement)              | `replicaCount: 2` or higher in resource configuration                            | `must_fix`   |
| AI-20 | RAG accuracy NFR mapped to infrastructure sizing (search tier, embedding model) | If requirements state accuracy target, architecture maps it to specific SKU/tier | `should_fix` |
| AI-21 | Model failover or retry strategy documented                                     | Multi-region deployment, fallback model, or circuit breaker pattern              | `suggestion` |

## Diagnostics & Observability

| #     | Check                                                               | Expected Evidence                                                               | Severity     |
| ----- | ------------------------------------------------------------------- | ------------------------------------------------------------------------------- | ------------ |
| AI-22 | AI-specific diagnostic settings (token usage, latency, error rates) | Diagnostic settings resource targeting AI Services with metrics/logs categories | `should_fix` |
| AI-23 | Application Insights or equivalent for AI request tracing           | APM integration for tracking inference requests end-to-end                      | `suggestion` |
| AI-24 | Cost alerts for token consumption anomalies                         | Budget alerts or anomaly detection tied to AI Services consumption              | `suggestion` |
| AI-30 | Model and data drift monitoring addressed in observability plan     | Monitoring section references Foundry evaluations, custom eval pipeline, or equivalent for tracking model output quality over time (M-R5) | `should_fix` |

## Governance

| #     | Check                                                                          | Expected Evidence                                                                                                                                           | Severity     |
| ----- | ------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------ |
| AI-29 | Azure Policy model catalog governance referenced (minimum `Audit` effect)      | Architecture assessment or governance section mentions Azure Policy initiative for allowed OpenAI model versions; `Audit` effect minimum, `Deny` before prod sign-off (G-R5) | `should_fix` |

---

## Usage by Challenger Subagent

When the `ai-architecture` lens is active:

1. Load this checklist into context
2. Load `.github/skills/azure-ai-architect/SKILL.md` (quick reference table only — do NOT load all sub-references unless a specific check requires deeper verification)
3. Evaluate each check against the artifact
4. For checks that fail: create a finding with the check ID (e.g., `AI-08`), severity from the table, and a concrete suggested mitigation
5. Checks marked `must_fix` that are absent from the artifact should always generate findings
6. Checks marked `should_fix` generate findings only if there is no documented exception or rationale for omission
7. Checks marked `suggestion` generate findings only for complex projects or when the gap creates compounding risk
