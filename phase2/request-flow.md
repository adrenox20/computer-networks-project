# Phase 2 Request Flow

## 1. Overview

The Phase 2 request path is designed to separate:

1. DNS resolution
2. TCP connectivity
3. TLS termination
4. Edge proxying
5. Backend isolation
6. Backend processing

The application domain is:

```text
app.team1.test
```

The normal HTTPS request path is:

```text
Client
  │
  ▼
DNS Resolution
  │
  ▼
Active Edge NGINX
  │
  ▼
Backend Isolation Gateway
  │
  ├──► Backend A
  │
  └──► Backend B
```

---

# 2. Normal DNS Resolution

The client first needs to resolve:

```text
app.team1.test
```

The primary DNS resolver is:

```text
10.7.7.82:53
```

The backup resolver is:

```text
10.7.20.185:53
```

Under normal conditions:

```text
Client
   │
   │ DNS query:
   │ app.team1.test
   ▼
Primary DNS
10.7.7.82:53
   │
   │ DNS A response
   ▼
Client
```

The DNS response provides the IP address currently associated with the application domain.

The DNS record uses a TTL of:

```text
30 seconds
```

---

# 3. DNS Response and Edge Selection

Before edge migration, the application can resolve to the active edge:

```text
app.team1.test
       │
       ▼
10.7.20.185
```

The client then uses that address for the HTTPS connection:

```text
10.7.20.185:443
```

After controlled edge migration and TTL expiry, the DNS answer becomes:

```text
app.team1.test
       │
       ▼
10.7.7.82
```

The client then connects to:

```text
10.7.7.82:443
```

---

# 4. TCP Connection

After DNS resolution, the client establishes a TCP connection to HTTPS port `443`.

Normal path:

```text
Client
   │
   │ TCP connection
   ▼
10.7.20.185:443
   │
   ▼
Active NGINX
```

The TCP connection must succeed before TLS negotiation can begin.

This layer is independently tested using:

```text
nc -vz 10.7.7.82 443
```

A successful TCP connection confirms that the destination host and port are reachable.

---

# 5. TLS Handshake

Once the TCP connection is established, the client performs a TLS handshake.

```text
Client
   │
   │ TLS ClientHello
   ▼
NGINX :443
   │
   │ Server certificate
   ▼
Client
   │
   │ TLS negotiation
   ▼
Encrypted HTTPS connection
```

TLS is terminated at the NGINX edge.

The TLS endpoint is tested using:

```text
openssl s_client -connect 10.7.7.82:443 -servername app.team1.test
```

The purpose of this test is to verify that:

- Port 443 accepts the connection
- TLS negotiation occurs
- The server presents its certificate
- The expected TLS endpoint is responding

---

# 6. HTTPS Request Reaches NGINX

After TLS is established, the client sends the HTTP request through the encrypted HTTPS connection.

Example:

```text
GET /
Host: app.team1.test
```

The request reaches the NGINX edge.

```text
Client
   │
   │ HTTPS request
   ▼
NGINX
10.7.20.185:443
```

NGINX acts as the reverse proxy.

It does not directly implement the application logic.

Instead, it forwards the request to one of the backend services.

---

# 7. NGINX Backend Selection

The active NGINX upstream contains two backend services:

```text
10.7.7.82:3001
10.7.7.82:3002
```

Therefore:

```text
                  ┌──► Backend A
                  │    10.7.7.82:3001
NGINX ────────────┤
                  │
                  └──► Backend B
                       10.7.7.82:3002
```

When both backends are healthy, requests can be served by either backend.

Each backend identifies itself using the response header:

```text
X-Backend: A
```

or:

```text
X-Backend: B
```

This allows the request path to be verified during the demonstration.

---

# 8. Backend Isolation Gateway

The NGINX edge does not directly access the backend container ports.

Instead, requests pass through the backend isolation gateway.

```text
Active NGINX
      │
      ▼
10.7.7.82:3001 / 3002
      │
      ▼
Isolation Gateway
      │
      ├──► Local Backend A
      │
      └──► Local Backend B
```

The gateway checks the source IP.

The permitted edge source is:

```text
10.7.20.185
```

If the request originates from the authorized edge:

```text
Source:
10.7.20.185

Result:
ALLOWED
```

The gateway forwards the request to the corresponding local backend.

---

# 9. Unauthorized Backend Request

If an unauthorized source attempts to access the backend gateway:

```text
Unauthorized Source
        │
        ▼
10.7.7.82:3001 / 3002
        │
        ▼
Isolation Gateway
        │
        X
      DENIED
```

The gateway records the blocked source.

This prevents arbitrary clients from bypassing the NGINX edge and directly accessing the backend services.

---

# 10. Backend A Response

If NGINX selects Backend A:

```text
NGINX
   │
   ▼
10.7.7.82:3001
   │
   ▼
Backend A
   │
   │ X-Backend: A
   ▼
Isolation Gateway
   │
   ▼
NGINX
   │
   ▼
Client
```

The client receives the application response through NGINX.

---

# 11. Backend B Response

If NGINX selects Backend B:

```text
NGINX
   │
   ▼
10.7.7.82:3002
   │
   ▼
Backend B
   │
   │ X-Backend: B
   ▼
Isolation Gateway
   │
   ▼
NGINX
   │
   ▼
Client
```

The client therefore receives a response from Backend B without knowing the backend's internal implementation.

---

# 12. Complete Normal HTTPS Flow

The complete request path is:

```text
                         CLIENT
                           │
                           │ 1. DNS Query
                           ▼
                    PRIMARY DNS :53
                           │
                           │ DNS Answer
                           ▼
                         CLIENT
                           │
                           │ 2. TCP :443
                           ▼
                    ACTIVE NGINX
                 10.7.20.185:443
                           │
                           │ 3. TLS
                           ▼
                    HTTPS Session
                           │
                           │ 4. HTTP Request
                           ▼
                    NGINX Reverse Proxy
                           │
                           │ 5. Backend Proxy
                           ▼
                ISOLATION GATEWAY
                           │
                    ┌──────┴──────┐
                    │             │
                    ▼             ▼
              BACKEND A      BACKEND B
               :3001          :3002
                    │             │
                    └──────┬──────┘
                           │
                           ▼
                      HTTP Response
                           │
                           ▼
                         NGINX
                           │
                           ▼
                         CLIENT
```

---

# 13. Primary DNS Failure Flow

If the primary DNS service is stopped:

```text
Client
   │
   │ Query primary DNS
   ▼
10.7.7.82:53
   │
   X
Timeout / failure
```

The client can instead query the backup resolver:

```text
Client
   │
   ▼
10.7.20.185:53
   │
   ▼
Backup DNS
   │
   ▼
DNS Answer
```

The important distinction is:

```text
DNS service failure
        ≠
Application failure
```

The application backends can remain healthy even when the primary DNS service is unavailable.

---

# 14. DNS TTL Flow

The DNS TTL controls how long a DNS answer can remain cached.

The Phase 2 TTL is:

```text
30 seconds
```

The sequence is:

```text
Initial DNS Answer
        │
        ▼
Client / Resolver caches answer
        │
        ▼
DNS record is changed
        │
        ▼
Old cached answer remains temporarily
        │
        ▼
TTL expires
        │
        ▼
New DNS query
        │
        ▼
New DNS answer
```

This behavior is used during controlled edge migration.

---

# 15. DNS Cache Before TTL Expiry

Suppose the old edge is:

```text
10.7.20.185
```

and the DNS record is changed to:

```text
10.7.7.82
```

A resolver that still has the old answer cached can temporarily return:

```text
10.7.20.185
```

even though the authoritative DNS record has already changed.

Therefore:

```text
DNS record changed
        │
        ▼
Existing cache
        │
        ▼
Old address
```

The old answer remains until the relevant TTL expires or the cache is flushed.

---

# 16. DNS Cache After TTL Expiry

After the 30-second TTL expires:

```text
Cached answer
      │
      ▼
Expires
      │
      ▼
New DNS query
      │
      ▼
10.7.7.82
```

The client then begins using the standby edge.

This demonstrates why DNS migration is not necessarily instantaneous.

---

# 17. Backend A Failure Flow

Under normal conditions:

```text
NGINX
  │
  ├──► Backend A
  │
  └──► Backend B
```

When Backend A is stopped:

```text
NGINX
  │
  ├──► Backend A
  │        X
  │      FAILED
  │
  └──► Backend B
           │
           ▼
        RESPONSE
```

NGINX detects that Backend A is unavailable and continues using Backend B.

The application therefore remains available.

---

# 18. Backend A Recovery

When Backend A is restarted:

```text
Backend A
    │
    ▼
Healthy
    │
    ▼
NGINX upstream
    │
    ├──► Backend A
    │
    └──► Backend B
```

Backend A becomes available again.

The recovery evidence verifies that the service has returned to the healthy backend pool.

---

# 19. Active Edge Migration Flow

The active edge is initially:

```text
10.7.20.185:443
```

The standby edge is:

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

The DNS record is then changed:

```text
app.team1.test
       │
       ▼
10.7.7.82
       │
       ▼
Standby NGINX
```

Because the TTL is 30 seconds, existing cached answers can continue directing traffic to the old edge temporarily.

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

---

# 20. Standby Edge Request Flow

After migration, the request path becomes:

```text
Client
   │
   │ DNS
   ▼
10.7.7.82
   │
   │ HTTPS :443
   ▼
Standby NGINX
   │
   │ Proxy
   ▼
Local backend connectivity
   │
   ├──► Backend A
   │
   └──► Backend B
   │
   ▼
Response
   │
   ▼
Client
```

The standby edge is therefore capable of serving the same application domain after the DNS cutover.

---

# 21. Troubleshooting Request Flow

Troubleshooting follows a strict layer-by-layer sequence.

## Layer 1 — DNS

Test:

```bash
dig @10.7.7.82 app.team1.test
```

Question:

```text
Does the domain resolve?
```

If no:

```text
Investigate DNS.
```

If yes:

```text
Continue to TCP.
```

---

## Layer 2 — TCP

Test:

```bash
nc -vz 10.7.7.82 443
```

Question:

```text
Can the client establish a TCP connection to port 443?
```

If no:

```text
Investigate host availability,
routing, firewall, or port exposure.
```

If yes:

```text
Continue to TLS.
```

---

## Layer 3 — TLS

Test:

```bash
openssl s_client \
  -connect 10.7.7.82:443 \
  -servername app.team1.test
```

Question:

```text
Does the TLS endpoint respond and present a certificate?
```

If no:

```text
Investigate TLS / NGINX configuration.
```

If yes:

```text
Continue to application testing.
```

---

## Layer 4 — Application

Test:

```bash
curl -k https://app.team1.test/
```

Question:

```text
Does the application return a valid HTTP response?
```

If no:

```text
Investigate NGINX proxying or backend services.
```

If yes:

```text
Application path is functioning.
```

---

# 22. Failure Classification

The architecture allows failures to be classified as follows:

| Observed Failure | Likely Layer |
|---|---|
| Domain does not resolve | DNS |
| Domain resolves but port 443 is unreachable | TCP/network |
| TCP works but TLS handshake fails | TLS |
| TLS works but HTTP request fails | NGINX/application |
| Backend A fails but B responds | Backend A |
| Both backends fail | Backend/application layer |
| Old edge continues after DNS change | DNS cache/TTL |
| Unauthorized backend connection denied | Service isolation |

---

# 23. Request Flow Summary

The Phase 2 architecture follows this complete sequence:

```text
             DNS
              │
              ▼
       IP Address Selection
              │
              ▼
             TCP
              │
              ▼
             TLS
              │
              ▼
       NGINX Reverse Proxy
              │
              ▼
      Backend Isolation
              │
        ┌─────┴─────┐
        ▼           ▼
    Backend A   Backend B
        │           │
        └─────┬─────┘
              ▼
          Application
              │
              ▼
           Response
              │
              ▼
            Client
```

The same architecture supports failure recovery through:

```text
Primary DNS failure
        ↓
Backup DNS

Backend A failure
        ↓
Backend B

Active edge migration
        ↓
Standby edge

DNS/TCP/TLS/Application failure
        ↓
Layer-by-layer troubleshooting
```

---

# 24. Key Architecture Principle

Phase 2 does not treat the application as a single service.

It separates the system into independently testable layers:

```text
DNS
│
├── Primary
└── Backup

EDGE
│
├── Active
└── Standby

BACKEND
│
├── A
└── B

TROUBLESHOOTING
│
├── DNS
├── TCP
├── TLS
└── Application
```

This separation provides controlled failure testing, easier troubleshooting, and a clear demonstration of resilience and recovery.