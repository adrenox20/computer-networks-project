# Computer Networks — Phase 2 Report

## Harden, Recover, and Troubleshoot

---

# 1. Introduction

Phase 2 extends the Computer Networks Phase 1 implementation by introducing resilience, controlled failure recovery, service isolation, DNS migration, and systematic troubleshooting.

The implementation was completed using two physical Mac systems with Docker Desktop used for service isolation and deployment.

The two hosts used in the Phase 2 implementation are:

| Host | IP Address | Primary Role |
|---|---|---|
| Ram Mac | `10.7.7.82` | Primary DNS, backends, standby edge |
| Mukund Mac | `10.7.20.185` | Active edge, backup DNS |

The application domain used throughout the implementation is:

```text
app.team1.test
```

The major Phase 2 components are:

- Primary DNS
- Backup DNS
- Active NGINX edge
- Standby NGINX edge
- Backend A
- Backend B
- Backend isolation gateway
- DNS cache/TTL testing environment
- Troubleshooting workflow

---

# 2. Phase 2 Objectives

The Phase 2 implementation was designed to demonstrate six major capabilities:

1. **Backup DNS Resolver**
2. **DNS TTL and Controlled Record Change**
3. **Backend Service Isolation**
4. **Backend High Availability and Failover**
5. **Controlled Edge Migration**
6. **Layer-by-Layer Troubleshooting**

The implementation also maintains rollback configurations so that Phase 2 changes can be reversed without modifying the original Phase 1 implementation.

---

# 3. System Architecture

The overall request path is:

```text
Client
   │
   ▼
DNS Resolution
   │
   ▼
Active / Standby NGINX
   │
   ▼
Backend Isolation Gateway
   │
   ├──► Backend A
   │
   └──► Backend B
```

The primary and backup DNS services provide redundancy at the name-resolution layer.

The two backend services provide redundancy at the application-service layer.

A standby NGINX provides a controlled migration target for the edge layer.

---

# 4. Physical Deployment

## 4.1 Ram Mac

```text
IP: 10.7.7.82
Hostname: MacBook-Pro-93.local
```

The Ram Mac hosts:

- Primary DNS
- Backend A
- Backend B
- Backend isolation gateway
- Standby NGINX
- Docker infrastructure

---

## 4.2 Mukund Mac

```text
IP: 10.7.20.185
Hostname: Mukunds-MacBook-Pro.local
```

The Mukund Mac hosts:

- Active NGINX edge
- Backup DNS
- Docker infrastructure

This separation allows the Phase 2 architecture to demonstrate communication between independent network hosts.

---

# 5. Backup DNS Resolver

## Objective

The objective was to provide DNS redundancy so that loss of the primary DNS service does not immediately prevent clients from resolving the application domain.

The DNS services are:

```text
Primary:
10.7.7.82:53

Backup:
10.7.20.185:53
```

Both DNS services contain the required application record.

---

## 5.1 Normal Operation

Under normal conditions:

```text
Client
   │
   ▼
Primary DNS
10.7.7.82:53
   │
   ▼
app.team1.test
```

The primary DNS returns the current address for the application.

---

## 5.2 Primary DNS Failure

The primary DNS service was intentionally stopped.

The expected behavior was:

```text
Primary DNS
     │
     X
   Failure
     │
     ▼
Backup DNS
10.7.20.185:53
     │
     ▼
Successful resolution
```

The backup DNS successfully resolved `app.team1.test`.

This demonstrates that DNS service failure can be handled independently of application-service availability.

---

## 5.3 Result

The backup DNS resolver successfully provided name resolution after the primary DNS service was stopped.

Evidence is stored under:

```text
evidence/04-backup-dns/
```

Relevant evidence includes:

- `backup-dns-cross-machine.txt`
- `backup-dns-cross-machine.png`
- `backup-dns-failover.txt`
- `backup-dns-failover.png`
- `primary-dns-stopped-status.txt`
- `backup-dns-status.txt`
- `backup-dns-logs.txt`

---

# 6. DNS TTL and Controlled Record Change

## Objective

The objective was to demonstrate how DNS caching affects controlled migration.

The configured TTL is:

```text
30 seconds
```

The process was:

```text
Initial DNS resolution
        ↓
DNS response cached
        ↓
DNS record changed
        ↓
Old cached response remains
        ↓
TTL expires
        ↓
New DNS response
```

---

## 6.1 Initial Resolution

The initial DNS record was resolved and recorded.

The response was retained as evidence before changing the DNS record.

---

## 6.2 Controlled DNS Change

The application DNS record was changed from the previous edge address to the standby edge:

```text
Old:
10.7.20.185

New:
10.7.7.82
```

Because the TTL was 30 seconds, a resolver that already had the old answer cached could continue returning the old address temporarily.

---

## 6.3 Cached Old Answer

The cached response demonstrated that changing the DNS record does not necessarily cause every client to immediately use the new address.

The old address remained available from the cache until the TTL expired.

---

## 6.4 TTL Expiry

After the TTL expired, a new DNS resolution returned:

```text
10.7.7.82
```

The client could then reach the standby edge.

---

## 6.5 Result

The TTL experiment successfully demonstrated:

- DNS caching
- Cached old answers
- TTL-based expiry
- New DNS resolution
- Controlled migration behavior

Evidence is stored under:

```text
evidence/09-dns-ttl/
```

---

# 7. Backend Service Isolation

## Objective

The objective was to prevent arbitrary clients from directly accessing the backend services.

The application backends are:

```text
Backend A → 10.7.7.82:3001
Backend B → 10.7.7.82:3002
```

The active edge is:

```text
10.7.20.185
```

Only the active edge is permitted to access the backend gateway ports.

---

## 7.1 Backend Access Model

```text
Active Edge
10.7.20.185
      │
      │ ALLOWED
      ▼
10.7.7.82:3001 / 3002
      │
      ▼
Backend A / Backend B
```

Unauthorized sources are denied.

```text
Unauthorized Source
        │
        ▼
10.7.7.82:3001 / 3002
        │
        X
      DENIED
```

---

## 7.2 Isolation Implementation

The actual backend containers are bound locally using:

```text
127.0.0.1:13001
127.0.0.1:13002
```

A host-side gateway exposes the controlled ports:

```text
10.7.7.82:3001
10.7.7.82:3002
```

The gateway checks the source IP before forwarding traffic.

The allowed source is:

```text
10.7.20.185
```

---

## 7.3 Result

The active edge successfully reached both backend services.

Unauthorized source attempts were denied.

Evidence is stored under:

```text
evidence/10-backend-isolation/
```

Important evidence includes:

- `isolation-edge-allowed-3001.txt`
- `isolation-edge-allowed-3002.txt`
- `isolation-unauthorized-source-blocked.txt`
- `isolation-unauthorized-source-blocked.png`
- `isolation-gateway.log`
- `isolation-gateway-console.log`

The gateway logs provide evidence of both allowed and denied connections.

---

# 8. Backend High Availability

## Objective

The objective was to ensure that application service continues when one backend becomes unavailable.

Two backends were deployed:

```text
Backend A → Port 3001
Backend B → Port 3002
```

The active NGINX edge maintains both services as upstream backends.

---

# 9. Normal Backend Operation

Under normal conditions:

```text
              ┌──► Backend A
              │
NGINX Edge ───┤
              │
              └──► Backend B
```

Both backends respond successfully.

The backends identify themselves using:

```text
X-Backend: A
```

and:

```text
X-Backend: B
```

This makes it possible to observe which backend handled a request.

---

# 10. Backend A Failure

Backend A was intentionally stopped.

The resulting state was:

```text
Backend A
    │
    X
  FAILED

Backend B
    │
    ▼
  HEALTHY
```

NGINX detected that Backend A was unavailable and continued serving requests through Backend B.

Therefore:

```text
Client
   │
   ▼
NGINX
   │
   X Backend A
   │
   ▼
Backend B
   │
   ▼
Response
```

---

# 11. Backend Recovery

Backend A was restarted after the failure demonstration.

After recovery, both backend services were available again.

```text
Backend A → Healthy
Backend B → Healthy
```

The restoration was verified through the service status and application responses.

Evidence is stored under:

```text
evidence/11-ha-failover/
```

Important evidence includes:

- `baseline-both-backends.txt`
- `baseline-both-backends.jpeg`
- `backend-a-stopped-status.txt`
- `backend-a-failed-b-serving.txt`
- `backend-a-failed-b-serving.jpeg`
- `backend-a-restored-status.txt`
- `backend-a-restored.txt`
- `backend-a-restored.jpeg`

---

# 12. Edge Migration

## Objective

The objective was to demonstrate controlled migration from the active NGINX edge to a standby edge.

The active edge was:

```text
10.7.20.185:443
```

The standby edge was:

```text
10.7.7.82:443
```

The application domain was:

```text
app.team1.test
```

---

## 12.1 Standby Edge Preparation

A standby NGINX instance was deployed on the Ram Mac using Docker.

The standby NGINX was configured to provide the same application entry point and connect to the available backend services.

Before changing DNS, the standby edge was tested independently.

This ensured that the migration target was functional before the cutover.

---

# 13. DNS Cutover

The DNS record was changed from:

```text
10.7.20.185
```

to:

```text
10.7.7.82
```

The TTL was:

```text
30 seconds
```

Therefore, clients with cached DNS information could temporarily continue using the old edge.

The migration sequence was:

```text
Active Edge
10.7.20.185
      │
      ▼
Prepare Standby
10.7.7.82
      │
      ▼
Change DNS
      │
      ▼
Wait for TTL
      │
      ▼
New DNS Answer
10.7.7.82
      │
      ▼
Standby Edge
```

---

# 14. Edge Migration Result

After the DNS TTL expired, the application resolved to the standby edge.

The standby NGINX successfully served the application.

This demonstrated that an application edge can be migrated without adding another physical machine.

Evidence is stored under:

```text
evidence/12-edge-migration/
```

Relevant evidence includes:

- `active-edge-before-cutover.txt`
- `dns-before-cutover.txt`
- `dns-cutover.txt`
- `dns-cutover.png`
- `dns-ttl-cached-old-answer.png`
- `ttl-expiry-new-edge.txt`
- `edge-migration-after-ttl.png`
- `edge-migration-final.txt`
- `standby-edge-baseline.txt`
- `service-inventory.png`

---

# 15. Troubleshooting Methodology

The Phase 2 troubleshooting process follows the order:

```text
DNS
 ↓
TCP
 ↓
TLS
 ↓
Application
```

The purpose is to identify the layer where a failure occurs instead of assuming that every failure is an application failure.

---

# 16. DNS Troubleshooting

DNS was tested using:

```bash
dig @10.7.7.82 app.team1.test
```

The test checks whether the configured DNS service returns the expected application address.

A DNS failure indicates that the problem should initially be investigated at the DNS layer.

Evidence:

```text
evidence/13-troubleshooting/dns-failure.txt
evidence/13-troubleshooting/dns-failure.png
```

---

# 17. TCP Troubleshooting

After DNS, TCP connectivity to HTTPS port 443 was tested.

The command used was:

```bash
nc -vz 10.7.7.82 443
```

This determines whether the destination host accepts a TCP connection on port 443.

A successful TCP connection indicates that the basic network path to the HTTPS service is functioning.

Evidence:

```text
evidence/13-troubleshooting/tcp-connectivity.txt
evidence/13-troubleshooting/tcp-connectivity.png
```

---

# 18. TLS Troubleshooting

TLS was tested using:

```bash
openssl s_client \
  -connect 10.7.7.82:443 \
  -servername app.team1.test
```

This verifies:

- TCP connection to the TLS endpoint
- TLS handshake
- Certificate presentation
- Server-side TLS response

The TLS evidence is:

```text
evidence/13-troubleshooting/tls.txt
```

The certificate may be self-signed in the development/test environment. Certificate trust verification and TLS endpoint functionality are separate concerns.

---

# 19. Application Troubleshooting

Finally, the application was tested through HTTPS.

The test verifies that the request can pass through:

```text
DNS
 ↓
TCP
 ↓
TLS
 ↓
NGINX
 ↓
Backend
```

and return an HTTP response.

Evidence:

```text
evidence/13-troubleshooting/application-success.txt
evidence/13-troubleshooting/application-success.png
```

---

# 20. Failure Classification

The troubleshooting process allows failures to be classified as follows:

| Observation | Layer |
|---|---|
| Domain does not resolve | DNS |
| DNS resolves but port 443 is unreachable | TCP |
| TCP works but TLS fails | TLS |
| TLS succeeds but application fails | Application/NGINX |
| Backend A fails while B works | Backend A |
| DNS returns old address after record change | DNS cache/TTL |
| Unauthorized backend request is rejected | Service isolation |

This classification provides a systematic troubleshooting approach rather than relying on trial and error.

---

# 21. HTTP Caching

The backend responses include HTTP cache-control behavior.

For example, the backend response uses:

```text
Cache-Control: public, max-age=30
```

This means that a response can be considered cacheable for the specified period.

The caching behavior is separate from DNS caching.

### DNS caching

Controls how long a DNS answer can remain cached.

```text
TTL = 30 seconds
```

### HTTP caching

Controls how long an HTTP response can remain cacheable.

```text
max-age=30
```

Therefore:

```text
DNS TTL
    ↓
Controls address caching

HTTP max-age
    ↓
Controls response caching
```

---

# 22. Resilience Summary

The Phase 2 architecture introduces resilience at multiple levels.

### DNS resilience

```text
Primary DNS
    ↓
Backup DNS
```

### Backend resilience

```text
Backend A
    +
Backend B
```

### Edge migration capability

```text
Active Edge
    ↓
Standby Edge
```

### Troubleshooting resilience

```text
DNS
 ↓
TCP
 ↓
TLS
 ↓
Application
```

Each mechanism addresses a different type of failure.

---

# 23. Limitations

The architecture improves resilience but does not completely eliminate all single points of failure.

The active edge remains the primary application entry point during normal operation.

If the active edge fails, the standby edge requires controlled DNS migration for clients to begin using it.

Therefore, the architecture provides:

- Backend redundancy
- DNS redundancy
- Standby edge capability
- Controlled migration

but the edge layer is not fully automatic active-active HA.

This limitation is intentionally identified as part of the architecture.

---

# 24. Rollback

Rollback configurations are maintained separately under:

```text
phase2/rollback/
```

The rollback strategy ensures that experimental Phase 2 changes can be reversed.

Examples include:

- Previous NGINX configuration
- Previous Docker Compose configuration
- Previous firewall/PF configuration
- Primary-edge restoration configuration

The general procedure is:

```text
Apply Change
    ↓
Test
    ↓
Capture Evidence
    ↓
Restore Previous Configuration if Required
```

Phase 1 configuration is kept separate from Phase 2 changes.

---

# 25. Evidence Mapping

| Phase 2 Area | Evidence Directory |
|---|---|
| Topology | `evidence/01-topology/` |
| Primary DNS | `evidence/03-primary-dns/` |
| Backup DNS | `evidence/04-backup-dns/` |
| DNS TTL | `evidence/09-dns-ttl/` |
| Backend Isolation | `evidence/10-backend-isolation/` |
| HA Failover | `evidence/11-ha-failover/` |
| Edge Migration | `evidence/12-edge-migration/` |
| Troubleshooting | `evidence/13-troubleshooting/` |

The evidence is organized so that each major Phase 2 requirement can be independently verified.

---

# 26. Final Results

The Phase 2 implementation successfully demonstrates:

- A working primary DNS resolver
- A working backup DNS resolver
- DNS resolution after primary DNS failure
- Short DNS TTL behavior
- Controlled DNS record changes
- DNS cache expiry
- Backend service isolation
- Authorized edge-to-backend communication
- Blocking of unauthorized backend access
- Two-backend high availability
- Backend A failure recovery through Backend B
- Backend A restoration
- A working standby NGINX edge
- Controlled DNS-based edge migration
- Layer-by-layer DNS/TCP/TLS/application troubleshooting
- Reversible Phase 2 configuration

---

# 27. Conclusion

Phase 2 transforms the Phase 1 network into a more resilient and controllable architecture.

The implementation demonstrates that reliability is not provided by a single mechanism. Instead, different layers require different recovery strategies.

DNS redundancy protects name resolution.

Backend redundancy protects application availability.

Service isolation prevents direct unauthorized backend access.

A standby edge provides a controlled migration target.

DNS TTL testing demonstrates the practical behavior of cached records during migration.

Finally, the troubleshooting workflow provides a structured method for identifying whether a problem originates at the DNS, TCP, TLS, or application layer.

The resulting architecture provides a practical demonstration of **hardening, recovery, high availability, controlled migration, and systematic troubleshooting** while keeping the original Phase 1 implementation separate and intact.