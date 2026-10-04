# Computer Networks Project — Phase 1

## Overview

This repository contains the implementation, configuration, source code, test documentation, packet captures, and evidence for Phase 1 of the Computer Networks Project.

Phase 1 implements a private LAN-based application architecture consisting of:

- Private DNS using `dnsmasq`
- Two HTTP/REST backend services
- nginx reverse proxy and load balancing
- HTTPS/TLS termination
- HTTP caching using `Cache-Control` and `ETag`
- Network and protocol analysis using Wireshark
- Failure and troubleshooting demonstrations

The system is entirely deployed on the team's private LAN.

---

# 1. Network Architecture

## Machines

| Machine | IP Address | Role |
|---|---|---|
| Mac 1 | `10.7.6.223` | Private DNS Server + Client |
| Mac 2 | `10.7.28.44` | nginx Edge/Load Balancer + Backend A + Client |
| Mac 3 | `10.7.31.67` | Backend B + Client |

Network:

```text
Subnet: 255.255.224.0 (/19)
Gateway: 10.7.0.1
Interface: en0
```

## Service Map

| Service | Host | Port |
|---|---|---:|
| Private DNS | Mac 1 — `10.7.6.223` | 53 |
| nginx HTTP | Mac 2 — `10.7.28.44` | 8080 |
| nginx HTTPS | Mac 2 — `10.7.28.44` | 8443 |
| Backend A | Mac 2 — `10.7.28.44` | 3001 |
| Backend B | Mac 3 — `10.7.31.67` | 3002 |

---

# 2. Request Flow

A normal application request follows this flow:

```text
Client
  │
  │ DNS query
  ▼
Mac 1 — Private DNS
10.7.6.223:53
  │
  │ app.team1.test → 10.7.28.44
  ▼
Mac 2 — nginx
10.7.28.44:8443
  │
  │ TLS termination
  │
  ├───────────────┐
  ▼               ▼
Backend A       Backend B
:3001           :3002
Mac 2           Mac 3
```

Architecture diagrams are available in:

```text
architecture/topology.png
architecture/request-flow.png
```

---

# 3. Private DNS

Mac 1 (`10.7.6.223`) runs `dnsmasq` as the private DNS server.

The private namespace is:

```text
team1.test
```

Configured records:

```text
app.team1.test → 10.7.28.44
api.team1.test → 10.7.28.44
```

Example test:

```bash
dig @10.7.6.223 app.team1.test
```

Expected result:

```text
app.team1.test → 10.7.28.44
```

Configuration:

```text
configuration/dns/dnsmasq.conf
```

DNS tests:

```text
tests/dns/README.md
```

DNS evidence:

```text
evidence/02-dns/
```

Raw packet captures:

```text
wireshark/03-dns/
```

---

# 4. Backend Services

## Backend A

Backend A runs on Mac 2:

```text
10.7.28.44:3001
```

Endpoints:

```text
/
 /api/status
```

The backend identifies itself using:

```text
X-Backend: A
```

Run:

```bash
cd backends/backend-a
./run.sh
```

Direct test:

```bash
curl -i http://10.7.28.44:3001/
```

---

## Backend B

Backend B runs on Mac 3:

```text
10.7.31.67:3002
```

Endpoints:

```text
/
/api/status
```

The backend identifies itself using:

```text
X-Backend: B
```

Run:

```bash
cd backends/backend-b
./run.sh
```

Direct test:

```bash
curl -i http://10.7.31.67:3002/
```

Backend source code:

```text
backends/backend-a/
backends/backend-b/
```

---

# 5. nginx Reverse Proxy and Load Balancer

nginx runs on Mac 2:

```text
10.7.28.44
```

HTTP:

```text
http://10.7.28.44:8080/
```

HTTPS:

```text
https://app.team1.test:8443/
```

The nginx upstream consists of:

```text
10.7.28.44:3001
10.7.31.67:3002
```

Repeated requests demonstrate responses from both backends using the `X-Backend` header.

Example:

```bash
for i in {1..5}; do
  curl -s -D - https://app.team1.test:8443/ -o /dev/null | grep X-Backend
done
```

nginx configuration:

```text
configuration/nginx/nginx.conf
```

Load-balancing tests:

```text
tests/load-balancing/README.md
```

Evidence:

```text
evidence/04-nginx/
```

---

# 6. HTTPS / TLS

nginx terminates TLS on:

```text
10.7.28.44:8443
```

Domain:

```text
app.team1.test
```

A Team 1 local CA was created using OpenSSL.

The server certificate contains:

```text
CN: app.team1.test
SAN: DNS:app.team1.test
```

The local CA certificate was installed in the client trust store.

HTTPS is demonstrated without bypassing certificate validation.

Example:

```bash
curl -i https://app.team1.test:8443/
```

The TLS packet capture demonstrates:

```text
ClientHello
ServerHello
Certificate
Server Key Exchange
Server Hello Done
Client Key Exchange
Change Cipher Spec
Encrypted Handshake Message
Application Data
```

TLS configuration and certificate setup:

```text
configuration/tls/
```

HTTPS tests:

```text
tests/https/README.md
```

TLS evidence:

```text
evidence/05-tls/
```

Raw TLS capture:

```text
wireshark/05-tls/
```

Private keys are excluded from version control.

---

# 7. HTTP Caching

The `/api/status` endpoint implements HTTP caching using:

```text
Cache-Control: public, max-age=30
ETag
```

Example:

```bash
curl -i http://127.0.0.1:3001/api/status
```

The response contains:

```text
Cache-Control: public, max-age=30
ETag: "backend-a-v1"
```

A conditional request can be tested using:

```bash
curl -i \
  -H 'If-None-Match: "backend-a-v1"' \
  http://127.0.0.1:3001/api/status
```

Expected response:

```text
HTTP/1.1 304 Not Modified
```

Backend B provides equivalent caching behavior using its own ETag.

Caching tests:

```text
tests/caching/README.md
```

Caching evidence:

```text
evidence/06-caching/
```

---

# 8. Wireshark and Packet Analysis

Wireshark was used to analyze the network and application protocol flow.

Captured traffic includes:

- ICMP
- DNS
- TCP
- TLS
- Load-balancing traffic

Raw captures are organized under:

```text
wireshark/
```

Current captures include:

```text
wireshark/01-icmp/
wireshark/03-dns/
wireshark/05-tls/
wireshark/07-load-balancing/
```

TCP handshake evidence is maintained under:

```text
wireshark/04-tcp/
```

when the dedicated TCP capture is added.

Wireshark usage screenshots:

```text
evidence/07-wireshark/
```

The packet analysis demonstrates source/destination addresses, ports, protocol behavior, and the TLS handshake.

---

# 9. Failure Demonstrations

Phase 1 includes failure demonstrations for:

1. Incorrect DNS server/record
2. One backend unavailable
3. Both backends unavailable
4. Incorrect destination port

The failures are diagnosed layer-by-layer:

```text
DNS
 ↓
TCP
 ↓
TLS
 ↓
Application
```

Failure evidence:

```text
evidence/08-failures/
```

Failure-related packet captures, when applicable:

```text
wireshark/08-failures/
```

---

# 10. Testing Documentation

Reproducible test procedures are documented separately:

```text
tests/
├── lan/
│   └── README.md
├── dns/
│   └── README.md
├── https/
│   └── README.md
├── load-balancing/
│   └── README.md
└── caching/
    └── README.md
```

These files describe the commands, expected behavior, results, and related evidence.

---

# 11. Repository Structure

```text
phase1/
│
├── README.md
│
├── architecture/
│   ├── architecture.md
│   ├── ip-service-table.md
│   ├── topology.png
│   └── request-flow.png
│
├── configuration/
│   ├── dns/
│   │   └── dnsmasq.conf
│   │
│   ├── nginx/
│   │   └── nginx.conf
│   │
│   └── tls/
│       ├── create-ca.sh
│       ├── create-cert.sh
│       ├── README.md
│       ├── san.cnf
│       └── team1-ca.crt
│
├── backends/
│   ├── backend-a/
│   │   ├── server.js
│   │   ├── app.py
│   │   └── run.sh
│   │
│   └── backend-b/
│       ├── server.js
│       ├── app.py
│       └── run.sh
│
├── tests/
│   ├── lan/
│   ├── dns/
│   ├── https/
│   ├── load-balancing/
│   └── caching/
│
├── evidence/
│   ├── 01-lan/
│   ├── 02-dns/
│   ├── 03-backends/
│   ├── 04-nginx/
│   ├── 05-tls/
│   ├── 06-caching/
│   ├── 07-wireshark/
│   └── 08-failures/
│
├── wireshark/
│   ├── 01-icmp/
│   ├── 03-dns/
│   ├── 04-tcp/
│   ├── 05-tls/
│   ├── 06-http/
│   ├── 07-load-balancing/
│   └── 08-failures/
│
└── demo-checklist.md
```

---

# 12. Security and Repository Notes

Private cryptographic material is not included in version control.

The following files must remain excluded:

```text
*.key
*.csr
*.srl
```

The public CA certificate may be included:

```text
team1-ca.crt
```

The TLS setup scripts allow the certificate infrastructure to be recreated without committing private keys.

---

# 13. Phase 1 Verification Checklist

- [x] Private LAN connectivity verified
- [x] IP addresses and service inventory documented
- [x] Private DNS configured using dnsmasq
- [x] `app.team1.test` resolution verified
- [x] `api.team1.test` resolution verified
- [x] Backend A implemented
- [x] Backend B implemented
- [x] nginx reverse proxy configured
- [x] nginx load balancing configured
- [x] `X-Backend` header implemented
- [x] HTTPS/TLS configured
- [x] Local CA trusted on client Macs
- [x] HTTPS verified without `curl -k`
- [x] TLS handshake captured
- [x] HTTP caching implemented
- [x] `Cache-Control` implemented
- [x] `ETag` implemented
- [x] `304 Not Modified` demonstrated
- [x] Failure scenarios demonstrated
- [x] ICMP/LAN packet capture collected
- [x] DNS packet capture collected
- [x] TLS packet capture collected
- [ ] Dedicated TCP handshake capture
- [ ] Architecture diagrams finalized
- [ ] Final repository audit
- [ ] Git commit and push

---

# 14. Demonstration

The recommended demonstration order is documented in:

```text
demo-checklist.md
```

The demonstration covers:

1. Topology and IP/service inventory
2. LAN connectivity
3. Private DNS
4. HTTPS
5. Load balancing
6. Wireshark protocol analysis
7. HTTP headers and caching
8. Backend failure
9. Phase 2 resilience
10. Fault diagnosis
11. Individual viva

---

# Phase 1 Status

The Phase 1 implementation contains the required private LAN, DNS, backend, nginx, HTTPS/TLS, caching, packet-analysis, and failure-demonstration components.

Remaining repository work is limited to final documentation/evidence packaging and the dedicated TCP handshake capture before submission.