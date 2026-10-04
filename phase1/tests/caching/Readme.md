# HTTP Caching Test

## Objective

Verify HTTP caching behavior using `Cache-Control` and `ETag`, including a conditional request that returns `304 Not Modified`.

## Backend A

```text
Mac 2
IP: 10.7.28.44
Port: 3001
```

### Initial Request

Run:

```bash
curl -i http://127.0.0.1:3001/api/status
```

Expected response includes:

```text
HTTP/1.1 200 OK
Cache-Control: public, max-age=30
ETag: "backend-a-v1"
```

### Conditional Request

Run:

```bash
curl -i \
  -H 'If-None-Match: "backend-a-v1"' \
  http://127.0.0.1:3001/api/status
```

Expected response:

```text
HTTP/1.1 304 Not Modified
```

## Backend B

```text
Mac 3
IP: 10.7.31.67
Port: 3002
```

### Initial Request

Run:

```bash
curl -i http://127.0.0.1:3002/api/status
```

Expected response includes:

```text
HTTP/1.1 200 OK
Cache-Control: public, max-age=30
ETag: "backend-b-v1"
```

### Conditional Request

Run:

```bash
curl -i \
  -H 'If-None-Match: "backend-b-v1"' \
  http://127.0.0.1:3002/api/status
```

Expected response:

```text
HTTP/1.1 304 Not Modified
```

## Caching Behavior

The backend responses demonstrate:

- `Cache-Control` specifies the caching policy and freshness lifetime.
- `ETag` identifies the current representation.
- `If-None-Match` allows the client to validate a previously cached representation.
- `304 Not Modified` indicates that the representation has not changed and does not need to be retransmitted.

## Result

Both backend applications successfully provide cache-control information and support ETag-based conditional requests. A `304 Not Modified` response was successfully demonstrated.

## Evidence

Caching screenshots:

```text
phase1/evidence/06-caching/
```

Backend source code:

```text
phase1/backends/backend-a/
phase1/backends/backend-b/
```