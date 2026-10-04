# IP and Service Table

## 1. Network Summary

| Parameter | Value |
|---|---|
| Network type | Private Wi-Fi / LAN |
| IP addressing | IPv4 |
| Subnet | `255.255.224.0` |
| CIDR | `/19` |
| Default gateway | `10.7.0.1` |
| Active interface | `en0` |
| Private DNS namespace | `team1.test` |
| Application hostname | `app.team1.test` |
| Public HTTPS port | `8443` |
| Public HTTP port | `8080` |

---

## 2. Machine and Service Inventory

| Machine | IPv4 Address | Interface | Role | Service | Protocol | Port |
|---|---|---|---|---|---|---:|
| Mac 1 | `10.7.6.223` | `en0` | Private DNS Server | dnsmasq | DNS/UDP | `53` |
| Mac 2 | `10.7.28.44` | `en0` | Edge / Reverse Proxy | nginx | HTTP/TCP | `8080` |
| Mac 2 | `10.7.28.44` | `en0` | TLS Termination | nginx | HTTPS/TCP | `8443` |
| Mac 2 | `10.7.28.44` | `en0` | Backend A | Node.js HTTP | HTTP/TCP | `3001` |
| Mac 3 | `10.7.31.67` | `en0` | Backend B | Node.js HTTP | HTTP/TCP | `3002` |

---

## 3. Mac 1 — Private DNS

**IP:** `10.7.6.223`

**Role:** Private DNS Server

**Service:** `dnsmasq`

**Port:** `53`

### DNS records

| Hostname | Record Type | Address |
|---|---|---|
| `app.team1.test` | A | `10.7.28.44` |
| `api.team1.test` | A | `10.7.28.44` |

### DNS configuration

Mac 1 provides authoritative local responses for the `team1.test` namespace.

The clients use:

```text
DNS Server: 10.7.6.223
DNS Port: 53
```

External resolvers configured as upstream resolvers are:

```text
8.8.8.8
1.1.1.1
```

---

## 4. Mac 2 — Edge and Backend A

**IP:** `10.7.28.44`

**Role:** Edge Reverse Proxy, Load Balancer and Backend A

### nginx HTTP

```text
Protocol: HTTP
Port: 8080
Hostname: app.team1.test
```

Entry point:

```text
http://app.team1.test:8080
```

### nginx HTTPS

```text
Protocol: HTTPS
Port: 8443
Hostname: app.team1.test
TLS termination: nginx
```

Entry point:

```text
https://app.team1.test:8443
```

### Backend A

```text
Protocol: HTTP
Port: 3001
Bind address: 0.0.0.0
```

Endpoints:

```text
GET /
GET /api/status
```

Backend identifier:

```text
X-Backend: A
```

---

## 5. Mac 3 — Backend B

**IP:** `10.7.31.67`

**Role:** Backend B and client used for packet analysis

### Backend B

```text
Protocol: HTTP
Port: 3002
Bind address: 0.0.0.0
```

Endpoints:

```text
GET /
GET /api/status
```

Backend identifier:

```text
X-Backend: B
```

---

## 6. nginx Upstream Services

The nginx upstream group contains two backend servers:

| Backend | IP Address | Port | Identifier |
|---|---|---:|---|
| Backend A | `10.7.28.44` | `3001` | `X-Backend: A` |
| Backend B | `10.7.31.67` | `3002` | `X-Backend: B` |

Load-balancing method:

```text
Round-robin
```

The client accesses only the nginx public entry point and does not need to directly access the backend services.

---

## 7. TLS Certificate Information

| Item | Value |
|---|---|
| Certificate Authority | Team1 Local CA |
| Server hostname | `app.team1.test` |
| Server certificate | `app.team1.test.crt` |
| CA certificate | `team1-ca.crt` |
| TLS termination | nginx |
| HTTPS port | `8443` |
| Certificate trust | Local client trust store |

Private key files are intentionally excluded from version control.

---

## 8. HTTP Caching

The `/api/status` endpoint supports HTTP caching.

### Backend A

```text
Cache-Control: public, max-age=30
ETag: "backend-a-v1"
```

### Backend B

```text
Cache-Control: public, max-age=30
ETag: "backend-b-v1"
```

Conditional requests use:

```text
If-None-Match
```

A valid cached representation can result in:

```text
HTTP/1.1 304 Not Modified
```

---

## 9. Network Flow

```text
Client
  |
  | DNS :53
  v
Mac 1
10.7.6.223
dnsmasq
  |
  | Returns 10.7.28.44
  v
Mac 2
10.7.28.44
nginx :8443
  |
  | Round-robin
  +----------------------+
  |                      |
  v                      v
Backend A              Backend B
10.7.28.44             10.7.31.67
:3001                  :3002
```

---

## 10. Port Reference

| Port | Service | Machine | Purpose |
|---:|---|---|---|
| `53` | dnsmasq | `10.7.6.223` | Private DNS |
| `8080` | nginx | `10.7.28.44` | HTTP entry point |
| `8443` | nginx | `10.7.28.44` | HTTPS/TLS entry point |
| `3001` | Backend A | `10.7.28.44` | REST backend |
| `3002` | Backend B | `10.7.31.67` | REST backend |

---

## 11. Client-Visible Services

The main application hostname is:

```text
app.team1.test
```

DNS resolves it to:

```text
10.7.28.44
```

The preferred secure application endpoint is:

```text
https://app.team1.test:8443
```

The HTTP endpoint used for load-balancing testing is:

```text
http://app.team1.test:8080
```

Clients do not need to know or directly specify the backend addresses when using the application hostname.