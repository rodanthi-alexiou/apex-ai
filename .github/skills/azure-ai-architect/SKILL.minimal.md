<!-- minimal:auto-generated from SKILL.md — do not edit manually -->

# Azure AI Architect (Minimal)

WAF-aligned AI workload architecture. Triggers: `Azure OpenAI`, `AI Search`, `Foundry`, `RAG`, `LLM`, `AI agent`.

**References** (load on demand):

- `references/ai-deployment-decisions.md` — PTU vs PAYG, token cost projection
- `references/ai-waf-checklist.md` — Security gates, reliability NFRs, networking
- `references/ai-resource-model.md` — Resource types, AVM paths, RBAC
- `references/ai-gateway-patterns.md` — APIM AI gateway, Access Contracts
- `references/ai-landing-zone-patterns.md` — Landing zone patterns

**Non-negotiable gates**: private endpoints on AI Services (prod), content safety on public endpoints, `kind: AIServices` (not Hub).

Read `SKILL.md` or `SKILL.digest.md` for full content.
