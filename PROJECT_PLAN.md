# Data Migration Program Plan (On-Prem to Azure)

## Project Summary
### As-Is
- Disparate on-premises OLTP, data marts, and batch ETL jobs with limited lineage and inconsistent data quality checks.
- Point-to-point integrations; change management handled via manual scripts and ad-hoc release cycles.
- Reporting latencies measured in hours to days; limited real-time capabilities.

### To-Be
- Cloud-first data platform on Azure with governed lakehouse + warehouse patterns.
- Near real-time ingestion for critical domains and standardized batch pipelines for non-critical sources.
- Unified metadata, lineage, and quality checks with automated CI/CD and environment parity.

## Project Description
### Activities
1. **Discovery & Assessment (Weeks 1-4)**
   - Inventory data sources, pipelines, SLAs, and dependencies.
   - Classify datasets by criticality, latency requirements, and regulatory constraints.
2. **Architecture & Design (Weeks 3-6)**
   - Define target architecture: landing zone, ingestion, processing, serving, and governance.
   - Select patterns (CDC, streaming, ELT/ETL, medallion zones).
3. **Build & Migrate (Weeks 6-20)**
   - Stand up core platform services, CI/CD, and monitoring.
   - Migrate prioritized domains in waves; implement automated validation.
4. **Validation & Cutover (Weeks 18-24)**
   - Parallel runs; data reconciliation; performance tuning.
   - Decommission on-prem workloads and finalize handover.

### Methodology
- Agile delivery with 2-week sprints.
- Wave-based migration by business domain.
- Quality gates at each stage: data completeness, accuracy, and latency.

### Timeline (High-Level)
- **Months 1-2**: Assessment, architecture, foundation.
- **Months 2-5**: Migration waves 1-3; platform hardening.
- **Months 5-6**: Final cutover and optimization.

## Technology Stack
### Core Platform (Azure)
- **Data Lake**: ADLS Gen2
- **Compute**: Azure Databricks or Synapse Spark
- **Streaming**: Azure Event Hubs + Structured Streaming
- **Warehouse**: Azure Synapse Analytics (Dedicated or Serverless)
- **Orchestration**: Azure Data Factory
- **Catalog/Governance**: Microsoft Purview

### CI/CD
- **Source Control**: GitHub
- **Pipelines**: GitHub Actions
- **IaC**: Terraform + Azure DevOps Environments (or GitHub Environments)
- **Secrets**: Azure Key Vault
- **Quality Gates**: unit tests, data tests, and policy checks

## Code
### Repo Structure (Proposed)
```
/infra
  /terraform
/data-pipelines
  /ingestion
  /transform
  /tests
/docs
```

### Example: Data Quality Check (PySpark)
```python
from pyspark.sql import functions as F

def assert_non_null(df, columns):
    violations = df.select([
        F.count(F.when(F.col(c).isNull(), c)).alias(c) for c in columns
    ]).collect()[0].asDict()
    if any(v > 0 for v in violations.values()):
        raise ValueError(f"Nulls detected: {violations}")
```

## Budget Breakdown (Estimate)
| Category | Description | Cost (USD) | Justification |
| --- | --- | ---: | --- |
| Cloud Infrastructure | ADLS, Databricks/Synapse, Event Hubs | 320,000 | Core compute/storage to run ingestion, processing, and analytics. |
| Data Migration Tools | CDC connectors, replication tooling | 90,000 | Accelerates migration and reduces downtime. |
| Security & Governance | Purview, Key Vault, IAM controls | 70,000 | Compliance and access control requirements. |
| Observability | Monitoring, logging, alerting | 45,000 | Ensures SLA compliance and stability. |
| Labor (Engineering) | Data engineers, platform engineers | 900,000 | Core build and migration execution. |
| Training & Enablement | Upskilling and onboarding | 60,000 | Ensure internal adoption and long-term sustainability. |
| Contingency (10%) | Risk buffer | 148,500 | Mitigate unknowns and scope changes. |
| **Total** |  | **1,633,500** |  |

## Communication Plan
- **Steering Committee**: Monthly review with executives.
- **Program Sync**: Weekly cross-team updates.
- **Technical Standups**: Twice weekly engineering standups.
- **Release Notes**: Bi-weekly updates to business stakeholders.
- **Risk Register**: Reviewed every sprint.

## Documentation
- **Architecture Diagrams**: Current vs target state.
- **Data Contracts**: Schemas, SLAs, and ownership.
- **Runbooks**: Incident response and operational playbooks.
- **Migration Playbooks**: Wave-by-wave execution guides.
- **Knowledge Base**: FAQs and onboarding content.
