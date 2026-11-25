# Computer Networks Project — Phase 2

## Harden, Recover, and Troubleshoot

**Project:** Computer Networks  
**Phase:** 2  
**Domain:** `app.team1.test`  
**Environment:** Two physical Macs with Docker Desktop  
**Primary DNS:** Ram Mac (`10.7.7.82`)  
**Active Edge:** Mukund Mac (`10.7.20.185`)

---

## 1. Project Overview

Phase 2 extends the Computer Networks Phase 1 implementation by adding:

- DNS redundancy and backup resolver
- DNS TTL and controlled DNS record changes
- Backend service isolation
- High-availability backend failover
- Controlled edge/Nginx migration
- Systematic troubleshooting across DNS, TCP, TLS, and application layers

The existing Phase 1 setup is kept intact. Phase 2 configurations, scripts, Docker files, rollback files, and evidence are maintained separately inside the `phase2/` directory.

The Phase 2 architecture uses Docker containers on two physical Macs because additional physical machines were not available. Docker provides the required isolated services while the two Macs provide separate network hosts.

---

## 2. Objectives

The Phase 2 implementation demonstrates the following:

### A. Backup DNS Resolver

A second DNS resolver is deployed on the Mukund Mac.

The system contains:

- Primary DNS on Ram Mac
- Backup DNS on Mukund Mac
- The same `app.team1.test` DNS record on both resolvers
- Client-side verification using both DNS servers
- Failure testing by stopping the primary DNS service

When the primary DNS becomes unavailable, the backup resolver continues to provide name resolution.

---

### B. DNS TTL and Controlled Record Change

The DNS record uses a short TTL of **30 seconds**.

The implementation demonstrates:

1. Initial DNS resolution
2. DNS record change
3. Observation of the previously cached answer
4. Expiration of the cached answer
5. Resolution of the new DNS address
6. Manual cache flushing
7. Controlled DNS cutover

This demonstrates how TTL affects DNS migration and why clients may continue using an old address until the cached record expires.

---

### C. Backend Service Isolation

Backend A and Backend B are protected so that they cannot be accessed directly by unauthorized clients.

The backend services are exposed through a host-side isolation gateway.

Only the active edge host:

```text
10.7.20.185
```

is allowed to access the backend gateway ports:

```text
3001
3002
```

Unauthorized sources are denied.

The original firewall/rollback configuration is retained under:

```text
phase2/rollback/
```

---

### D. High Availability and Backend Failover

Two backend services are deployed:

```text
Backend A → port 3001
Backend B → port 3002
```

The active NGINX edge maintains both backends in an upstream pool.

Under normal operation:

```text
Client
   ↓
Active Edge NGINX
   ↓
Backend A / Backend B
```

When Backend A is stopped, NGINX detects that it is unavailable and continues serving requests through Backend B.

After Backend A is restored, it becomes available to the upstream pool again.

The active edge NGINX remains a potential single point of failure.

---

### E. Controlled Edge Migration

A standby NGINX edge is deployed on the Ram Mac.

The standby edge uses the same application domain:

```text
app.team1.test
```

DNS is changed from the active edge:

```text
10.7.20.185
```

to the standby edge:

```text
10.7.7.82
```

Because the DNS TTL is 30 seconds, clients may temporarily continue using the old address.

After TTL expiry, new DNS resolution points clients to the standby edge.

This demonstrates controlled edge migration without requiring new hardware.

---

### F. Troubleshooting

A systematic troubleshooting workflow is demonstrated across four layers:

```text
DNS
 ↓
TCP
 ↓
TLS
 ↓
Application
```

The troubleshooting evidence covers:

- DNS resolution failure
- TCP connectivity verification
- TLS handshake and certificate presentation
- Application-level HTTPS response

This allows failures to be isolated to the appropriate network/application layer rather than treating every failure as an application problem.

---

# 3. Network Architecture

The Phase 2 deployment uses two physical Macs.

### Ram Mac

```text
Hostname: MacBook-Pro-93.local
IP:       10.7.7.82
```

Hosts:

- Primary DNS
- Backend A
- Backend B
- Standby NGINX
- Backend isolation gateway

### Mukund Mac

```text
Hostname: Mukunds-MacBook-Pro.local
IP:       10.7.20.185
```

Hosts:

- Active Edge NGINX
- Backup DNS

---

## 4. High-Level Request Flow

Normal application request:

```text
Client
   │
   │ DNS query
   ▼
Primary DNS
10.7.7.82:53
   │
   │ app.team1.test
   ▼
Active Edge NGINX
10.7.20.185:443
   │
   │ HTTPS proxy
   ▼
Backend Gateway
10.7.7.82:3001 / 3002
   │
   ├──────────────► Backend A
   │                10.7.7.82:3001
   │
   └──────────────► Backend B
                    10.7.7.82:3002
```

During edge migration:

```text
Client
   │
   │ DNS after TTL expiry
   ▼
Standby NGINX
10.7.7.82:443
   │
   ├──► Backend A
   │
   └──► Backend B
```

---

# 5. Docker Architecture

The backend services and supporting services are containerized using Docker.

The main internal Docker network on the Ram Mac is:

```text
docker_phase2-internal
```

Subnet:

```text
172.18.0.0/16
```

Important container addresses include:

```text
Backend A      172.18.0.5
Backend B      172.18.0.3
Primary DNS    172.18.0.4
Standby NGINX  172.18.0.2
Cache Resolver 172.18.0.6
```

Docker provides service isolation while the two physical Macs provide separate network locations for the active and backup infrastructure.

---

# 6. Directory Structure

```text
phase2/
├── README.md
├── architecture.md
├── ip-service-table.md
├── request-flow.md
├── phase2-report.md
├── final-demo-checklist.md
├── viva-preparation.md
│
├── docker/
│   ├── compose-ram.yml
│   ├── compose-mukund.yml
│   ├── backend-a/
│   ├── backend-b/
│   ├── primary-dns/
│   ├── backup-dns/
│   ├── edge-nginx/
│   └── standby-nginx/
│
├── configuration/
│   ├── dns/
│   ├── nginx/
│   ├── tls/
│   └── firewall/
│
├── scripts/
│   ├── start-phase2.sh
│   ├── stop-phase2.sh
│   ├── status-phase2.sh
│   ├── backup-dns-test.sh
│   ├── stop-primary-dns.sh
│   ├── restore-primary-dns.sh
│   ├── dns-ttl-test.sh
│   ├── dns-cutover.sh
│   ├── dns-cache-flush.sh
│   ├── backend-isolation-test.sh
│   ├── apply-firewall-rules.sh
│   ├── rollback-firewall.sh
│   ├── fail-backend-a.sh
│   ├── restore-backend-a.sh
│   ├── fail-both-backends.sh
│   ├── restore-both-backends.sh
│   ├── edge-migration.sh
│   ├── restore-primary-edge.sh
│   └── troubleshooting/
│
├── evidence/
│   ├── 01-topology/
│   ├── 03-primary-dns/
│   ├── 04-backup-dns/
│   ├── 09-dns-ttl/
│   ├── 10-backend-isolation/
│   ├── 11-ha-failover/
│   ├── 12-edge-migration/
│   └── 13-troubleshooting/
│
└── rollback/
```

The `tests/` directory was intentionally removed because the required validation is already represented by the Phase 2 scripts and evidence.

---

# 7. Evidence Organization

Evidence is organized by Phase 2 functionality.

### `01-topology`

Contains topology and service inventory evidence.

### `03-primary-dns`

Contains primary DNS status, logs, and resolution evidence.

### `04-backup-dns`

Contains backup DNS resolution and primary-DNS failure evidence.

### `09-dns-ttl`

Contains DNS caching, TTL expiry, and new-record resolution evidence.

### `10-backend-isolation`

Contains allowed and blocked backend access evidence.

### `11-ha-failover`

Contains backend failure, continued service through Backend B, and backend restoration evidence.

### `12-edge-migration`

Contains active-edge state, DNS cutover, cached DNS state, TTL expiry, and final standby-edge operation.

### `13-troubleshooting`

Contains DNS, TCP, TLS, and application troubleshooting evidence.

Evidence files are kept in text and/or screenshot form so that the evaluator can verify the result without repeating the entire experiment.

---

# 8. Rollback Strategy

Phase 2 changes are reversible.

Rollback material is stored separately under:

```text
phase2/rollback/
```

Important rollback material includes:

- Previous NGINX configuration
- Previous Docker Compose configuration
- Previous firewall/PF configuration
- Configuration required to restore the primary edge
- Configuration required to restore backend access

The rollback principle is:

```text
Change
  ↓
Test
  ↓
Capture Evidence
  ↓
Rollback if Required
```

Phase 1 files are not modified as part of this Phase 2 implementation.

---

# 9. Operational Principle

The Phase 2 system follows a layered approach:

```text
DNS
 ↓
Network/TCP
 ↓
TLS
 ↓
Edge/Proxy
 ↓
Backend
 ↓
Application
```

Each layer can be independently tested.

For example:

- If DNS fails, verify the resolver.
- If DNS works but TCP fails, verify connectivity/firewall/port availability.
- If TCP works but TLS fails, inspect the certificate and TLS configuration.
- If TLS succeeds but the application fails, inspect NGINX and backend services.

This layered troubleshooting model is used in the final demonstration.

---

# 10. Key Demonstrated Outcomes

The Phase 2 implementation demonstrates:

| Requirement | Result |
|---|---|
| Backup DNS | Implemented |
| Primary DNS failure | Demonstrated |
| DNS TTL | 30 seconds |
| Controlled DNS cutover | Demonstrated |
| Backend isolation | Implemented |
| Unauthorized backend access | Blocked |
| Backend A/B HA | Implemented |
| Backend A failure | Demonstrated |
| Backend recovery | Demonstrated |
| Standby edge | Implemented |
| Controlled edge migration | Demonstrated |
| DNS/TCP/TLS/Application troubleshooting | Demonstrated |
| Rollback configuration | Maintained |

---

# 11. Important Addresses

| Component | Host | Address |
|---|---|---|
| Ram Mac | Physical host | `10.7.7.82` |
| Mukund Mac | Physical host | `10.7.20.185` |
| Primary DNS | Ram | `10.7.7.82:53` |
| Backup DNS | Mukund | `10.7.20.185:53` |
| Active Edge | Mukund | `10.7.20.185:443` |
| Standby Edge | Ram | `10.7.7.82:443` |
| Backend A | Ram | `10.7.7.82:3001` |
| Backend B | Ram | `10.7.7.82:3002` |
| Application | DNS name | `app.team1.test` |

---

# 12. Phase 2 Completion

Phase 2 is considered complete when the evaluator can verify the complete flow:

```text
Client
  │
  ▼
DNS Resolution
  │
  ▼
Active / Standby Edge
  │
  ▼
Isolated Backend Gateway
  │
  ├──► Backend A
  │
  └──► Backend B
```

and the following failure/recovery scenarios:

```text
Primary DNS Failure
        ↓
Backup DNS

Backend A Failure
        ↓
Backend B

Active Edge Migration
        ↓
Standby Edge

DNS / TCP / TLS / Application Failure
        ↓
Layer-by-Layer Diagnosis
```

All Phase 2 configuration, automation, rollback material, and evidence are maintained inside the `phase2/` directory.