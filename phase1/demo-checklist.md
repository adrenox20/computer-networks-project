# Phase 1 Demonstration Checklist

## Project

Computer Networks Project — Phase 1

## Team Network

| Machine | IP Address | Role |
|---|---|---|
| Mac 1 | `10.7.6.223` | Private DNS Server + Client |
| Mac 2 | `10.7.28.44` | nginx Edge/Load Balancer + Backend A + Client |
| Mac 3 | `10.7.31.67` | Backend B + Client |

Private network:

```text
10.7.0.0/19
```

Gateway:

```text
10.7.0.1
```

---

# Demonstration Sequence

## 1. Show Topology and IP/Service Inventory

### Show

- Network topology diagram
- IP/service table
- Machine roles
- Service ports

### Key information

```text
Mac 1 — 10.7.6.223
Private DNS — 53

Mac 2 — 10.7.28.44
nginx HTTP — 8080
nginx HTTPS — 8443
Backend A — 3001

Mac 3 — 10.7.31.67
Backend B — 3002
```

### Evidence

```text
phase1/architecture/topology.png
phase1/architecture/ip-service-table.md
phase1/architecture/architecture.md
```

---

## 2. Confirm All Machines Are on the Private LAN

Run pairwise ping tests.

### Mac 1 → Mac 2

```bash
ping -c 4 10.7.28.44
```

### Mac 1 → Mac 3

```bash
ping -c 4 10.7.31.67
```

### Mac 2 → Mac 3

```bash
ping -c 4 10.7.31.67
```

### Mac 3 → Mac 2

```bash
ping -c 4 10.7.28.44
```

### Explain

All machines use the same private `/19` LAN.

### Evidence

```text
phase1/evidence/01-lan/
phase1/wireshark/01-icmp/
```

---

## 3. Resolve the Private Domain

From a client Mac:

```bash
dig @10.7.6.223 app.team1.test
```

Expected:

```text
app.team1.test → 10.7.28.44
```

Also demonstrate:

```bash
dig @10.7.6.223 api.team1.test
```

Expected:

```text
api.team1.test → 10.7.28.44
```

### Explain

Mac 1 runs `dnsmasq` and provides authoritative private resolution for the `team1.test` namespace.

### Evidence

```text
phase1/evidence/02-dns/
phase1/wireshark/03-dns/
```

---

## 4. Open the Service over HTTPS

Use the domain name rather than the IP address:

```bash
curl -i https://app.team1.test:8443/
```

### Verify

- HTTPS connection succeeds
- No certificate warning
- No `-k` option
- HTTP `200 OK`
- `X-Backend` header visible

Example:

```text
HTTP/1.1 200 OK
X-Backend: A
```

or:

```text
HTTP/1.1 200 OK
X-Backend: B
```

### Explain

nginx on Mac 2 terminates TLS and forwards the request to the backend upstream.

### Evidence

```text
phase1/evidence/05-tls/
phase1/evidence/04-nginx/
```

---

## 5. Show Load Balancing Across Both Backends

Run repeated requests:

```bash
for i in {1..5}; do
  curl -s -D - https://app.team1.test:8443/ -o /dev/null | grep X-Backend
done
```

### Verify

Responses show both:

```text
X-Backend: A
```

and:

```text
X-Backend: B
```

### Explain

nginx distributes requests between:

```text
10.7.28.44:3001
10.7.31.67:3002
```

The `X-Backend` header identifies the backend that handled each request.

### Evidence

```text
phase1/evidence/04-nginx/
phase1/wireshark/07-load-balancing/
```

---

## 6. Show Wireshark Evidence

Open the saved captures.

### DNS

Show:

```text
DNS Query
DNS Response
```

### TCP

Show:

```text
SYN
SYN-ACK
ACK
```

Identify:

- Source IP
- Destination IP
- Source port
- Destination port

### TLS

Show:

```text
ClientHello
ServerHello
Certificate
Key Exchange
Finished
```

Explain that application data is encrypted after the TLS handshake.

### Evidence

```text
phase1/wireshark/03-dns/
phase1/wireshark/04-tcp/
phase1/wireshark/05-tls/
```

---

## 7. Show HTTP Headers and Caching

### Show Cache Headers

Backend A:

```bash
curl -i http://127.0.0.1:3001/api/status
```

Verify:

```text
Cache-Control: public, max-age=30
ETag: "backend-a-v1"
```

### Show Conditional Request

```bash
curl -i \
  -H 'If-None-Match: "backend-a-v1"' \
  http://127.0.0.1:3001/api/status
```

Expected:

```text
HTTP/1.1 304 Not Modified
```

### Explain

- A fresh cache can reuse a valid representation.
- A conditional request uses `If-None-Match`.
- `304 Not Modified` means the cached representation is still valid.
- A full request returns the resource with `200 OK`.

### Evidence

```text
phase1/evidence/06-caching/
```

---

# 8. Fail One Backend

Stop one backend.

For example, stop Backend B on Mac 3:

```text
10.7.31.67:3002
```

Then run repeated requests:

```bash
for i in {1..5}; do
  curl -s -D - https://app.team1.test:8443/ -o /dev/null | grep X-Backend
done
```

### Verify

Requests continue to reach the available backend.

### Explain

The failed backend is unavailable, but the remaining backend can still serve requests.

### Evidence

```text
phase1/evidence/08-failures/
```

---

# 9. Phase 2 DNS and Resilience

This step belongs to the Phase 2 demonstration.

Be prepared to demonstrate:

- Backup DNS
- DNS failover
- TTL behavior
- DNS-based cutover
- Resilience extensions

Phase 2 evidence will be added when those extensions are implemented.

---

# 10. Diagnose a Faculty-Injected Fault

Use systematic troubleshooting.

### Layer 1 — DNS

```bash
dig @10.7.6.223 app.team1.test
```

Verify that the domain resolves correctly.

### Layer 2 — TCP

Verify that the required destination port is reachable.

### Layer 3 — TLS

Verify:

```bash
curl -i https://app.team1.test:8443/
```

Check certificate validation and TLS connectivity.

### Layer 4 — Application

Check:

- nginx
- Backend A
- Backend B
- HTTP response
- `X-Backend`

### Diagnosis Order

```text
DNS
 ↓
TCP
 ↓
TLS
 ↓
Application
```

### Explain

Identify the affected layer before changing configuration.

---

# 11. Individual Viva

Every team member should be able to explain the complete Phase 1 system.

## Required Concepts

### Networking

- Private IPv4 addressing
- Subnet/prefix
- Default gateway
- ICMP
- TCP
- UDP
- Source and destination ports

### DNS

- DNS query
- DNS response
- Private DNS
- dnsmasq
- `app.team1.test`
- `api.team1.test`

### HTTP

- HTTP request
- HTTP response
- HTTP headers
- REST endpoint
- `X-Backend`

### nginx

- Reverse proxy
- Upstream servers
- Load balancing
- TLS termination

### TLS

- ClientHello
- ServerHello
- Certificate
- Key exchange
- Finished
- Encryption of application data
- Local CA trust

### Caching

- `Cache-Control`
- `ETag`
- `If-None-Match`
- `304 Not Modified`
- Fresh cache vs conditional request vs full request

### Troubleshooting

- DNS failure
- TCP failure
- TLS failure
- Application/backend failure
- Wrong destination port

---

# Phase 1 Evidence Locations

```text
phase1/
├── architecture/
│   ├── architecture.md
│   ├── ip-service-table.md
│   ├── topology.png
│   └── request-flow.png
│
├── configuration/
│   ├── dns/
│   ├── nginx/
│   └── tls/
│
├── backends/
│   ├── backend-a/
│   └── backend-b/
│
├── evidence/
│   ├── 01-lan/
│   ├── 02-dns/
│   ├── 03-backends/
│   ├── 04-nginx/
│   ├── 05-tls/
│   ├── 06-caching/
│   └── 08-failures/
│
└── wireshark/
    ├── 01-icmp/
    ├── 03-dns/
    ├── 04-tcp/
    ├── 05-tls/
    ├── 06-http/
    ├── 07-load-balancing/
    └── 08-failures/
```

# Final Pre-Demo Checklist

- [ ] All machines connected to the same private LAN
- [ ] IP/service table updated
- [ ] Topology diagram ready
- [ ] Request-flow diagram ready
- [ ] dnsmasq configuration ready
- [ ] nginx configuration ready
- [ ] Backend A ready on port 3001
- [ ] Backend B ready on port 3002
- [ ] TLS certificate trusted on client Macs
- [ ] HTTPS works without `curl -k`
- [ ] Load balancing shows Backend A and Backend B
- [ ] DNS resolution works
- [ ] Cache-Control header visible
- [ ] ETag visible
- [ ] 304 response demonstrated
- [ ] DNS Wireshark capture ready
- [ ] TCP handshake capture ready
- [ ] TLS Wireshark capture ready
- [ ] LAN/ICMP evidence ready
- [ ] Failure demonstrations ready
- [ ] Backend failure test ready
- [ ] All evidence placed in the appropriate evidence folders
- [ ] Raw `.pcapng` files placed in the Wireshark folders
- [ ] Private keys excluded from Git
- [ ] README updated
- [ ] Team members prepared for individual viva