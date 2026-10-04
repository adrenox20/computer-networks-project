# Phase 1 Architecture Document

## 1. System Overview

The Phase 1 system implements a private network service platform using three macOS machines connected to the same private Wi-Fi/LAN.

The system provides:

- Private DNS resolution using `dnsmasq`
- Two LAN-accessible HTTP backend services
- nginx reverse proxy and round-robin load balancing
- HTTPS/TLS termination
- HTTP caching using `Cache-Control` and `ETag`
- Packet-level observation using Wireshark
- Controlled failure demonstrations

The private application domain used by the system is:

```text
app.team1.test
```

The `.test` namespace is used as required by the project specification.

The public application entry point is nginx on:

```text
https://app.team1.test:8443
```

Port `8443` is used instead of `443` because the project permits `8443` when standard ports are unavailable.

---

## 2. Network Architecture

The implementation uses three macOS machines. Machine roles are combined where appropriate.

```text
                         Private Wi-Fi / LAN
                               |
          +--------------------+--------------------+
          |                    |                    |
          |                    |                    |
   Mac 1: 10.7.6.223    Mac 2: 10.7.28.44    Mac 3: 10.7.31.67
          |                    |                    |
       DNS Server          Edge / nginx          Backend B
       dnsmasq :53         HTTP :8080            HTTP :3002
          |                 HTTPS :8443
          |                    |
          |             Backend A :3001
          |                    |
          +--------------------+--------------------+
                               |
                         Application Response
```

### Logical request path

```text
Client
  |
  | 1. DNS query: app.team1.test
  v
Mac 1 — 10.7.6.223
dnsmasq :53
  |
  | DNS response: 10.7.28.44
  v
Mac 2 — 10.7.28.44
nginx :8443
  |
  | HTTPS/TLS termination
  |
  | Round-robin upstream selection
  +-------------------------+
  |                         |
  v                         v
Mac 2 — 10.7.28.44     Mac 3 — 10.7.31.67
Backend A :3001        Backend B :3002
  |                         |
  +------------+------------+
               |
               v
          HTTP response
```

---

## 3. Machine Roles

### Mac 1 — Private DNS Server

**IP address:** `10.7.6.223`

**Interface:** `en0`

**Subnet:** `255.255.224.0` (`/19`)

**Gateway:** `10.7.0.1`

**Primary service:** `dnsmasq`

**Service port:** `53`

Mac 1 provides the private DNS service for the `team1.test` namespace.

DNS records include:

```text
app.team1.test  -> 10.7.28.44
api.team1.test  -> 10.7.28.44
```

Mac 2 and Mac 3 were configured to use Mac 1 (`10.7.6.223`) as their DNS resolver.

---

### Mac 2 — Edge, Reverse Proxy, Load Balancer and Backend A

**IP address:** `10.7.28.44`

**Interface:** `en0`

**Subnet:** `255.255.224.0` (`/19`)

**Gateway:** `10.7.0.1`

**Services:**

```text
nginx HTTP       :8080
nginx HTTPS      :8443
Backend A        :3001
```

Mac 2 is the single public application entry point.

nginx receives client requests and forwards them to the backend upstream group.

Backend A is also hosted on Mac 2 and listens on TCP port `3001`.

---

### Mac 3 — Backend B and Client

**IP address:** `10.7.31.67`

**Interface:** `en0`

**Subnet:** `255.255.224.0` (`/19`)

**Gateway:** `10.7.0.1`

**Service:**

```text
Backend B :3002
```

Mac 3 runs Backend B on TCP port `3002`.

Mac 3 was also used as a client during packet capture and HTTPS/TLS testing.

---

## 4. Address and Service Table

| Machine | IP Address | Role | Service | Port |
|---|---|---|---|---:|
| Mac 1 | `10.7.6.223` | Private DNS | dnsmasq | `53` |
| Mac 2 | `10.7.28.44` | Edge / Reverse Proxy | nginx HTTP | `8080` |
| Mac 2 | `10.7.28.44` | Edge / TLS | nginx HTTPS | `8443` |
| Mac 2 | `10.7.28.44` | Backend A | Node.js HTTP | `3001` |
| Mac 3 | `10.7.31.67` | Backend B | Node.js HTTP | `3002` |

Common network parameters:

```text
Subnet: 255.255.224.0 (/19)
Gateway: 10.7.0.1
Interface: en0
Private domain: team1.test
Application domain: app.team1.test
```

---

## 5. Private DNS Architecture

Mac 1 runs `dnsmasq` as the private DNS resolver.

The relevant DNS records are:

```text
app.team1.test  -> 10.7.28.44
api.team1.test  -> 10.7.28.44
```

The DNS service listens on:

```text
10.7.6.223:53
```

The resolver configuration uses:

```text
no-resolv
server=8.8.8.8
server=1.1.1.1
```

The private `team1.test` records are handled locally by `dnsmasq`.

A successful lookup follows this sequence:

```text
Client
  |
  | DNS query: app.team1.test
  v
10.7.6.223:53
  |
  | DNS response: 10.7.28.44
  v
Client
```

DNS resolution was verified using `dig`, including confirmation that Mac 1 (`10.7.6.223`) was the DNS server.

---

## 6. HTTP Backend Architecture

Both backend services are implemented using Node.js and the built-in HTTP module.

### Backend A

```text
IP:   10.7.28.44
Port: 3001
```

Endpoints:

```text
GET /
GET /api/status
```

Example response:

```json
{
  "backend": "A",
  "status": "ok"
}
```

The response includes:

```text
X-Backend: A
```

### Backend B

```text
IP:   10.7.31.67
Port: 3002
```

Endpoints:

```text
GET /
GET /api/status
```

Example response:

```json
{
  "backend": "B",
  "status": "ok"
}
```

The response includes:

```text
X-Backend: B
```

Both applications listen on a LAN-accessible interface rather than only on `127.0.0.1`.

---

## 7. nginx Reverse Proxy and Load Balancing

Mac 2 (`10.7.28.44`) runs nginx as the edge reverse proxy.

The nginx upstream group contains:

```text
10.7.28.44:3001
10.7.31.67:3002
```

The load-balancing strategy is nginx's default round-robin behavior.

The HTTP entry point is:

```text
http://app.team1.test:8080
```

The HTTPS entry point is:

```text
https://app.team1.test:8443
```

The client does not need to know the backend addresses when accessing the application through the public domain.

The request path is:

```text
Client
  |
  | HTTP/HTTPS request
  v
nginx 10.7.28.44
  |
  +----> Backend A 10.7.28.44:3001
  |
  +----> Backend B 10.7.31.67:3002
```

Repeated requests were used to demonstrate responses from both backends through the `X-Backend` response header.

---

## 8. HTTPS and TLS Architecture

TLS is terminated by nginx on Mac 2.

The HTTPS listener is:

```text
10.7.28.44:8443
```

The configured server name is:

```text
app.team1.test
```

The server certificate was generated for:

```text
app.team1.test
```

using a local Team1 Certificate Authority.

Certificate files include:

```text
team1-ca.crt
app.team1.test.crt
app.team1.test.key
```

The private key files are kept out of the Git repository.

The client trust chain is:

```text
Team1 Local CA
       |
       v
app.team1.test certificate
       |
       v
nginx on 10.7.28.44:8443
```

Client verification was performed using `curl` without the `-k` option.

---

## 9. TLS Protocol Flow

A TLS 1.2 packet capture was collected between:

```text
Client: 10.7.31.67
Server: 10.7.28.44:8443
```

The observed flow includes:

```text
TCP SYN
      ↓
TCP SYN-ACK
      ↓
TCP ACK
      ↓
Client Hello
      ↓
Server Hello
      ↓
Certificate
      ↓
Server Key Exchange
      ↓
Server Hello Done
      ↓
Client Key Exchange
      ↓
Change Cipher Spec
      ↓
Encrypted Handshake Message
      ↓
Application Data
```

After TLS negotiation, application data is encrypted and is not visible as plaintext HTTP payload in the packet capture.

---

## 10. HTTP Caching Architecture

The `/api/status` endpoint implements HTTP caching support.

The response includes:

```text
Cache-Control: public, max-age=30
ETag: "backend-a-v1"
```

for Backend A and:

```text
Cache-Control: public, max-age=30
ETag: "backend-b-v1"
```

for Backend B.

A client can send a conditional request using:

```text
If-None-Match
```

When the representation has not changed, the backend returns:

```text
HTTP/1.1 304 Not Modified
```

without retransmitting the response body.

The caching flow is:

```text
Initial request
      |
      v
HTTP 200 OK
Cache-Control + ETag
      |
      v
Client stores representation
      |
      | Conditional request
      | If-None-Match
      v
Server
      |
      v
304 Not Modified
```

This demonstrates efficient HTTP validation using an entity tag.

---

## 11. Packet Analysis Architecture

Wireshark was used to observe protocol behavior at multiple layers.

The evidence collected includes:

### ICMP / LAN

Used to verify connectivity between the participating machines.

### DNS

The DNS query and response between clients and:

```text
10.7.6.223:53
```

were captured.

### TCP

TCP connection establishment was observed using:

```text
SYN
SYN-ACK
ACK
```

### TLS

The HTTPS handshake between:

```text
10.7.31.67
        |
        | TCP 8443
        v
10.7.28.44
```

was captured.

### HTTP

HTTP request and response headers were observed for backend and load-balancing tests.

### Load Balancing

Repeated requests were used to identify the backend serving each response using:

```text
X-Backend: A
X-Backend: B
```

---

## 12. Failure Testing Architecture

Phase 1 includes controlled failure demonstrations to identify the layer at which a request fails.

The tested scenarios include:

### Wrong DNS server/record

Demonstrates failure at the DNS/name-resolution layer.

### One backend stopped

Demonstrates the effect of an unavailable backend on the load-balancing layer.

### Both backends stopped

Demonstrates application/service unavailability behind the edge.

### Wrong destination port

Demonstrates a TCP connection failure when the destination port does not have the expected service.

The diagnostic approach is:

```text
DNS
 ↓
TCP
 ↓
TLS
 ↓
HTTP
 ↓
Backend/Application
```

The failing layer is identified by determining the highest protocol layer successfully completed before the failure.

---

## 13. Complete End-to-End Request Flow

A normal HTTPS request to the application follows this sequence:

```text
1. Client requests:
   https://app.team1.test:8443/

2. DNS:
   app.team1.test
          ↓
   10.7.6.223:53
          ↓
   10.7.28.44

3. TCP:
   Client ephemeral port
          ↓
   10.7.28.44:8443
          ↓
   SYN → SYN-ACK → ACK

4. TLS:
   ClientHello
          ↓
   ServerHello
          ↓
   Certificate
          ↓
   Key Exchange
          ↓
   Finished / encrypted handshake

5. HTTPS:
   Encrypted HTTP request
          ↓
   nginx on 10.7.28.44:8443

6. Load balancing:
   nginx upstream
          ↓
   Backend A :3001
       OR
   Backend B :3002

7. Backend response:
   X-Backend: A/B
          ↓
   nginx
          ↓
   TLS encryption
          ↓
   Client
```

This flow connects the major Phase 1 concepts: DNS, TCP, TLS, HTTPS, reverse proxying, load balancing, HTTP headers, caching, and packet analysis.

---

## 14. Phase 1 Evidence Mapping

| Area | Evidence |
|---|---|
| LAN connectivity | ICMP screenshots and packet captures |
| Private DNS | `dig` output and DNS Wireshark captures |
| Backend A | Backend A `curl` responses |
| Backend B | Backend B `curl` responses |
| nginx/load balancing | Repeated requests showing `X-Backend: A/B` |
| TLS | HTTPS `curl` verification and TLS Wireshark capture |
| TLS handshake | ClientHello, ServerHello, Certificate, Key Exchange and encrypted handshake evidence |
| HTTP caching | `Cache-Control`, ETag and `304 Not Modified` |
| Failure testing | Wrong DNS, one backend down, both backends down and wrong port |
| Source/configuration | Backend source, dnsmasq configuration, nginx configuration and TLS configuration |

---

## 15. Security and Repository Notes

Private cryptographic keys are not part of the repository.

The following file types are excluded from version control:

```text
*.key
*.csr
*.srl
```

The repository contains the public certificates and configuration/documentation necessary to explain the TLS setup without exposing private keys.

The live system uses the private `team1.test` namespace and the LAN addresses listed in this document.