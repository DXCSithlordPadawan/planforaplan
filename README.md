# AI Application Generator — Documentation Index

**Version:** 2.0  
**Date:** March 2026  
**Application:** AI Application Generator  
**Stack:** Python 3.11+ · FastAPI · Jinja2 · Podman

---

## Overview

This folder contains the complete planning and requirements documentation for an AI-powered web application generator. The system is designed to transform natural language requirements into fully functional web applications within a five-minute demonstration window.

The core functionality enables users to describe a web application in plain English, review and approve an AI-generated implementation plan, and receive a running application that launches automatically in their browser. This dramatically accelerates the prototyping and demonstration process by eliminating the traditional gap between conceptualization and working prototype.

The system is built entirely in Python, using FastAPI for the orchestration backend and serving a lightweight frontend using Jinja2 templating with Tailwind CSS via CDN. Generated applications are also Python-based (FastAPI + Jinja2), eliminating any dependency on Node.js, npm, or frontend build tooling.

---

## Document Library

| # | Document | Audience | Description |
|---|----------|----------|-------------|
| 01 | [Architecture Guide](/app/docs/01-ARCHITECTURE.md) | Developers, Architects | Complete internal and external architecture: component breakdown, module reference, data flows, request lifecycles, security architecture, Mermaid diagrams |
| 02 | [User Guide](/app/docs/02-USER-GUIDE.md) | End Users, Presenters | Step-by-step workflow, writing effective requirements, troubleshooting, FAQ |
| 03 | [API Guide](/app/docs/03-API-GUIDE.md) | Developers, Integrators | All REST endpoints and WebSocket, request/response schemas, cURL and Python examples |
| 04 | [Support Tasks Guide](/app/docs/04-SUPPORT-TASKS.md) | L1/L2/L3 Support, SysAdmins | Support tiers, diagnostic steps, common errors, health check procedures, escalation checklist |
| 05 | [RACI Document](/app/docs/05-RACI.md) | All Teams | Responsibility assignment matrix for development, operations, security, support, and documentation activities |
| 06 | [RBAC Document](/app/docs/06-RBAC.md) | Security Officer, DevOps | Role definitions, permission matrix, file system access, container permissions, credential handling, gaps and roadmap |
| 07 | [Security Analysis and Compliance](/app/docs/07-SECURITY-COMPLIANCE.md) | Security Officer, Auditors | Threat model, OWASP Top 10 mapping, NIST SP 800-53 mapping, FIPS 140-3, DISA STIG, CIS L2, CWE analysis, known gaps |
| 08 | [Maintenance Guide](/app/docs/08-MAINTENANCE-GUIDE.md) | DevOps, Lead Developer | Routine schedule, dependency updates, security scanning, base template maintenance, Python upgrades, AI model updates |
| 09 | [Deployment Guide](/app/docs/09-DEPLOYMENT-GUIDE.md) | DevOps, SysAdmins | Windows and Linux installation, environment configuration, development and production modes, reverse proxy, troubleshooting |
| 10 | [Container Build Guide](/app/docs/10-CONTAINER-BUILD-GUIDE.md) | DevOps, SysAdmins | Containerfile walkthrough, Podman build and run commands, hardened runtime flags, volumes, image scanning, air-gapped deployment |

---

## Quick Reference

### Starting the Application

**Windows:**
```cmd
cd C:\path\to\app
start.bat
```

**Linux / macOS:**
```bash
cd /path/to/app
./start.sh
```
→ Open `http://127.0.0.1:8000`

### Running Tests

**Windows:** `test.bat`  
**Linux / macOS:** `./test.sh`

### Building the Container

```bash
podman build -t ai-app-generator:2.0 -f Containerfile .
podman run -d --name ai-app-gen -p 127.0.0.1:8000:8000 --env-file .env ai-app-generator:2.0
```

### Health Check

```bash
curl http://127.0.0.1:8000/api/health
```

---

## Compliance Standards

| Standard | Coverage Document |
|----------|-----------------|
| FIPS 140-3 | [07-SECURITY-COMPLIANCE.md](/app/docs/07-SECURITY-COMPLIANCE.md) |
| NIST SP 800-53 Rev 5 | [07-SECURITY-COMPLIANCE.md](/app/docs/07-SECURITY-COMPLIANCE.md) |
| OWASP Top 10 2021 | [07-SECURITY-COMPLIANCE.md](/app/docs/07-SECURITY-COMPLIANCE.md) |
| DISA STIG Application Security | [07-SECURITY-COMPLIANCE.md](/app/docs/07-SECURITY-COMPLIANCE.md) |
| CIS Benchmark Level 2 | [07-SECURITY-COMPLIANCE.md](/app/docs/07-SECURITY-COMPLIANCE.md), [10-CONTAINER-BUILD-GUIDE.md](/app/docs/10-CONTAINER-BUILD-GUIDE.md) |
| RBAC / NIST AC-2, AC-3, AC-6 | [06-RBAC.md](/app/docs/06-RBAC.md) |

---

*All documents are maintained in `app/docs/`*

