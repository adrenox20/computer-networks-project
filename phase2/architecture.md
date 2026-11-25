# Phase 2 Architecture

## 1. Architecture Overview

Phase 2 extends the Phase 1 computer-network architecture with redundancy, service isolation, backend high availability, controlled DNS migration, and troubleshooting mechanisms.

The implementation uses **two physical Macs** and Docker containers for the required network services.

The two physical hosts are:

- **Ram Mac:** `10.7.7.82`
- **Mukund Mac:** `10.7.20.185`

Docker is used to provide isolated backend and infrastructure services because a third physical Mac was not available.

---

## 2. Physical Topology

```text
                         ┌──────────────────────────────┐
                         │            Client            │
                         │       User / Test Host       │
                         └──────────────┬───────────────┘
                                        │
                              DNS / HTTPS requests
                                        │
                                        ▼
                         ┌──────────────────────────────┐
                         │        DNS Resolution        │
                         │                              │
                         │ Primary DNS                  │
                         │ 10.7.7.82:53                 │
                         │                              │
                         │ Backup DNS                   │
                         │ 10.7.20.185:53              │
                         └──────────────┬───────────────┘
                                        │
                         app.team1.test resolution
                                        │
                                        ▼
                  ┌────────────────────────────────────────┐
                  │              Edge Layer                 │
                  │                                        │
                  │ Active Edge                             │
                  │ Mukund Mac                              │
                  │ 10.7.20.185:443                         │
                  │                                        │
                  │ Standby Edge                            │
                  │ Ram Mac                                 │
                  │ 10.7.7.82:443                           │
                  └────────────────┬───────────────────────┘
                                   │
                         HTTP/HTTPS proxy
                                   │
                                   ▼
                  ┌────────────────────────────────────────┐
                  │       Backend Isolation Gateway          │
                  │             Ram Mac                      │
                  │           10.7.7.82                      │
                  │                                            │
                  │       Port 3001 → Backend A              │
                  │       Port 3002 → Backend B              │
                  └────────────────┬───────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
          ┌─────────────────┐          ┌─────────────────┐
          │    Backend A    │          │    Backend B    │
          │     Port 3001   │          │     Port 3002   │
          │     Healthy     │          │     Healthy     │
          └─────────────────┘          └─────────────────┘
```

---

# 3. Physical Hosts

## 3.1 Ram Mac

```text
Hostname: MacBook-Pro-93.local
IP:       10.7.7.82
```

The Ram Mac hosts:

- Primary DNS
- Backend A
- Backend B
- Backend isolation gateway
- Standby NGINX
- Supporting Docker services

---

## 3.2 Mukund Mac

```text
Hostname: Mukunds-MacBook-Pro.local
IP:       10.7.20.185
```

The Mukund Mac hosts:

- Active NGINX edge
- Backup DNS
- Docker-based supporting services

The active application edge is intentionally separated from the backend host so that the architecture demonstrates a distributed network path rather than placing every service on one machine.

---

# 4. DNS Architecture

The application uses the domain:

```text
app.team1.test
```

DNS is provided by two resolvers.

### Primary DNS

```text
Host: 10.7.7.82
Port: 53
Role: Primary resolver
```

### Backup DNS

```text
Host: 10.7.20.185
Port: 53
Role: Backup resolver
```

Both DNS services contain the application record.

The DNS record uses a short TTL:

```text
TTL = 30 seconds
```

The short TTL allows controlled DNS changes to propagate relatively quickly during testing and edge migration.

---

# 5. DNS Failure Architecture

Under normal operation:

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

If the primary DNS service becomes unavailable:

```text
Client
   │
   ▼
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
app.team1.test
```

The backup resolver therefore provides continued name-resolution capability when the primary resolver fails.

The failure is specifically a **DNS service failure**. It does not automatically imply that the application backend has failed.

---

# 6. Docker Network Architecture

The main Docker network on the Ram Mac is:

```text
Network:
docker_phase2-internal

Subnet:
172.18.0.0/16

Gateway:
172.18.0.1
```

Important container addresses are:

| Service | Container IP |
|---|---:|
| Standby NGINX | `172.18.0.2` |
| Backend B | `172.18.0.3` |
| Primary DNS | `172.18.0.4` |
| Backend A | `172.18.0.5` |
| Cache Resolver | `172.18.0.6` |

These addresses belong to the internal Docker network and are separate from the physical Mac IP addresses.

---

# 7. Backend Architecture

Two independent backend services are used.

## Backend A

```text
Service: Backend A
Port:    3001
Host:    10.7.7.82
```

Backend A identifies itself using:

```text
X-Backend: A
```

## Backend B

```text
Service: Backend B
Port:    3002
Host:    10.7.7.82
```

Backend B identifies itself using:

```text
X-Backend: B
```

The `X-Backend` response header makes it possible to verify which backend handled an individual request.

---

# 8. Backend Isolation Architecture

The backend services are not intended to be directly reachable by arbitrary network clients.

The host-side isolation design uses local-only Docker publication for the actual application containers.

The backend containers are bound internally to:

```text
127.0.0.1:13001
127.0.0.1:13002
```

A host-side gateway then provides the externally reachable backend ports:

```text
10.7.7.82:3001
10.7.7.82:3002
```

The gateway checks the source IP.

The permitted edge source is:

```text
10.7.20.185
```

Therefore:

```text
Mukund Edge
10.7.20.185
       │
       │ ALLOWED
       ▼
10.7.7.82:3001 / 3002
       │
       ▼
Backend A / Backend B
```

An unauthorized source follows:

```text
Unauthorized Client
       │
       ▼
10.7.7.82:3001 / 3002
       │
       X
       │
     DENIED
```

This ensures that backend access is restricted to the edge layer.

---

# 9. Active Edge NGINX

The active application edge runs on the Mukund Mac.

```text
Host:
10.7.20.185

HTTPS:
443

HTTP:
80
```

The edge uses NGINX as the reverse proxy.

Its upstream pool contains:

```text
10.7.7.82:3001
10.7.7.82:3002
```

The request path is therefore:

```text
Client
   │
   │ HTTPS
   ▼
10.7.20.185:443
   │
   │ NGINX reverse proxy
   ▼
10.7.7.82:3001
        OR
10.7.7.82:3002
```

NGINX monitors backend availability using its upstream failure handling.

---

# 10. Backend High Availability

The two backend services provide application-level redundancy.

Normal operation:

```text
                    ┌──► Backend A
                    │
Active Edge NGINX ──┤
                    │
                    └──► Backend B
```

If Backend A fails:

```text
                    ┌──► Backend A
                    │       X
Active Edge NGINX ──┤      FAILED
                    │
                    └──► Backend B
                            │
                            ▼
                         RESPONSE
```

The application remains available through Backend B.

After Backend A is restored:

```text
                    ┌──► Backend A
                    │
Active Edge NGINX ──┤
                    │
                    └──► Backend B
```

Both backends are again available to the upstream pool.

---

# 11. Edge Migration Architecture

A second NGINX instance is deployed on the Ram Mac as the standby edge.

### Active edge

```text
10.7.20.185:443
```

### Standby edge

```text
10.7.7.82:443
```

Before migration:

```text
app.team1.test
      │
      ▼
10.7.20.185
      │
      ▼
Active NGINX
```

During controlled migration, the DNS record is changed:

```text
app.team1.test
      │
      ▼
10.7.7.82
      │
      ▼
Standby NGINX
```

Because the DNS TTL is 30 seconds, clients may continue using the previous address until their cached DNS entry expires.

After TTL expiry:

```text
Client
   │
   ▼
DNS
   │
   ▼
10.7.7.82
   │
   ▼
Standby NGINX
```

This demonstrates controlled edge migration without requiring additional physical hardware.

---

# 12. Standby NGINX Backend Connectivity

The standby NGINX runs inside Docker on the Ram Mac.

Because the backend containers are protected by the host-side isolation gateway, the standby edge uses Docker's host gateway mechanism to reach the locally published backend ports.

The standby edge therefore reaches:

```text
host.docker.internal:13001
host.docker.internal:13002
```

which correspond to the locally published Backend A and Backend B services.

This avoids incorrectly treating the standby NGINX container as an authorized external edge source.

---

# 13. TLS Architecture

HTTPS is terminated at the NGINX edge.

The TLS certificate is configured for:

```text
app.team1.test
```

The HTTPS request path is:

```text
Client
   │
   │ TLS
   ▼
NGINX :443
   │
   │ HTTP proxy
   ▼
Backend
```

Therefore, TLS is handled at the edge rather than being independently terminated by each backend.

TLS verification is tested using:

```text
openssl s_client
```

The application can also be tested through:

```text
curl
```

using the application domain.

---

# 14. Request Flow

A normal HTTPS request follows this sequence:

### Step 1 — DNS

The client resolves:

```text
app.team1.test
```

through the configured DNS resolver.

### Step 2 — TCP

The client establishes a TCP connection to port:

```text
443
```

on the resolved edge address.

### Step 3 — TLS

The client performs the TLS handshake with NGINX.

### Step 4 — HTTP

The HTTPS request reaches the NGINX reverse proxy.

### Step 5 — Backend selection

NGINX forwards the request to a healthy backend:

```text
Backend A
```

or:

```text
Backend B
```

### Step 6 — Response

The backend returns the response with its identifying header:

```text
X-Backend: A
```

or:

```text
X-Backend: B
```

This makes backend selection visible during testing.

---

# 15. Failure Domains

The architecture separates failures into different domains.

## DNS Failure

Example:

```text
Primary DNS unavailable
```

Expected result:

```text
Backup DNS continues resolution.
```

---

## Backend Failure

Example:

```text
Backend A unavailable
```

Expected result:

```text
NGINX continues serving through Backend B.
```

---

## Edge Failure

Example:

```text
Active edge unavailable
```

The standby edge is available as the migration target.

However, DNS must point to the standby edge for clients to use it.

---

## Application Failure

An application-level failure can occur even when:

- DNS works
- TCP works
- TLS works

Therefore, troubleshooting proceeds layer by layer rather than assuming that every failure is a DNS or network problem.

---

# 16. Troubleshooting Architecture

The troubleshooting methodology follows:

```text
                Failure
                  │
                  ▼
             DNS Check
                  │
              Successful?
             /           \
           No             Yes
           │               │
       DNS Layer        TCP Check
                           │
                       Successful?
                      /           \
                    No             Yes
                    │               │
                TCP Layer       TLS Check
                                    │
                                Successful?
                               /           \
                             No             Yes
                             │               │
                         TLS Layer      Application
                                         Check
```

The Phase 2 troubleshooting evidence demonstrates this layered approach using:

- `dig`
- `nc`
- `openssl s_client`
- `curl`

---

# 17. DNS TTL and Cutover Flow

The controlled DNS migration follows:

```text
Initial DNS
    │
    ▼
Client caches old address
    │
    ▼
DNS record changed
    │
    ▼
Old cached answer remains temporarily
    │
    ▼
TTL = 30 seconds expires
    │
    ▼
Client resolves new address
    │
    ▼
Traffic reaches new edge
```

This demonstrates why DNS changes are not always immediately visible to every client.

---

# 18. High Availability Failure Flow

The backend failover sequence is:

```text
Normal State
    │
    ├── Backend A = Healthy
    └── Backend B = Healthy
            │
            ▼
       Stop Backend A
            │
            ▼
       NGINX detects failure
            │
            ▼
       Backend B continues
       serving requests
            │
            ▼
       Restore Backend A
            │
            ▼
       Backend A becomes
       available again
```

---

# 19. Controlled Edge Migration Flow

The edge migration sequence is:

```text
Active Edge
10.7.20.185
      │
      ▼
Verify standby edge
10.7.7.82
      │
      ▼
Change DNS record
      │
      ▼
Old DNS answer remains
during TTL
      │
      ▼
TTL expires
      │
      ▼
New DNS resolution
10.7.7.82
      │
      ▼
Standby edge serves application
```

---

# 20. Single Points of Failure

The Phase 2 architecture improves resilience but does not eliminate every single point of failure.

The active edge NGINX remains a potential SPOF during normal operation.

```text
Client
   │
   ▼
Active Edge
   │
   ├──► Backend A
   └──► Backend B
```

If the active edge itself fails, the standby edge can take over through controlled DNS migration.

Therefore:

- Backend layer has active redundancy.
- DNS layer has primary/backup redundancy.
- Edge layer has an available standby.
- Edge migration is controlled through DNS TTL.

This is an important limitation to identify during the viva.

---

# 21. Architecture Summary

The final Phase 2 architecture can be summarized as:

```text
                         CLIENT
                           │
                           ▼
                    DNS RESOLUTION
                    /            \
                   /              \
          Primary DNS          Backup DNS
          10.7.7.82            10.7.20.185
                │
                ▼
          app.team1.test
                │
                ▼
       ┌───────────────────┐
       │   EDGE NGINX      │
       │                   │
       │ Active:           │
       │ 10.7.20.185:443   │
       │                   │
       │ Standby:          │
       │ 10.7.7.82:443     │
       └─────────┬─────────┘
                 │
                 ▼
        BACKEND ISOLATION
             GATEWAY
                 │
          ┌──────┴──────┐
          │             │
          ▼             ▼
     BACKEND A      BACKEND B
      :3001          :3002
       │                │
       └───────┬────────┘
               ▼
          APPLICATION
```

The architecture provides:

1. **DNS redundancy**
2. **Short-TTL controlled migration**
3. **Restricted backend access**
4. **Backend high availability**
5. **Standby edge capability**
6. **Layered troubleshooting**
7. **Rollback capability**
8. **Clear separation between Phase 1 and Phase 2**