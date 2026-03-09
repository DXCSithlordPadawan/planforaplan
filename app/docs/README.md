# AI Application Generator — Documentation Index

**Version:** 2.0  
**Date:** March 2026  
**Application:** AI Application Generator  
**Stack:** Python 3.11+ · FastAPI · Jinja2 · Podman

---

## Document Library

| # | Document | Audience | Description |
|---|----------|----------|-------------|
| 01 | [Architecture Guide](01-ARCHITECTURE.md) | Developers, Architects | Complete internal and external architecture: component breakdown, module reference, data flows, request lifecycles, security architecture, Mermaid diagrams |
| 02 | [User Guide](02-USER-GUIDE.md) | End Users, Presenters | Step-by-step workflow, writing effective requirements, troubleshooting, FAQ |
| 03 | [API Guide](03-API-GUIDE.md) | Developers, Integrators | All REST endpoints and WebSocket, request/response schemas, cURL and Python examples |
| 04 | [Support Tasks Guide](04-SUPPORT-TASKS.md) | L1/L2/L3 Support, SysAdmins | Support tiers, diagnostic steps, common errors, health check procedures, escalation checklist |
| 05 | [RACI Document](05-RACI.md) | All Teams | Responsibility assignment matrix for development, operations, security, support, and documentation activities |
| 06 | [RBAC Document](06-RBAC.md) | Security Officer, DevOps | Role definitions, permission matrix, file system access, container permissions, credential handling, gaps and roadmap |
| 07 | [Security Analysis and Compliance](07-SECURITY-COMPLIANCE.md) | Security Officer, Auditors | Threat model, OWASP Top 10 mapping, NIST SP 800-53 mapping, FIPS 140-3, DISA STIG, CIS L2, CWE analysis, known gaps |
| 08 | [Maintenance Guide](08-MAINTENANCE-GUIDE.md) | DevOps, Lead Developer | Routine schedule, dependency updates, security scanning, base template maintenance, Python upgrades, AI model updates |
| 09 | [Deployment Guide](09-DEPLOYMENT-GUIDE.md) | DevOps, SysAdmins | Windows and Linux installation, environment configuration, development and production modes, reverse proxy, troubleshooting |
| 10 | [Container Build Guide](10-CONTAINER-BUILD-GUIDE.md) | DevOps, SysAdmins | Containerfile walkthrough, Podman build and run commands, hardened runtime flags, volumes, image scanning, air-gapped deployment |

---

## Quick Reference

### Starting the Application

```cmd
cd C:\saabdemo\app
start.bat
```
→ Open `http://127.0.0.1:8000`

### Running Tests

```cmd
test.bat
```

### Building the Container

```cmd
podman build -t ai-app-generator:2.0 -f Containerfile .
podman run -d --name ai-app-gen -p 127.0.0.1:8000:8000 --env-file .env ai-app-generator:2.0
```

### Health Check

```cmd
curl http://127.0.0.1:8000/api/health
```

---

## Compliance Standards

| Standard | Coverage Document |
|----------|-----------------|
| FIPS 140-3 | [07-SECURITY-COMPLIANCE.md](07-SECURITY-COMPLIANCE.md) |
| NIST SP 800-53 Rev 5 | [07-SECURITY-COMPLIANCE.md](07-SECURITY-COMPLIANCE.md) |
| OWASP Top 10 2021 | [07-SECURITY-COMPLIANCE.md](07-SECURITY-COMPLIANCE.md) |
| DISA STIG Application Security | [07-SECURITY-COMPLIANCE.md](07-SECURITY-COMPLIANCE.md) |
| CIS Benchmark Level 2 | [07-SECURITY-COMPLIANCE.md](07-SECURITY-COMPLIANCE.md), [10-CONTAINER-BUILD-GUIDE.md](10-CONTAINER-BUILD-GUIDE.md) |
| RBAC / NIST AC-2, AC-3, AC-6 | [06-RBAC.md](06-RBAC.md) |

---

*All documents are maintained in `C:\saabdemo\app\docs\`*
