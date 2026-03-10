# AI Application Generator — RACI Document

**Version:** 2.1
**Date:** 2026-03-10
**Standard:** RACI (Responsible, Accountable, Consulted, Informed)

---

## Table of Contents

1. [Role Definitions](#1-role-definitions)
2. [RACI Key](#2-raci-key)
3. [Development and Release Activities](#3-development-and-release-activities)
4. [Operations Activities](#4-operations-activities)
5. [Security Activities](#5-security-activities)
6. [Support Activities](#6-support-activities)
7. [AI Provider Management](#7-ai-provider-management)
8. [Documentation Activities](#8-documentation-activities)

---

## 1. Role Definitions

| Role | Description |
|------|-------------|
| **Application Owner** | Business owner of the product; makes final decisions on scope and priorities |
| **Lead Developer** | Develops and maintains application code; owns the codebase |
| **DevOps / Sysadmin** | Manages deployments, infrastructure, container builds, and environment configuration |
| **QA Engineer** | Owns test strategy, test execution, and quality gates |
| **Security Officer** | Reviews security controls, approves compliance posture, handles incidents |
| **L1 Support** | First line of user-facing support; handles configuration and usage queries |
| **L2 Support** | Second line; handles environment, server, and deployment issues |
| **End User** | The person using the application to generate and deploy apps |

---

## 2. RACI Key

| Code | Meaning |
|------|---------|
| **R** | **Responsible** — does the work |
| **A** | **Accountable** — final decision authority; signs off |
| **C** | **Consulted** — provides input before action |
| **I** | **Informed** — notified after action |

---

## 3. Development and Release Activities

| Activity | App Owner | Lead Dev | DevOps | QA | Security Officer |
|----------|-----------|----------|--------|----|-----------------|
| Define new feature requirements | A | C | I | C | C |
| Design architecture changes | C | R/A | C | I | C |
| Implement application code | I | R/A | I | C | C |
| Write unit and integration tests | I | R | I | A | I |
| Conduct code review | C | A | I | R | C |
| Run security scan (bandit) | I | R | I | C | A |
| Run dependency audit (pip-audit) | I | R | I | C | A |
| Run type checking (mypy) and linting (ruff) | I | R/A | I | C | I |
| Approve release for deployment | A | C | C | C | C |
| Tag and version release | I | R/A | C | I | I |
| Update documentation | I | R | C | C | I |

---

## 4. Operations Activities

| Activity | App Owner | Lead Dev | DevOps | QA | Security Officer |
|----------|-----------|----------|--------|----|-----------------|
| Install Python environment and dependencies (`setup.bat`/`setup.ps1`) | I | C | R/A | I | I |
| Configure `.env` file for deployment | I | C | R/A | I | C |
| Start the orchestrator server (`start.bat`/`start.ps1`) | I | I | R/A | I | I |
| Build Podman container image | I | C | R/A | I | C |
| Run container image | I | C | R/A | I | C |
| Monitor server health (`/api/health`) | I | I | R/A | I | I |
| Apply dependency updates | I | C | R/A | C | A |
| Rotate AI provider API keys | A | I | C | I | R |
| Manage base template venv | I | R/A | C | I | I |
| Monitor port availability (8000, 8001) | I | I | R/A | I | I |

---

## 5. Security Activities

| Activity | App Owner | Lead Dev | DevOps | QA | Security Officer |
|----------|-----------|----------|--------|----|-----------------|
| Define security requirements | A | C | C | I | R |
| Implement security controls (middleware, path validation, certifi) | I | R/A | I | C | C |
| Conduct security review of new code | I | C | I | C | R/A |
| Resolve bandit HIGH findings | A | R | I | C | C |
| Resolve pip-audit CRITICAL/HIGH CVEs | A | R | C | I | C |
| Maintain Security Analysis document | I | C | I | I | R/A |
| Respond to a security incident | A | C | C | I | R |
| Review RBAC roles and permissions | A | C | C | I | R |
| Approve FIPS 140-3 compliance posture | A | C | I | I | R |

---

## 6. Support Activities

| Activity | App Owner | L1 Support | L2 Support | Lead Dev | DevOps |
|----------|-----------|-----------|-----------|----------|--------|
| Handle user API key errors | I | R/A | I | I | I |
| Handle user configuration questions (all providers) | I | R/A | I | I | I |
| Diagnose server startup failures | I | C | R/A | C | C |
| Resolve port conflict issues | I | I | R/A | C | C |
| Diagnose template generation warnings | I | C | C | R/A | I |
| Escalate code-level defects | I | R | C | A | I |
| Communicate outages to users | A | R | C | I | I |
| Document workarounds in support guide | I | R | C | A | I |

---

## 7. AI Provider Management

| Activity | App Owner | Lead Dev | DevOps | Security Officer |
|----------|-----------|----------|--------|-----------------|
| Select AI provider(s) for use | A | C | I | C |
| Obtain and manage API keys | A | I | C | R |
| Monitor API usage and costs | A | I | C | I |
| Respond to provider rate limit issues | I | R/A | I | I |
| Evaluate new AI providers | A | R | I | C |
| Update `create_provider` factory for new provider | I | R/A | I | I |
| Update `ConfigRequest.provider` pattern | I | R/A | I | C |
| Update provider dropdown in UI template | I | R/A | I | I |

---

## 8. Documentation Activities

| Activity | App Owner | Lead Dev | DevOps | QA | Security Officer |
|----------|-----------|----------|--------|----|-----------------|
| Maintain Architecture Guide | I | R/A | C | I | C |
| Maintain User Guide | C | R | I | C | I |
| Maintain API Guide | I | R/A | I | C | I |
| Maintain Deployment Guide | I | C | R/A | C | C |
| Maintain Container Build Guide | I | C | R/A | I | C |
| Maintain Security Analysis document | I | C | I | I | R/A |
| Maintain RACI document | A | C | C | C | C |
| Maintain RBAC document | A | C | C | I | R |
| Maintain Maintenance Guide | I | C | R/A | C | I |
| Maintain Support Tasks Guide | I | C | C | C | I |
| Maintain Bug Fix Log | I | R/A | I | I | I |
| Review all docs on each major release | A | R | R | R | R |

---

*Document maintained at `C:\planforaplan\docs\05-RACI.md`*
