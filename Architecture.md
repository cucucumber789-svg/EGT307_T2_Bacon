# Architecture — Smart Environmental Monitoring System

## Overview

This document outlines the overall system architecture, repository structure,
technology decisions, and deployment strategy for the Smart Environmental
Monitoring System. The system uses a **microservices architecture** orchestrated
by **Docker** and **Kubernetes**.

---

## System Architecture (High-Level)

```
┌─────────────────────┐
│  Frontend Dashboard │
│   (TBD)             │
└────────┬────────────┘
         │ REST API
         ▼
┌─────────────────────┐        ┌─────────────────────┐
│   Backend API       │◄──────►│   ML Service        │
│   (Flask + PySpark) │        │   (TBD)             │
└────────┬────────────┘        └─────────────────────┘
         │ SQL
         ▼
┌─────────────────────┐
│   PostgreSQL DB     │
└─────────────────────┘
```

All four microservices are containerised with Docker and deployed via Kubernetes.

---

## Repository File Structure

```
EGT307_T2_Bacon/
├── README.md
├── Architecture.md
├── docker-compose.yml
│
├── backend-api/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── spark_session.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── routers/
│   │   └── services/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
│
├── ml-service/
│   ├── (TBD)
│   └── Dockerfile
│
├── frontend/
│   ├── (TBD)
│   └── Dockerfile
│
├── database/
│   └── init.sql
│
└── k8s/
    ├── backend-api/
    │   ├── deployment.yaml
    │   ├── service.yaml
    │   └── configmap.yaml
    ├── ml-service/
    ├── database/
    └── frontend/
```

---

## Technology Decisions

| Component        | Technology      | Justification                                            |
|------------------|-----------------|----------------------------------------------------------|
| Backend API      | Flask + PySpark | Flask for lightweight HTTP; PySpark for large-scale      |
|                  |                 | sensor data processing (module recommendation).          |
| Database         | PostgreSQL      | Strong relational support for structured sensor data;    |
|                  |                 | ACID compliance; mature tooling.                         |
| ORM              | SQLAlchemy      | Standard Python ORM; decouples app logic from SQL.       |
| Containerisation | Docker          | Consistent runtime across environments; single-command   |
|                  |                 | startup via docker-compose.                              |
| Orchestration    | Kubernetes      | Automated deployment, scaling, self-healing, and load    |
|                  |                 | balancing across microservices.                          |
| Frontend         | (TBD)           | To be decided by the frontend team member.               |
| ML Service       | (TBD)           | To be co-developed; framework and model approach pending. |

---

## Microservice Communication

| From              | To                | Protocol  | Purpose                          |
|-------------------|-------------------|-----------|----------------------------------|
| Frontend          | Backend API       | REST/HTTP | User requests, data display      |
| Backend API       | PostgreSQL        | SQL       | Data persistence & retrieval     |
| Backend API       | ML Service        | REST/HTTP | Anomaly prediction requests      |
| ML Service        | Backend API       | REST/HTTP | Prediction results returned      |

---

## Docker & Kubernetes Strategy

### Docker
- Each microservice has its own `Dockerfile`
- `docker-compose.yml` at root for local multi-service development
- Environment variables injected via `.env` files or ConfigMaps

### Kubernetes
- Separate YAML manifests per service under `k8s/`
- ConfigMaps for environment configuration
- Services for internal DNS-based inter-service communication
- Deployments with replica counts for scalability

---

## Open Decisions (Pending Team Discussion)

The following items have **not yet been finalised** and are subject to change:

1. **PySpark Usage Scope** — How Spark will be used in the backend is
   undecided. Options include batch aggregation, preprocessing for ML, or
   running Spark MLlib models directly.

2. **Sensor Data Input Format** — The format in which sensor data arrives
   (CSV uploads, JSON API payloads, or IoT streaming) has not been determined.

3. **ML Service API Contract** — The interface between Backend API and ML
   Service needs to be defined collaboratively before integration.

4. **ML Service Technology Stack** — The ML microservice's framework, model
   format, and serving approach are yet to be decided.

5. **Frontend Framework** — The frontend dashboard framework (React, Vue,
   or other) is pending team decision.

6. **Team Role Assignments** — Specific responsibilities for each member
   are to be confirmed and documented in README.md.

---
