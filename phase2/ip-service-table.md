# Phase 2 IP and Service Table

## 1. Physical Hosts

| Host | Hostname | IP Address | Role |
|---|---|---|---|
| Ram Mac | `MacBook-Pro-93.local` | `10.7.7.82` | Primary infrastructure host |
| Mukund Mac | `Mukunds-MacBook-Pro.local` | `10.7.20.185` | Active edge and backup DNS host |

---

## 2. Core Services

| Service | Host | IP / Address | Port | Protocol | Role |
|---|---|---:|---:|---|---|
| Primary DNS | Ram Mac | `10.7.7.82` | `53` | DNS/UDP + TCP | Primary resolver |
| Backup DNS | Mukund Mac | `10.7.20.185` | `53` | DNS/UDP + TCP | Backup resolver |
| Active NGINX Edge | Mukund Mac | `10.7.20.185` | `443` | HTTPS | Primary application edge |
| Active NGINX HTTP | Mukund Mac | `10.7.20.185` | `80` | HTTP | HTTP entry point |
| Standby NGINX Edge | Ram Mac | `10.7.7.82` | `443` | HTTPS | Standby application edge |
| Standby NGINX HTTP | Ram Mac | `10.7.7.82` | `80` | HTTP | Standby HTTP entry point |
| Backend A | Ram Mac | `10.7.7.82` | `3001` | HTTP | Application backend A |
| Backend B | Ram Mac | `10.7.7.82` | `3002` | HTTP | Application backend B |

---

## 3. Backend Isolation Ports

The actual backend containers are published locally on the Ram Mac and are accessed through the host-side isolation gateway.

| Component | Host Binding | Container Port | Purpose |
|---|---:|---:|---|
| Backend A local binding | `127.0.0.1:13001` | `3001` | Local backend A access |
| Backend B local binding | `127.0.0.1:13002` | `3002` | Local backend B access |
| Isolation Gateway A | `10.7.7.82:3001` | `13001` | Controlled access to Backend A |
| Isolation Gateway B | `10.7.7.82:3002` | `13002` | Controlled access to Backend B |

The isolation gateway allows the active edge source:

```text
10.7.20.185
```

and denies unauthorized sources.

---

# 4. Application Domain

| Item | Value |
|---|---|
| Application domain | `app.team1.test` |
| DNS TTL | `30 seconds` |
| Primary DNS | `10.7.7.82` |
| Backup DNS | `10.7.20.185` |
| Active edge | `10.7.20.185` |
| Standby edge | `10.7.7.82` |

The DNS A record is changed during controlled edge migration.

---

# 5. Docker Network

The main Docker network is:

| Property | Value |
|---|---|
| Network name | `docker_phase2-internal` |
| Subnet | `172.18.0.0/16` |
| Gateway | `172.18.0.1` |

---

# 6. Docker Container Addresses

| Service | Container IP | Role |
|---|---:|---|
| Standby NGINX | `172.18.0.2` | Standby application edge |
| Backend B | `172.18.0.3` | Application backend B |
| Primary DNS | `172.18.0.4` | Primary DNS resolver |
| Backend A | `172.18.0.5` | Application backend A |
| Cache Resolver | `172.18.0.6` | DNS TTL/cache testing |

These Docker IP addresses are internal container-network addresses. They should not be confused with the physical Mac addresses used for inter-host communication.

---

# 7. NGINX Upstream Services

The active NGINX edge uses the following backend upstreams:

```text
10.7.7.82:3001
10.7.7.82:3002
```

Mapping:

| Upstream | Backend |
|---|---|
| `10.7.7.82:3001` | Backend A |
| `10.7.7.82:3002` | Backend B |

NGINX distributes requests between available healthy backend services.

---

# 8. Backend Identification

Each backend returns an `X-Backend` response header.

| Header Value | Backend |
|---|---|
| `X-Backend: A` | Backend A |
| `X-Backend: B` | Backend B |

This is used during testing to confirm which backend served a request.

For example:

```text
HTTP/1.1 200 OK
X-Backend: A
```

indicates that Backend A handled the request.

---

# 9. TLS

| Component | Value |
|---|---|
| Application domain | `app.team1.test` |
| HTTPS port | `443` |
| TLS termination | NGINX edge |
| Active TLS endpoint | `10.7.20.185:443` |
| Standby TLS endpoint | `10.7.7.82:443` |

TLS is terminated at the NGINX edge before the request is proxied to the backend services.

---

# 10. Troubleshooting Ports and Tools

| Layer | Tool | Target | Purpose |
|---|---|---|---|
| DNS | `dig` | DNS server `:53` | Verify name resolution |
| TCP | `nc` | Edge `:443` | Verify TCP connectivity |
| TLS | `openssl s_client` | Edge `:443` | Verify TLS handshake/certificate |
| Application | `curl` | `app.team1.test:443` | Verify application response |

The troubleshooting order is:

```text
DNS
 ↓
TCP
 ↓
TLS
 ↓
Application
```

---

# 11. Important Network Relationships

### DNS

```text
Client
   │
   ├──► Primary DNS: 10.7.7.82:53
   │
   └──► Backup DNS: 10.7.20.185:53
```

### Active application path

```text
Client
   │
   ▼
10.7.20.185:443
   │
   ▼
NGINX
   │
   ├──► 10.7.7.82:3001
   │
   └──► 10.7.7.82:3002
```

### Standby application path

```text
Client
   │
   ▼
10.7.7.82:443
   │
   ▼
Standby NGINX
   │
   ├──► Backend A
   │
   └──► Backend B
```

---

# 12. Failure and Recovery Mapping

| Failure | Expected Recovery |
|---|---|
| Primary DNS unavailable | Backup DNS resolves the domain |
| Backend A unavailable | NGINX continues through Backend B |
| Backend B unavailable | Backend A remains available |
| Backend A restored | Backend A returns to service |
| DNS record changed | New address becomes active after TTL |
| Active edge migration | DNS points clients to standby edge |
| DNS troubleshooting failure | Check resolver and DNS record |
| TCP troubleshooting failure | Check port/connectivity |
| TLS troubleshooting failure | Check TLS endpoint/certificate |
| Application troubleshooting failure | Check NGINX/backend application |

---

# 13. Quick Viva Reference

### Primary DNS

```text
10.7.7.82:53
```

### Backup DNS

```text
10.7.20.185:53
```

### Active Edge

```text
10.7.20.185:443
```

### Standby Edge

```text
10.7.7.82:443
```

### Backend A

```text
10.7.7.82:3001
```

### Backend B

```text
10.7.7.82:3002
```

### Application

```text
app.team1.test
```

### DNS TTL

```text
30 seconds
```

### Backend access restriction

```text
Allowed edge source:
10.7.20.185
```

### Docker network

```text
docker_phase2-internal
172.18.0.0/16
```