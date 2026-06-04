# moda-iberica-assistant — Handoff (Step 0 complete)

Updated: 2026-05-28 | IaC: TBD | Branch: main

## Completed Steps

- [x] Step 0 → Project initialized

## Key Decisions

- Region: swedencentral (EU GDPR-compliant)
- Compliance: GDPR, LOPDGDD, DORA readiness
- Budget: €600K year one
- IaC tool: TBD (captured in Step 1)
- Architecture pattern: TBD

## Open Challenger Findings (must_fix only)

None

## Context for Next Step

Step 1 (Requirements) will capture functional/non-functional requirements for a conversational AI shopping assistant for Moda Ibérica (~180 stores, e-commerce, €450M revenue). Key integrations: SAP Commerce Cloud catalog, OMS inventory API, Salesforce Service Cloud, SharePoint content. Multilingual (ES/CA/PT). Target: production by Oct 2026.

## Skill Context

- region: swedencentral
- tags: Environment, ManagedBy, Project, Owner
- naming_prefix: CAF abbreviations (rg-, kv-, st, etc.)
- security_baseline: TLS 1.2, HTTPS-only, no public blob, managed identity, no shared key
- avm_first: Always prefer AVM modules over raw resource definitions
- complexity: TBD (computed after Step 1)

## Artifacts

- agent-output/moda-iberica-assistant/00-session-state.json
- agent-output/moda-iberica-assistant/00-handoff.md
