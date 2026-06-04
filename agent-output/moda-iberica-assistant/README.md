<!-- markdownlint-disable MD033 MD041 -->

<a id="readme-top"></a>

<div align="center">

![Status](https://img.shields.io/badge/Status-In%20Progress-yellow?style=for-the-badge)

![Step](https://img.shields.io/badge/Step-2%20of%207-blue?style=for-the-badge)

# 🏗️ moda-iberica-assistant

**Conversational AI shopping assistant for Moda Ibérica — omnichannel (web, mobile, in-store tablets) product discovery, outfit recommendations, stock checking, and FAQ handling powered by Azure OpenAI and RAG.**

[View Architecture](#-architecture) · [View Artifacts](#-generated-artifacts) · [View Progress](#-workflow-progress)

</div>

---

## 📋 Project Summary

| Property           | Value                 |
| ------------------ | --------------------- |
| **Created**        | 2026-05-28            |
| **Last Updated**   | 2026-06-01            |
| **Region**         | swedencentral         |
| **Environment**    | Dev + Production      |
| **Estimated Cost** | €15K–€30K/month (run) |
| **AVM Coverage**   | TBD%                  |

---

## ✅ Workflow Progress

<!-- Visual progress bar -->

```text
[██░░░░░░░░] 29% Complete
```

| Step | Phase          |                                    Status                                     | Artifact                                                           |
| :--: | -------------- | :---------------------------------------------------------------------------: | ------------------------------------------------------------------ |
|  1   | Requirements   |     ![Done](https://img.shields.io/badge/-Done-success?style=flat-square)     | [01-requirements.md](./01-requirements.md)                         |
|  2   | Architecture   |     ![Done](https://img.shields.io/badge/-Done-success?style=flat-square)     | [02-architecture-assessment.md](./02-architecture-assessment.md)   |
|  3   | Design         | ![Pending](https://img.shields.io/badge/-Pending-lightgrey?style=flat-square) | [03-des-\*.md](.)                                                  |
|  4   | Planning       | ![Pending](https://img.shields.io/badge/-Pending-lightgrey?style=flat-square) | [04-implementation-plan.md](./04-implementation-plan.md)           |
|  5   | Implementation | ![Pending](https://img.shields.io/badge/-Pending-lightgrey?style=flat-square) | [05-implementation-reference.md](./05-implementation-reference.md) |
|  6   | Deployment     | ![Pending](https://img.shields.io/badge/-Pending-lightgrey?style=flat-square) | [06-deployment-summary.md](./06-deployment-summary.md)             |
|  7   | Documentation  | ![Pending](https://img.shields.io/badge/-Pending-lightgrey?style=flat-square) | [07-documentation-index.md](./07-documentation-index.md)           |

> **Legend**:
> ![Done](https://img.shields.io/badge/-Done-success?style=flat-square) Complete
> | ![WIP](https://img.shields.io/badge/-WIP-yellow?style=flat-square) In Progress
> | ![Pending](https://img.shields.io/badge/-Pending-lightgrey?style=flat-square) Pending
> | ![Skip](https://img.shields.io/badge/-Skipped-blue?style=flat-square) Skipped

---

## 🏛️ Architecture

_Architecture diagram will be generated in Step 2._

### Key Resources

| Resource             | Type               | SKU      | Purpose                                  |
| -------------------- | ------------------ | -------- | ---------------------------------------- |
| Azure OpenAI         | Cognitive Services | TBD      | LLM for conversation and generation      |
| Azure AI Search      | Search Service     | TBD      | Vector/hybrid search over catalog & docs |
| Azure Container Apps | Container App      | TBD      | Application hosting with autoscale       |
| Azure Cosmos DB      | NoSQL Database     | TBD      | Session state and conversation history   |
| Azure API Management | API Gateway        | TBD      | Integration gateway + WAF                |
| Azure Blob Storage   | Storage Account    | TBD      | RAG document store                       |
| Azure Key Vault      | Key Vault          | Standard | Secrets and certificates                 |
| Azure Content Safety | AI Service         | TBD      | Content filtering for AI outputs         |
| Application Insights | Monitoring         | TBD      | Observability and telemetry              |

---

## 📄 Generated Artifacts

<details>
<summary><strong>📁 Step 1-3: Requirements, Architecture & Design</strong></summary>

| File                                       | Description                    |                                Status                                 | Created    |
| ------------------------------------------ | ------------------------------ | :-------------------------------------------------------------------: | ---------- |
| [01-requirements.md](./01-requirements.md) | Project requirements with NFRs | ![Done](https://img.shields.io/badge/-Done-success?style=flat-square) | 2026-05-28 |

</details>

---

## 🔗 Related Resources

| Resource            | Path                                                                                                               |
| ------------------- | ------------------------------------------------------------------------------------------------------------------ |
| **Bicep Templates** | [`infra/bicep/moda-iberica-assistant/`](../../infra/bicep/moda-iberica-assistant/)                                 |
| **Workflow Docs**   | [Published workflow guide](https://jonathan-vella.github.io/azure-agentic-infraops/concepts/workflow/)             |
| **Troubleshooting** | [Published troubleshooting guide](https://jonathan-vella.github.io/azure-agentic-infraops/guides/troubleshooting/) |

---

<div align="center">

**Generated by [APEX](../../README.md)** · [Report Issue](https://github.com/jonathan-vella/azure-agentic-infraops/issues/new)

<a href="#readme-top">⬆️ Back to Top</a>

</div>
