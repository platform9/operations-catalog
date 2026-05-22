#!/bin/bash
# bulk_load.sh — POSTs all PE Catalog entries from Confluence to your local API
# Usage: bash bulk_load.sh
# Make sure your API is running first: python app.py

BASE="http://localhost:5000"

post() {
  curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE/catalog" \
    -H "Content-Type: application/json" \
    -d "$1"
}

echo "Loading PE Catalog entries..."

# ── JumpCloud ──────────────────────────────────────────────────────────────────
STATUS=$(post '{
  "serviceName": "JumpCloud",
  "description": "Platform9'\''s centralized identity administrative platform. This provides access to critical organizational services that all employees will use. The administrator role for JumpCloud is operated and governed by the Platform Engineer team uniquely.",
  "status": "Active",
  "serviceCategory": "Supported Service",
  "serviceSubjectMatterExperts": ["Platform Engineering"],
  "criticalDependencies": ["Active employment credentials", "Internet connectivity"],
  "documentation": [
    "https://platform9.atlassian.net/wiki/spaces/OP/pages/1697612030",
    "https://platform9.atlassian.net/wiki/spaces/OP/pages/3561259017",
    "https://platform9.atlassian.net/wiki/spaces/~117646495/pages/3135406106"
  ],
  "SLA": {"availability": "Accessible and logins succeed", "responseTimes": "UNDEFINED", "resolutionTargets": "UNDEFINED"},
  "targetAudience": "All of Platform9",
  "requestsChannel": "Platform Engineering",
  "incidentManagement": "Escalation to Platform Engineering or the SRE team via FireHydrant Incident response procedure",
  "monitoringTools": "UNDEFINED",
  "activeMaintenanceWindows": "UNDEFINED",
  "onboardingDocumentation": "https://platform9.atlassian.net/wiki/spaces/OP/pages/484868286",
  "costModel": "External information needed",
  "versionInformation": "N/A — JumpCloud does not have versioned releases as it operates as a continuously delivered product",
  "deprecationPolicy": "External information needed"
}')
echo "JumpCloud: $STATUS"

# ── GitHub ─────────────────────────────────────────────────────────────────────
STATUS=$(post '{
  "serviceName": "GitHub",
  "description": "Source control and code repository for the PF9 organization. PE also supports GitHub Runners for CICD efforts.",
  "status": "Active",
  "serviceCategory": "Supported Service",
  "serviceSubjectMatterExperts": ["Platform Engineering", "Engineering"],
  "criticalDependencies": ["GitHub hosted"],
  "documentation": ["https://github.com/platform9"],
  "SLA": {"availability": "GitHub hosted", "responseTimes": "GitHub hosted", "resolutionTargets": "GitHub hosted"},
  "targetAudience": "Any Platform9 code contributors or consumers of automated processes including source control and CICD",
  "requestsChannel": "Platform Engineering",
  "incidentManagement": "Escalation to Platform Engineering or the SRE team via FireHydrant Incident response procedure",
  "monitoringTools": "UNDEFINED",
  "activeMaintenanceWindows": "UNDEFINED",
  "onboardingDocumentation": "https://platform9.atlassian.net/wiki/spaces/OP/pages/484868286",
  "costModel": "Need licensing or pricing information. GitHub Runner costing model TBD",
  "versionInformation": "N/A",
  "deprecationPolicy": "N/A"
}')
echo "GitHub: $STATUS"

# ── 1Password ──────────────────────────────────────────────────────────────────
STATUS=$(post '{
  "serviceName": "1Password",
  "description": "Centralized secret management tool for all of Platform9",
  "status": "Active",
  "serviceCategory": "Supported Services",
  "serviceSubjectMatterExperts": ["Platform Engineering"],
  "criticalDependencies": ["JumpCloud SSO"],
  "documentation": [
    "https://platform9.atlassian.net/wiki/spaces/OP/pages/3100540929",
    "https://platform9.atlassian.net/wiki/spaces/OP/pages/5863768119",
    "https://platform9.atlassian.net/wiki/spaces/OP/pages/5865996325",
    "https://platform9.atlassian.net/wiki/spaces/OP/pages/5864161294"
  ],
  "SLA": {"availability": "TBD", "responseTimes": "TBD", "resolutionTargets": "TBD"},
  "targetAudience": "All of Platform9",
  "requestsChannel": "Platform Engineering",
  "incidentManagement": "Escalation to Platform Engineering or the SRE team via FireHydrant Incident response procedure",
  "monitoringTools": "TBD",
  "activeMaintenanceWindows": "N/A",
  "onboardingDocumentation": "https://platform9.atlassian.net/wiki/spaces/OP/pages/484868286",
  "costModel": "TBD",
  "versionInformation": "https://releases.1password.com/mac/stable/#changelog",
  "deprecationPolicy": "Migration to a new secret management platform would be an Epic value of an effort"
}')
echo "1Password: $STATUS"

# ── Twingate ───────────────────────────────────────────────────────────────────
STATUS=$(post '{
  "serviceName": "TwinGate",
  "description": "Platform9'\''s VPN service which is required for accessing internal resources",
  "status": "Active",
  "serviceCategory": "Operated Services",
  "serviceSubjectMatterExperts": ["Platform Engineering"],
  "criticalDependencies": ["Downloaded the Twingate client", "2FA configured"],
  "documentation": ["https://platform9.atlassian.net/wiki/spaces/OP/pages/3531440165"],
  "SLA": {"availability": "24/7", "responseTimes": "TBD", "resolutionTargets": "TBD"},
  "targetAudience": "All of Platform9 to access internal resources",
  "requestsChannel": "Platform Engineering",
  "incidentManagement": "Escalation to Platform Engineering or the SRE team via FireHydrant Incident response procedure",
  "monitoringTools": "N/A",
  "activeMaintenanceWindows": "N/A (TBD)",
  "onboardingDocumentation": "https://platform9.atlassian.net/wiki/spaces/OP/pages/484868286",
  "costModel": "TBD — includes cost for Twingate service itself and connectors provisioned in AWS VPCs",
  "versionInformation": "2025.227.17625 | 0.173.2",
  "deprecationPolicy": "TBD"
}')
echo "TwinGate: $STATUS"

# ── GroundCover ────────────────────────────────────────────────────────────────
STATUS=$(post '{
  "serviceName": "GroundCover",
  "description": "Kubernetes focused platform for monitoring and observability used by Platform9 (specifically PCD)",
  "status": "Active",
  "serviceCategory": "Operated Services and Supported Services",
  "serviceSubjectMatterExperts": ["Platform Engineering"],
  "criticalDependencies": ["AWS EKS", "RBAC Connectivity on 443", "eBPF sensors or oTEL collectors"],
  "documentation": [
    "https://platform9.atlassian.net/wiki/spaces/OP/pages/5218598939",
    "https://platform9.atlassian.net/wiki/spaces/OP/pages/5218271259"
  ],
  "SLA": {"availability": "Needs definition", "responseTimes": "UNDEFINED", "resolutionTargets": "UNDEFINED"},
  "targetAudience": "All Platform9 technical audiences",
  "requestsChannel": "Platform Engineering",
  "incidentManagement": "Escalation to Platform Engineering or the SRE team via FireHydrant Incident response procedure",
  "monitoringTools": "VictorOps alerting on the groundcover namespaces",
  "activeMaintenanceWindows": "N/A",
  "onboardingDocumentation": "https://platform9.atlassian.net/wiki/spaces/~712020d2fc698b634546a7a98747393af83698/pages/5372149761",
  "costModel": "https://app.groundcover.com/grafana/d/df9nyvr0coow0b/draft-cost-signals",
  "versionInformation": "1.9.763",
  "deprecationPolicy": "Migration to a new monitoring platform would be an Epic value of an effort"
}')
echo "GroundCover: $STATUS"

# ── ECR Registries ─────────────────────────────────────────────────────────────
STATUS=$(post '{
  "serviceName": "ECR Registries",
  "description": "Various artifacts that PE provides with AWS ECR",
  "status": "Active",
  "serviceCategory": "Supported Services",
  "serviceSubjectMatterExperts": ["Platform Engineering"],
  "criticalDependencies": ["AWS"],
  "documentation": ["https://platform9.atlassian.net/wiki/spaces/OP/pages/5513183235"],
  "SLA": {"availability": "Deferred to AWS", "responseTimes": "Deferred to AWS", "resolutionTargets": "Deferred to AWS"},
  "targetAudience": "Engineering teams",
  "requestsChannel": "Platform Engineering",
  "incidentManagement": "Escalation to Platform Engineering or the SRE team via FireHydrant Incident response procedure",
  "monitoringTools": "TBD",
  "activeMaintenanceWindows": "N/A",
  "onboardingDocumentation": "https://platform9.atlassian.net/wiki/spaces/OP/pages/5513183235",
  "costModel": "https://platform9.atlassian.net/wiki/spaces/OP/pages/5579931683",
  "versionInformation": "N/A",
  "deprecationPolicy": "We would need to identify a new artifact registry technology to migrate to"
}')
echo "ECR Registries: $STATUS"

# ── Velero ─────────────────────────────────────────────────────────────────────
STATUS=$(post '{
  "serviceName": "Velero",
  "description": "Velero provides a K8s backup and restoration process for PCD DUs",
  "status": "Active",
  "serviceCategory": "Operated Services",
  "serviceSubjectMatterExperts": ["Platform Engineering"],
  "criticalDependencies": ["Access to S3 buckets specified from the Velero backup process"],
  "documentation": ["https://platform9.atlassian.net/wiki/spaces/PCD/pages/5315952651"],
  "SLA": {"availability": "velero-backup retention: 720h, volume-snapshot-12h retention: 168h", "responseTimes": "UNDEFINED", "resolutionTargets": "UNDEFINED"},
  "targetAudience": "Restoration usage is performed by the Platform Engineering team",
  "requestsChannel": "Platform Engineering",
  "incidentManagement": "Escalation to Platform Engineering or the SRE team via FireHydrant Incident response procedure",
  "monitoringTools": "No alerts configured if a Velero backup fails",
  "activeMaintenanceWindows": "N/A",
  "onboardingDocumentation": "https://platform9.atlassian.net/wiki/spaces/PCD/pages/5315952651",
  "costModel": "TBD",
  "versionInformation": "https://github.com/platform9/pmo-v2-tf-cicd/tree/main/modules/apps/velero",
  "deprecationPolicy": "Moving to a different backup and restore process would be an effort"
}')
echo "Velero: $STATUS"

# ── Splunk On-call/VictorOps ───────────────────────────────────────────────────
STATUS=$(post '{
  "serviceName": "Splunk On-call/VictorOps",
  "description": "Team based on-call alerting platform for Staging and Production readiness and operations. Administered by PE",
  "status": "Active",
  "serviceCategory": "Operated Services || Supported Services",
  "serviceSubjectMatterExperts": ["Platform Engineering"],
  "criticalDependencies": ["SSO"],
  "documentation": ["https://platform9.atlassian.net/wiki/spaces/SUP/pages/4473192454"],
  "SLA": {"availability": "TBD", "responseTimes": "TBD", "resolutionTargets": "TBD"},
  "targetAudience": "Platform Engineering and SRE team",
  "requestsChannel": "Platform Engineering",
  "incidentManagement": "Escalation to Platform Engineering or the SRE team via FireHydrant Incident response procedure",
  "monitoringTools": "N/A",
  "activeMaintenanceWindows": "N/A",
  "onboardingDocumentation": "https://platform9.atlassian.net/wiki/spaces/OP/pages/484868286",
  "costModel": "TBD",
  "versionInformation": "N/A",
  "deprecationPolicy": "TBD (other options considered)"
}')
echo "Splunk On-call/VictorOps: $STATUS"

# ── TeamCity ───────────────────────────────────────────────────────────────────
STATUS=$(post '{
  "serviceName": "TeamCity",
  "description": "CICD tooling for PCD version builds",
  "status": "Active",
  "serviceCategory": "Supported Services",
  "serviceSubjectMatterExperts": ["Engineering"],
  "criticalDependencies": ["N/A"],
  "documentation": ["https://platform9.atlassian.net/wiki/spaces/OP/pages/50397349"],
  "SLA": {"availability": "TBD", "responseTimes": "TBD", "resolutionTargets": "TBD"},
  "targetAudience": "Developers of Platform9 products and audiences for building artifacts",
  "requestsChannel": "Platform Engineering",
  "incidentManagement": "Escalation to Platform Engineering or the SRE team via FireHydrant Incident response procedure",
  "monitoringTools": "Needs implementation",
  "activeMaintenanceWindows": "N/A",
  "onboardingDocumentation": "https://platform9.atlassian.net/wiki/spaces/OP/pages/484868286",
  "costModel": "TBD",
  "versionInformation": "N/A",
  "deprecationPolicy": "Moving away from TeamCity to another CICD build tool will require a significant effort"
}')
echo "TeamCity: $STATUS"

# ── S3 Artifacts ───────────────────────────────────────────────────────────────
STATUS=$(post '{
  "serviceName": "S3 Artifacts",
  "description": "Various S3 buckets that Platform Engineering owns to provide certain artifacts for consumption from various stakeholders within Platform9",
  "status": "Active",
  "serviceCategory": "Supported Services",
  "serviceSubjectMatterExperts": ["Platform Engineering"],
  "criticalDependencies": ["IAM permissions", "SAML auth to AWS"],
  "documentation": [
    "https://platform9.atlassian.net/wiki/spaces/OP/pages/5293080590",
    "https://platform9.atlassian.net/wiki/spaces/PCD/pages/5622824981"
  ],
  "SLA": {"availability": "Deferred to AWS", "responseTimes": "Deferred to AWS", "resolutionTargets": "Deferred to AWS"},
  "targetAudience": "External customers that rely on the Support Bundle feature. Internal employees.",
  "requestsChannel": "Platform Engineering",
  "incidentManagement": "Escalation to Platform Engineering or the SRE team via FireHydrant Incident response procedure",
  "monitoringTools": "TBD",
  "activeMaintenanceWindows": "N/A",
  "onboardingDocumentation": "N/A",
  "costModel": "AWS S3 pricing models",
  "versionInformation": "N/A",
  "deprecationPolicy": "New methods of sharing artifacts would be a technology shift"
}')
echo "S3 Artifacts: $STATUS"

# ── GuardDuty ──────────────────────────────────────────────────────────────────
STATUS=$(post '{
  "serviceName": "GuardDuty",
  "description": "Threat and anomaly detection service hosted by AWS",
  "status": "Active",
  "serviceCategory": "Supported Services",
  "serviceSubjectMatterExperts": ["Platform Engineering"],
  "criticalDependencies": ["AWS SLA"],
  "documentation": [
    "https://platform9.atlassian.net/wiki/spaces/OP/pages/4874895544",
    "https://platform9.atlassian.net/browse/INF-3332"
  ],
  "SLA": {"availability": "Deferred to AWS", "responseTimes": "UNDEFINED", "resolutionTargets": "UNDEFINED"},
  "targetAudience": "Platform Engineering",
  "requestsChannel": "Platform Engineering",
  "incidentManagement": "Escalation to Platform Engineering or the SRE team via FireHydrant Incident response procedure",
  "monitoringTools": "N/A",
  "activeMaintenanceWindows": "N/A",
  "onboardingDocumentation": "N/A",
  "costModel": "Cost Explorer in AWS",
  "versionInformation": "N/A",
  "deprecationPolicy": "N/A"
}')
echo "GuardDuty: $STATUS"

# ── Bork ───────────────────────────────────────────────────────────────────────
STATUS=$(post '{
  "serviceName": "Bork",
  "description": "Internally hosted K8s API service which manages and deploys the infra and subsequent regions for a DU (Deployment Unit)",
  "status": "Active",
  "serviceCategory": "Operated Services",
  "serviceSubjectMatterExperts": ["Platform Engineering", "Thomas Dell", "Ben Smith"],
  "criticalDependencies": ["Bork1: consul and kplane", "Bork2: consul", "Bork3: N/A"],
  "documentation": [
    "https://github.com/platform9/bork",
    "https://github.com/platform9/bork/tree/master/docs/generated"
  ],
  "SLA": {"availability": "UNDEFINED", "responseTimes": "UNDEFINED", "resolutionTargets": "UNDEFINED"},
  "targetAudience": "Any internal Platform9 employees that are deploying a DU",
  "requestsChannel": "Platform Engineering",
  "incidentManagement": "Escalation to Platform Engineering or the SRE team via FireHydrant Incident response procedure",
  "monitoringTools": "Uptime Kuma monitoring of namespace health",
  "activeMaintenanceWindows": "Maintenance window must be communicated and agreed upon by the Platform Engineering team",
  "onboardingDocumentation": "https://github.com/platform9/bork",
  "costModel": "Internally developed (N/A)",
  "versionInformation": "See Swagger Documentation — k get deployment (look at image tag)",
  "deprecationPolicy": "Bork1 and Bork2 will be fully deprecated after all customers are moved to Bork3"
}')
echo "Bork: $STATUS"

# ── Stikked ────────────────────────────────────────────────────────────────────
STATUS=$(post '{
  "serviceName": "Stikked",
  "description": "Secure file sharing tool used internally within Platform9",
  "status": "Active",
  "serviceCategory": "Operated Services || Supported Services",
  "serviceSubjectMatterExperts": ["Platform Engineering"],
  "criticalDependencies": ["TwinGate connection"],
  "documentation": ["https://stikked.platform9.horse/"],
  "SLA": {"availability": "N/A", "responseTimes": "N/A", "resolutionTargets": "N/A"},
  "targetAudience": "All Platform9",
  "requestsChannel": "Platform Engineering",
  "incidentManagement": "Escalation to Platform Engineering or the SRE team via FireHydrant Incident response procedure",
  "monitoringTools": "N/A",
  "activeMaintenanceWindows": "N/A",
  "onboardingDocumentation": "https://platform9.atlassian.net/wiki/spaces/OP/pages/639565831",
  "costModel": "N/A",
  "versionInformation": "N/A",
  "deprecationPolicy": "N/A"
}')
echo "Stikked: $STATUS"

# ── Prometheus ─────────────────────────────────────────────────────────────────
STATUS=$(post '{
  "serviceName": "Prometheus",
  "description": "Monitoring platform used to scrape metrics that are fed into Grafana",
  "status": "Active",
  "serviceCategory": "Operated Services and Supported Services",
  "serviceSubjectMatterExperts": ["Platform Engineering"],
  "criticalDependencies": ["AWS EKS"],
  "documentation": [
    "https://platform9.atlassian.net/wiki/spaces/MON/pages/584713444",
    "https://platform9.atlassian.net/wiki/spaces/MON/pages/524911194",
    "https://platform9.atlassian.net/wiki/spaces/PM/pages/519569497"
  ],
  "SLA": {"availability": "TBD", "responseTimes": "TBD", "resolutionTargets": "TBD"},
  "targetAudience": "Platform Engineering and SRE team",
  "requestsChannel": "Platform Engineering",
  "incidentManagement": "Escalation to Platform Engineering or the SRE team via FireHydrant Incident response procedure",
  "monitoringTools": "N/A",
  "activeMaintenanceWindows": "TBD",
  "onboardingDocumentation": "N/A",
  "costModel": "TBD",
  "versionInformation": "TBD",
  "deprecationPolicy": "Sunsetting Prometheus will require replacement of current alerts"
}')
echo "Prometheus: $STATUS"

# ── Tempus ─────────────────────────────────────────────────────────────────────
STATUS=$(post '{
  "serviceName": "Tempus",
  "description": "Tool for Platform9 customer upgrade scheduling. Supports automatic upgrade schedule generation, viewing and editing upgrade metadata, triggering upgrades, and pushing/retrieving Platform9 release information",
  "status": "Active",
  "serviceCategory": "Operated Services",
  "serviceSubjectMatterExperts": ["Platform Engineering"],
  "criticalDependencies": ["PF9Deploy"],
  "documentation": ["https://platform9.atlassian.net/wiki/spaces/OP/pages/404553815"],
  "SLA": {"availability": "TBD", "responseTimes": "TBD", "resolutionTargets": "TBD"},
  "targetAudience": "Platform Engineering",
  "requestsChannel": "Platform Engineering",
  "incidentManagement": "Escalation to Platform Engineering or the SRE team via FireHydrant Incident response procedure",
  "monitoringTools": "TBD",
  "activeMaintenanceWindows": "TBD",
  "onboardingDocumentation": "N/A",
  "costModel": "TBD",
  "versionInformation": "https://github.com/platform9/pf9-tempus",
  "deprecationPolicy": "TBD"
}')
echo "Tempus: $STATUS"

# ── Loki ───────────────────────────────────────────────────────────────────────
STATUS=$(post '{
  "serviceName": "Loki",
  "description": "Backend service for Grafana logging and metric collection",
  "status": "Active",
  "serviceCategory": "Operated Services",
  "serviceSubjectMatterExperts": ["Platform Engineering"],
  "criticalDependencies": ["Grafana"],
  "documentation": [
    "https://grafana.com/docs/loki/latest/get-started/components/",
    "https://platform9.atlassian.net/wiki/spaces/PM/pages/4188078086"
  ],
  "SLA": {"availability": "TBD", "responseTimes": "TBD", "resolutionTargets": "TBD"},
  "targetAudience": "Platform Engineering and SRE Team",
  "requestsChannel": "Platform Engineering",
  "incidentManagement": "Escalation to Platform Engineering or the SRE team via FireHydrant Incident response procedure",
  "monitoringTools": "N/A",
  "activeMaintenanceWindows": "TBD",
  "onboardingDocumentation": "https://platform9.atlassian.net/wiki/spaces/PM/pages/3666608133",
  "costModel": "Monitoring account AWS spending",
  "versionInformation": "TBD",
  "deprecationPolicy": "Sunsetting Loki will require replacement of current alerts"
}')
echo "Loki: $STATUS"

# ── Whistle ────────────────────────────────────────────────────────────────────
STATUS=$(post '{
  "serviceName": "Whistle",
  "description": "Internally developed monitoring system",
  "status": "Active",
  "serviceCategory": "Operated Services",
  "serviceSubjectMatterExperts": ["Platform Engineering", "Thomas Dell"],
  "criticalDependencies": ["TBD"],
  "documentation": [
    "https://platform9.atlassian.net/wiki/spaces/OP/pages/502891110",
    "https://sales.platform9.horse/"
  ],
  "SLA": {"availability": "TBD", "responseTimes": "TBD", "resolutionTargets": "TBD"},
  "targetAudience": "Platform Engineering on-call and SRE on-call",
  "requestsChannel": "Platform Engineering",
  "incidentManagement": "Escalation to Platform Engineering or the SRE team via FireHydrant Incident response procedure",
  "monitoringTools": "Not applicable",
  "activeMaintenanceWindows": "Not applicable",
  "onboardingDocumentation": "Not currently onboarding new alerts into Whistle for PMK or PCD",
  "costModel": "Internally developed",
  "versionInformation": "https://platform9.atlassian.net/wiki/spaces/OP/pages/490897569",
  "deprecationPolicy": "Sunsetting Whistle will require replacement of current alerts"
}')
echo "Whistle: $STATUS"

# ── PF9Deploy ──────────────────────────────────────────────────────────────────
STATUS=$(post '{
  "serviceName": "PF9Deploy",
  "description": "Life Cycle management tool which stores the source of truth for DUs",
  "status": "Active",
  "serviceCategory": "Operated Services",
  "serviceSubjectMatterExperts": ["Platform Engineering", "Thomas Dell", "Gaurav Gavhane"],
  "criticalDependencies": ["Celery pod", "RDS"],
  "documentation": ["https://platform9.atlassian.net/wiki/spaces/OP/pages/3350593545"],
  "SLA": {"availability": "Needs definition", "responseTimes": "UNDEFINED", "resolutionTargets": "UNDEFINED"},
  "targetAudience": "Internal Platform9",
  "requestsChannel": "Platform Engineering",
  "incidentManagement": "Escalation to Platform Engineering or the SRE team via FireHydrant Incident response procedure",
  "monitoringTools": "N/A",
  "activeMaintenanceWindows": "N/A",
  "onboardingDocumentation": "N/A",
  "costModel": "N/A",
  "versionInformation": "https://github.com/platform9/pf9-deploy",
  "deprecationPolicy": "Major effort required to rework the existing standard deployment of DUs"
}')
echo "PF9Deploy: $STATUS"

# ── PCD Manager ────────────────────────────────────────────────────────────────
STATUS=$(post '{
  "serviceName": "PCD Manager",
  "description": "Full-stack dashboard built with the Next.js framework used to manage Platform9 Private Cloud Directors (PCDs) across different regions",
  "status": "Active",
  "serviceCategory": "Operated Services",
  "serviceSubjectMatterExperts": ["Platform Engineering"],
  "criticalDependencies": ["Bork"],
  "documentation": ["https://platform9.atlassian.net/wiki/spaces/SUP/pages/5217878017"],
  "SLA": {"availability": "TBD", "responseTimes": "TBD", "resolutionTargets": "TBD"},
  "targetAudience": "Any internal Platform9 users deploying a DU",
  "requestsChannel": "Platform Engineering",
  "incidentManagement": "Escalation to Platform Engineering or the SRE team via FireHydrant Incident response procedure",
  "monitoringTools": "TBD",
  "activeMaintenanceWindows": "Needs clarification if there is criticality to when it can be updated",
  "onboardingDocumentation": "https://platform9.atlassian.net/wiki/spaces/SUP/pages/5399805954",
  "costModel": "N/A",
  "versionInformation": "https://github.com/platform9/support-toolkit/tree/master/PCD_Manager",
  "deprecationPolicy": "N/A"
}')
echo "PCD Manager: $STATUS"

# ── AlertManager ───────────────────────────────────────────────────────────────
STATUS=$(post '{
  "serviceName": "AlertManager",
  "description": "Alert management service for routing and handling operational alerts",
  "status": "Active",
  "serviceCategory": "Operated Services || Supported Services",
  "serviceSubjectMatterExperts": ["Platform Engineering"],
  "criticalDependencies": ["TBD"],
  "documentation": [
    "https://platform9.atlassian.net/wiki/spaces/OP/pages/3785588769",
    "https://platform9.atlassian.net/wiki/spaces/OP/pages/4591779871"
  ],
  "SLA": {"availability": "TBD", "responseTimes": "TBD", "resolutionTargets": "TBD"},
  "targetAudience": "SRE and Platform Engineering",
  "requestsChannel": "Platform Engineering",
  "incidentManagement": "Escalation to Platform Engineering or the SRE team via FireHydrant Incident response procedure",
  "monitoringTools": "N/A",
  "activeMaintenanceWindows": "N/A",
  "onboardingDocumentation": "N/A",
  "costModel": "TBD",
  "versionInformation": "TBD",
  "deprecationPolicy": "TBD"
}')
echo "AlertManager: $STATUS"

# ── Hosted/Delegated DNS ───────────────────────────────────────────────────────
STATUS=$(post '{
  "serviceName": "Hosted/Delegated DNS",
  "description": "Route53 hosted zones for various Platform9 domains",
  "status": "Active",
  "serviceCategory": "Operated Services || Supported Services",
  "serviceSubjectMatterExperts": ["Platform Engineering"],
  "criticalDependencies": ["Delegated zones (TBD)"],
  "documentation": ["https://platform9.atlassian.net/wiki/spaces/OP/pages/1111326734"],
  "SLA": {"availability": "Primarily deferred to AWS SLAs", "responseTimes": "UNDEFINED", "resolutionTargets": "UNDEFINED"},
  "targetAudience": "All users and customers of Platform9 products",
  "requestsChannel": "Platform Engineering",
  "incidentManagement": "Escalation to Platform Engineering or the SRE team via FireHydrant Incident response procedure",
  "monitoringTools": "Needs further implementation",
  "activeMaintenanceWindows": "TBD",
  "onboardingDocumentation": "TBD",
  "costModel": "N/A",
  "versionInformation": "N/A",
  "deprecationPolicy": "N/A"
}')
echo "Hosted/Delegated DNS: $STATUS"

# ── Cost Consulting ────────────────────────────────────────────────────────────
STATUS=$(post '{
  "serviceName": "Cost Consulting",
  "description": "Platform Engineering'\''s contribution to SaaS cost analysis",
  "status": "Active",
  "serviceCategory": "Operated Services || Supported Services",
  "serviceSubjectMatterExperts": ["Platform Engineering"],
  "criticalDependencies": ["N/A"],
  "documentation": ["https://app.groundcover.com/grafana/d/df9nyvr0coow0b/draft-cost-signals"],
  "SLA": {"availability": "N/A", "responseTimes": "N/A", "resolutionTargets": "N/A"},
  "targetAudience": "Any internal customers in Platform9",
  "requestsChannel": "Platform Engineering",
  "incidentManagement": "Escalation to Platform Engineering or the SRE team via FireHydrant Incident response procedure",
  "monitoringTools": "N/A",
  "activeMaintenanceWindows": "N/A",
  "onboardingDocumentation": "N/A",
  "costModel": "https://app.groundcover.com/grafana/d/df9nyvr0coow0b/draft-cost-signals",
  "versionInformation": "N/A",
  "deprecationPolicy": "N/A"
}')
echo "Cost Consulting: $STATUS"

# ── Technical Consulting ───────────────────────────────────────────────────────
STATUS=$(post '{
  "serviceName": "Technical Consulting",
  "description": "Platform Engineering'\''s contribution to application architecture design and analysis",
  "status": "Active",
  "serviceCategory": "Supported Services",
  "serviceSubjectMatterExperts": ["Platform Engineering"],
  "criticalDependencies": ["N/A"],
  "documentation": ["N/A"],
  "SLA": {"availability": "N/A", "responseTimes": "N/A", "resolutionTargets": "N/A"},
  "targetAudience": "All Platform9 teams who are scoping out a new implementation of technology or tooling",
  "requestsChannel": "Platform Engineering",
  "incidentManagement": "Escalation to Platform Engineering or the SRE team via FireHydrant Incident response procedure",
  "monitoringTools": "N/A",
  "activeMaintenanceWindows": "N/A",
  "onboardingDocumentation": "N/A",
  "costModel": "N/A",
  "versionInformation": "N/A",
  "deprecationPolicy": "N/A"
}')
echo "Technical Consulting: $STATUS"

# ── Kaapi Infrastructure (stub — page has no content yet) ─────────────────────
STATUS=$(post '{
  "serviceName": "Kaapi Infrastructure",
  "description": "TBD",
  "status": "TBD",
  "serviceCategory": "Operated Services || Supported Services",
  "serviceSubjectMatterExperts": ["Platform Engineering"],
  "criticalDependencies": [],
  "documentation": [],
  "SLA": {"availability": "TBD", "responseTimes": "TBD", "resolutionTargets": "TBD"},
  "targetAudience": "TBD",
  "requestsChannel": "Platform Engineering",
  "incidentManagement": "Escalation to Platform Engineering or the SRE team via FireHydrant Incident response procedure",
  "monitoringTools": "TBD",
  "activeMaintenanceWindows": "TBD",
  "onboardingDocumentation": "TBD",
  "costModel": "TBD",
  "versionInformation": "TBD",
  "deprecationPolicy": "TBD"
}')
echo "Kaapi Infrastructure: $STATUS"

# ── PCDV RPM Package Upload (stub — page has no content yet) ──────────────────
STATUS=$(post '{
  "serviceName": "PCDV RPM Package Upload",
  "description": "TBD",
  "status": "TBD",
  "serviceCategory": "Operated Services || Supported Services",
  "serviceSubjectMatterExperts": ["Platform Engineering"],
  "criticalDependencies": [],
  "documentation": [],
  "SLA": {"availability": "TBD", "responseTimes": "TBD", "resolutionTargets": "TBD"},
  "targetAudience": "TBD",
  "requestsChannel": "Platform Engineering",
  "incidentManagement": "Escalation to Platform Engineering or the SRE team via FireHydrant Incident response procedure",
  "monitoringTools": "TBD",
  "activeMaintenanceWindows": "TBD",
  "onboardingDocumentation": "TBD",
  "costModel": "TBD",
  "versionInformation": "TBD",
  "deprecationPolicy": "TBD"
}')
echo "PCDV RPM Package Upload: $STATUS"

# ── Employee Onboard/Offboard (stub — page has no content yet) ────────────────
STATUS=$(post '{
  "serviceName": "Employee Onboard/Offboard",
  "description": "TBD",
  "status": "TBD",
  "serviceCategory": "Operated Services || Supported Services",
  "serviceSubjectMatterExperts": ["Platform Engineering"],
  "criticalDependencies": [],
  "documentation": [],
  "SLA": {"availability": "TBD", "responseTimes": "TBD", "resolutionTargets": "TBD"},
  "targetAudience": "TBD",
  "requestsChannel": "Platform Engineering",
  "incidentManagement": "Escalation to Platform Engineering or the SRE team via FireHydrant Incident response procedure",
  "monitoringTools": "TBD",
  "activeMaintenanceWindows": "TBD",
  "onboardingDocumentation": "TBD",
  "costModel": "TBD",
  "versionInformation": "TBD",
  "deprecationPolicy": "TBD"
}')
echo "Employee Onboard/Offboard: $STATUS"

# ── Claude AI (stub — page has no content yet) ────────────────────────────────
STATUS=$(post '{
  "serviceName": "Claude AI",
  "description": "TBD",
  "status": "TBD",
  "serviceCategory": "Operated Services || Supported Services",
  "serviceSubjectMatterExperts": ["Platform Engineering"],
  "criticalDependencies": [],
  "documentation": [],
  "SLA": {"availability": "TBD", "responseTimes": "TBD", "resolutionTargets": "TBD"},
  "targetAudience": "TBD",
  "requestsChannel": "Platform Engineering",
  "incidentManagement": "Escalation to Platform Engineering or the SRE team via FireHydrant Incident response procedure",
  "monitoringTools": "TBD",
  "activeMaintenanceWindows": "TBD",
  "onboardingDocumentation": "TBD",
  "costModel": "TBD",
  "versionInformation": "TBD",
  "deprecationPolicy": "TBD"
}')
echo "Claude AI: $STATUS"

echo ""
echo "Done. Check above for HTTP 201 (success) on each entry."
echo "View all entries: curl http://localhost:5000/catalog | python -m json.tool"
