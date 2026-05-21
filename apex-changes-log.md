# APEX Repo Changes Log

**Repository:** `roda-infraops-hack` (forked from APEX Accelerator)
**Branch:** `main`
**Goal:** Transform APEX into an Azure AI-first platform engineering system — every agent
in the workflow understands AI workloads natively, without wasting tokens on non-AI projects.

---

## What Was Missing from Original APEX

The upstream APEX accelerator is a general-purpose Azure IaC orchestration system. It had
**no native awareness of AI workloads**. Specifically:

| Gap                                    | Impact                                                                                                                   |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| No AI-specific requirements gathering  | Agents couldn't capture PTU/PAYG preferences, token throughput, RAG sources, or content safety needs                     |
| No AI architecture decision phase      | Architect agent had no framework for PTU vs PAYG, AI gateway patterns, or RAG architecture choices                       |
| No AI governance policy awareness      | Governance agent didn't filter for `Microsoft.CognitiveServices/*` or `Microsoft.MachineLearningServices/*` policies     |
| No AI diagram guidance                 | Design agent didn't know to include AI Landing Zone components (AI Services, AI Search, APIM gateway, private endpoints) |
| No AI-specific Bicep patterns          | CodeGen agent would hallucinate AVM module paths for AI resources                                                        |
| No Foundry agent optimization skill    | No mechanism for eval-driven parameter sweeps (temperature, model, instructions)                                         |
| No AI challenger lens                  | Adversarial review couldn't catch AI-specific gaps (content safety, token cost, RBAC role IDs)                           |
| No EU data residency rules for AI SKUs | `GlobalStandard` SKU routes inference globally — violating GDPR for regulated workloads                                  |
| No compressed AI skill variants        | Loading full `azure-ai-architect` SKILL.md at every step wastes tokens on context that's only partially needed           |

---

## Changes Made — Summary

| #   | Change                                                                                        | Date   | Files                 |
| --- | --------------------------------------------------------------------------------------------- | ------ | --------------------- |
| 1   | [Foundry FAOS Optimization sub-skill](#1-foundry-faos-optimization-sub-skill)                 | May 19 | 2 (1 new, 1 modified) |
| 2   | [AI Services AVM Bicep patterns](#2-ai-services-avm-bicep-patterns)                           | May 19 | 2 (1 new, 1 modified) |
| 3   | [EU Data Residency Fix (GlobalStandard → DataZoneStandard)](#3-eu-data-residency-fix)         | May 20 | 4 modified            |
| 4   | [Conditional AI-Architecture Challenger Lens](#4-conditional-ai-architecture-challenger-lens) | May 20 | 7 (1 new, 6 modified) |
| 5   | [End-to-End AI Workflow Integration](#5-end-to-end-ai-workflow-integration)                   | May 20 | 7 (2 new, 5 modified) |

---

## 1. Foundry FAOS Optimization Sub-Skill

**Gap addressed:** No mechanism for eval-driven parameter sweeps on AI agents.

### New: `.github/skills/microsoft-foundry/foundry-agent/faos-optimize/faos-optimize.md`

- `<!-- ref:faos-optimize-v1 -->` reference tag
- **When to Use** — four trigger conditions (eval loops, temperature tuning, batch eval,
  A/B configuration comparison)
- **FAOS Optimization Pattern** — Python code block using `AIProjectClient` that externalizes
  `AGENT_INSTRUCTIONS`, `AGENT_MODEL`, and `AGENT_TEMPERATURE` as env vars so the FAOS
  evaluator can sweep parameters without code changes
- **Required Environment Variables** table (`AGENT_INSTRUCTIONS`, `AGENT_MODEL`,
  `AGENT_TEMPERATURE`) with defaults
- **`azure.yaml` snippet** — shows how to wire the three env vars into azd's `services.env:`
  block so each environment gets its own values
- **Eval Loop Integration** — 5-step cycle: baseline → eval → optimize → compare → promote
- **WAF Reliability Mapping** table — maps RAG accuracy ≥ 80% NFR and groundedness to
  specific FAOS parameters with concrete guidance

### Modified: `.github/skills/microsoft-foundry/SKILL.md`

1. **Sub-Skills table** (line ~30): added two new rows after the existing `rbac` row:

   | Sub-Skill                  | Description                                                                                 |
   | -------------------------- | ------------------------------------------------------------------------------------------- |
   | `faos-optimize`            | Optimize agent config for FAOS eval sweeps → `foundry-agent/faos-optimize/faos-optimize.md` |
   | `resource/private-network` | Deploy Foundry with VNet isolation → `references/private-network-standard-agent-setup.md`   |

2. **Hub deprecation `[!CAUTION]` block** (line ~76): inserted before `## Agent: Setup Types`.
   Warns that `kind: Hub` / `Microsoft.MachineLearningServices/workspaces` is deprecated
   as of 2025 and redirects to `Microsoft.CognitiveServices/accounts` with `kind: AIServices`.

3. **Reference Index** (line ~126): added entry:

   ```text
   | `foundry-agent/faos-optimize/faos-optimize.md` | FAOS Optimization (eval-driven tuning) |
   ```

---

## 2. AI Services AVM Bicep Patterns

**Gap addressed:** CodeGen agent had no AVM module references for AI resources — would
hallucinate paths or emit raw resource definitions.

### New: `.github/skills/azure-bicep-patterns/references/ai-services-patterns.md`

- `<!-- ref:ai-services-patterns-v1 -->` reference tag

- **AVM Module Paths** table with minimum version pins:

  | Resource                       | AVM Module                                       | Min Version |
  | ------------------------------ | ------------------------------------------------ | ----------- |
  | AI Services (Foundry resource) | `br/public:avm/res/cognitive-services/account`   | `0.9.x`     |
  | AI Search                      | `br/public:avm/res/search/search-service`        | `0.9.x`     |
  | Cosmos DB (NoSQL)              | `br/public:avm/res/document-db/database-account` | `0.10.x`    |
  | Container Apps Environment     | `br/public:avm/res/app/managed-environment`      | `0.8.x`     |
  | Container Apps                 | `br/public:avm/res/app/container-app`            | `0.11.x`    |

- **AI Services Bicep example** — full `module` block with `kind: 'AIServices'`,
  `publicNetworkAccess: 'Disabled'`, `managedIdentities`, `deployments` array (GPT-4o,
  `GlobalStandard` SKU), and diagnostic settings

- **AI Search Bicep example** — `replicaCount: 2` (WAF Reliability HA requirement),
  `publicNetworkAccess: 'disabled'`, `authOptions` (AAD-only with `http403`)

- **Cosmos DB Bicep example** — `disableLocalAuth: true` (Entra ID-only auth),
  `publicNetworkAccess: 'Disabled'`, system-assigned identity

- **Managed Identity → RBAC Role Assignments** table with role definition IDs:

  | Assignment                          | Role Name                      | Role Definition ID                     |
  | ----------------------------------- | ------------------------------ | -------------------------------------- |
  | Container Apps → AI Services        | Cognitive Services OpenAI User | `5e0bd9bd-7b93-4f28-af87-19fc36ad61bd` |
  | Container Apps → AI Search          | Search Index Data Contributor  | `8ebe5a00-799e-43f5-93ac-243d3dce84a7` |
  | AI Services → AI Search (grounding) | Search Index Data Reader       | `1407120a-92aa-4202-b7e9-c0e197c71c8f` |

  Plus a reusable Bicep `roleAssignment` pattern using `guid()` for deterministic names.

- **Private Endpoint DNS Zone Names** table:

  | Service         | Private DNS Zone                          |
  | --------------- | ----------------------------------------- |
  | AI Services     | `privatelink.cognitiveservices.azure.com` |
  | AI Search       | `privatelink.search.windows.net`          |
  | Cosmos DB (SQL) | `privatelink.documents.azure.com`         |

- **Learn More** links to AVM registry GitHub entries for all five modules

### Modified: `.github/skills/azure-bicep-patterns/SKILL.md`

Three additions:

1. **Quick Reference table** (line ~26): added row:

   ```text
   | Azure AI Services Patterns | AI workloads: AI Services, AI Search, Cosmos DB, Container Apps |
     [ai-services-patterns](references/ai-services-patterns.md) |
   ```

2. **`## Azure AI Services Patterns` section** (line ~77): new summary section listing the
   four key rules agents must follow:
   - Use `kind: 'AIServices'` — never `kind: 'Hub'` (deprecated 2025)
   - Private endpoints are mandatory for production AI services
   - Use RBAC role assignments over keys — never use connection strings
   - `replicaCount ≥ 2` for AI Search to qualify for the 99.9% SLA

3. **Reference Index** (line ~98): added entry:

   ```text
   | [ai-services-patterns.md](references/ai-services-patterns.md) |
     AVM modules, RBAC, and private DNS for AI Services, AI Search, Cosmos DB, Container Apps |
   ```

---

## 3. EU Data Residency Fix

**Gap addressed:** `GlobalStandard` Azure OpenAI SKU routes inference globally — violating
GDPR Art.44 + NEN 7510 §13 for Dutch hospital PHI in the CareFlow AI project.

### What Changed (4 files)

| File                                                                      | Change                                                                                                                                                                                                                           |
| ------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `agent-output/careflow-ai/04-implementation-plan.md`                      | 8 occurrences of `GlobalStandard` → `DataZoneStandard`; governance constraint reference updated to `#1 + #3`                                                                                                                     |
| `agent-output/careflow-ai/04-governance-constraints.md`                   | Added Regulatory Constraint #3 (EU data residency); fixed stale `Standard` references in compliance table and deployment blockers; added GDPR/NEN 7510 rows to Security Policies table; updated Healthcare Regulatory Note       |
| `.github/skills/azure-ai-architect/references/ai-deployment-decisions.md` | SKU table expanded to 6 rows with `DataZoneStandard`, `DataZoneProvisioned`, `GlobalProvisionedManaged`; added data residency guarantee column; added decision guide defaulting to `DataZoneStandard` for EU-regulated workloads |
| `.github/skills/azure-bicep-patterns/references/ai-services-patterns.md`  | Bicep example SKU changed from `GlobalStandard` → `DataZoneStandard`; inline comment and key-parameters note updated to prohibit `GlobalStandard` for EU workloads                                                               |

### Key SKU Distinction

| SKU                | Routing                       | GDPR/NEN 7510 | Use for CareFlow AI                    |
| ------------------ | ----------------------------- | ------------- | -------------------------------------- |
| `GlobalStandard`   | Global — may leave EU/EEA     | ❌ Prohibited | Never                                  |
| `DataZoneStandard` | EU geographic zone only       | ✅ Compliant  | Default (PAYG)                         |
| `Standard`         | Region-pinned (swedencentral) | ✅ Compliant  | Fallback if DataZone quota unavailable |

### Governance Constraint #3 Summary

- **Type**: Regulatory (not Azure Policy-detected)
- **Frameworks**: GDPR Article 44, NEN 7510:2017 §13
- **Rule**: All `Microsoft.CognitiveServices/accounts/deployments` must set `sku.name = 'DataZoneStandard'`
- **Enforcement point**: Step 5 Bicep CodeGen — verified by `adversarial-checklist-ai-architecture.md` item 9

---

## 4. Conditional AI-Architecture Challenger Lens

**Gap addressed:** Adversarial review couldn't catch AI-specific gaps. The CareFlow AI
plan passed standard review but missed: content safety filters, RBAC role IDs, APIM gateway
policies, Defender for AI, AI egress firewall rules, token cost breakdown, and more (9 gaps
total).

### Why

The CareFlow AI implementation plan passed through standard challenger review (security-governance,
architecture-reliability, cost-feasibility) but missed AI-specific concerns:

1. AI resource naming (`oai-` used instead of CAF `aisa-` prefix)
2. No content safety filters specified for Azure OpenAI deployments
3. Missing Microsoft Defender for AI enrollment
4. No APIM AI gateway policies (token limits, semantic caching, jailbreak detection)
5. Missing Azure Firewall rules for AI service egress
6. No DDoS protection for AI endpoints
7. Missing AI-specific diagnostics (token metrics, model latency, RAG accuracy)
8. Generic RBAC — no specific Cognitive Services role IDs
9. No token cost breakdown (PTU vs PAYG analysis absent)

**Root cause**: The challenger subagent had no mechanism to load domain-specific AI knowledge.
Generic security/reliability/cost lenses lack the specificity to catch AI workload gaps.

### What Changed (7 files)

| File                                                                                | Change                                                                                               |
| ----------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `.github/skills/azure-defaults/references/adversarial-checklist-ai-architecture.md` | **New** — 24-item machine-actionable checklist (6 sections, must_fix/should_fix/suggestion severity) |
| `.github/agents/_subagents/challenger-review-subagent.agent.md`                     | Added `ai-architecture` lens definition, conditional skill loading section, reference index entries  |
| `.github/skills/workflow-engine/templates/workflow-graph.json`                      | Added `conditional_lenses` array to step-4, step-5b, step-5t challenger configs                      |
| `.github/agents/05-iac-planner.agent.md`                                            | Updated Phase 4.3–4.4 heading to "2–3 lenses", added conditional AI pass paragraph                   |
| `.github/agents/06b-bicep-codegen.agent.md`                                         | Updated Phase 4.5 heading to "1–4 passes", added conditional AI pass paragraph                       |
| `.github/agents/06t-terraform-codegen.agent.md`                                     | Updated Phase 4.5 heading to "1–4 passes", added conditional AI pass paragraph                       |
| `.github/skills/azure-defaults/references/adversarial-review-protocol.md`           | Added Pass 4 row (conditional) to Multi-Pass Rotating Lenses table with activation rules             |

### How It Works

1. **Keyword detection**: When `01-requirements.md` contains any of:
   `Azure OpenAI`, `AI Search`, `AI Services`, `Foundry`, `RAG`, `embedding`,
   `LLM`, `AI agent`, `Copilot`, `Document Intelligence`
2. **Additional pass triggered**: The challenger subagent is invoked with
   `review_focus = "ai-architecture"` after all standard passes complete
3. **Skill + checklist loaded**: The subagent loads `adversarial-checklist-ai-architecture.md`
   (24 items) and the `azure-ai-architect` SKILL.md for domain knowledge
4. **Standard early-exit unaffected**: The conditional pass runs independently of
   pass 2/3 early-exit decisions — if AI keywords exist, it always runs

### Design Decisions

- **Conditional, not always-on**: Avoids wasting a review pass on non-AI projects
- **Keywords from requirements (not plan)**: Requirements are available earliest;
  keyword list matches the `azure-ai-architect` skill trigger keywords
- **`adds_pass: true`**: Increases max pass count rather than replacing an existing lens
- **Checklist + skill dual-source**: Checklist provides structured items with severity;
  skill provides deeper domain reasoning for nuanced judgments

---

## 5. End-to-End AI Workflow Integration

**Gap addressed:** Even with skills and patterns available, the core agents (Requirements →
Architect → Governance → Design → Orchestrator) had no mechanism to detect AI workloads
and activate AI-specific logic. The skills existed in isolation — nothing wired them into
the pipeline.

**Design principle:** Deterministic activation via a single trigger (`## AI Workload
Requirements` H2 section in `01-requirements.md`) rather than fuzzy keyword matching.
Non-AI projects pay zero token cost — all AI logic is conditional.

### What Changed (7 files)

| File                                                 | Change                                                                                                                                                                                                                              |
| ---------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `.github/skills/azure-ai-architect/SKILL.digest.md`  | **New** — compressed skill variant (~80 lines) with Quick Reference, Key Decision tables (PTU vs PAYG, Landing Zone, Security Gates), WAF Augmentation table. Loaded at Architect level instead of full SKILL.md.                   |
| `.github/skills/azure-ai-architect/SKILL.minimal.md` | **New** — ultra-compact pointer file (~15 lines). Purpose statement + 5 reference paths + non-negotiable gates. Loaded at >80% context pressure.                                                                                    |
| `.github/agents/02-requirements.agent.md`            | Added AI Workload Detection (Phase 2) + AI Workload NFRs (Phase 3). Scans for AI keywords → outputs `## AI Workload Requirements` H2 with PTU/PAYG preference, TPM targets, RAG sources, content safety, data residency.            |
| `.github/agents/03-architect.agent.md`               | Added `### Conditional Skill: AI Workload` (loads `SKILL.digest.md` if trigger present) + `## Phase 1.6: AI Architecture Decisions` (PTU/PAYG, AI Gateway, RAG Architecture, Content Safety Gates). Sits after multi-tenancy (1.5). |
| `.github/agents/04g-governance.agent.md`             | Added AI Workload Policy Filter — scans for `Microsoft.CognitiveServices/*`, `Microsoft.MachineLearningServices/*`, `Microsoft.Search/*` namespaces in policy assignments when AI trigger is present.                               |
| `.github/agents/04-design.agent.md`                  | Added AI Landing Zone diagram guidance — AI services zone placement, private endpoint topology, APIM gateway position in architecture diagrams.                                                                                     |
| `.github/agents/01-orchestrator.agent.md`            | Added note documenting that AI conditional phases auto-activate via `## AI Workload Requirements` presence.                                                                                                                         |

### How It Works

```text
User describes AI workload
        │
        ▼
┌─────────────────────────────┐
│ 02-Requirements Agent       │  Detects AI keywords → emits
│ Phase 2: AI Detection       │  "## AI Workload Requirements" H2
│ Phase 3: AI NFRs            │  with PTU/PAYG, TPM, safety, etc.
└─────────────────────────────┘
        │
        ▼  (H2 trigger present in 01-requirements.md)
┌─────────────────────────────┐
│ 03-Architect Agent          │  Loads SKILL.digest.md (not full)
│ Conditional: AI Workload    │  Executes Phase 1.6: AI decisions
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│ 04g-Governance Agent        │  Filters for CognitiveServices/
│ AI Policy Filter            │  MachineLearningServices/Search
└─────────────────────────────┘
        │
        ▼
┌─────────────────────────────┐
│ 04-Design Agent             │  Includes AI Landing Zone
│ AI Diagram Guidance         │  components in architecture diagrams
└─────────────────────────────┘
```

### Token Efficiency

| Variant            | Size       | When Loaded                                  |
| ------------------ | ---------- | -------------------------------------------- |
| `SKILL.md` (full)  | ~400 lines | Only by dedicated AI subagents or deep dives |
| `SKILL.digest.md`  | ~80 lines  | Architect phase (conditional on AI trigger)  |
| `SKILL.minimal.md` | ~15 lines  | Any agent at >80% context pressure           |
| No load            | 0 lines    | Non-AI projects — zero overhead              |

### Trigger Keywords

Any of these in user requirements activates the AI pathway:
`Azure OpenAI`, `AI Search`, `AI Services`, `Foundry`, `RAG`, `embedding`,
`LLM`, `AI agent`, `Copilot`, `Document Intelligence`

---

## Validation

All changes pass the project validation suite:

```bash
npm run lint:agent-frontmatter   # Agent YAML frontmatter
npm run lint:skills-format       # SKILL.md format
npm run lint:md                  # Markdown linting
npm run validate:all             # Full suite
```

---

## Remaining Backlog (Not Yet Implemented)

| Item                                                     | Priority | Reason Deferred                                                          |
| -------------------------------------------------------- | -------- | ------------------------------------------------------------------------ |
| Add Foundry MCP to `.vscode/mcp.json`                    | P1       | Requires verifying `@azure/ai-foundry-mcp` package name against upstream |
| Import `azure-reliability` + `entra-agent-id` skills     | P4       | Adds new skill files — lower priority                                    |
| Correct deprecated Hub terminology in existing templates | CT       | Sweep across all existing infra/bicep templates                          |
