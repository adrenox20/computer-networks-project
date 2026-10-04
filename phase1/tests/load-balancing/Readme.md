# nginx Load Balancing Test

## Objective

Verify that nginx on Mac 2 (`10.7.28.44`) operates as the reverse proxy and distributes requests between Backend A and Backend B.

## Services

### nginx

```text
Mac 2
IP: 10.7.28.44
HTTP Port: 8080
HTTPS Port: 8443
```

### Backend A

```text
Mac 2
IP: 10.7.28.44
Port: 3001
```

### Backend B

```text
Mac 3
IP: 10.7.31.67
Port: 3002
```

## HTTP Load Balancing Test

Run:

```bash
curl -i http://10.7.28.44:8080/
```

Expected response:

```text
HTTP/1.1 200 OK
```

The response should contain either:

```text
X-Backend: A
```

or:

```text
X-Backend: B
```

## Repeated Request Test

Run multiple requests:

```bash
for i in {1..5}; do
  curl -s -D - http://10.7.28.44:8080/ -o /dev/null | grep X-Backend
done
```

The test should show responses served by both backends.

Example:

```text
X-Backend: A
X-Backend: B
X-Backend: A
X-Backend: B
X-Backend: A
```

The exact order may vary depending on nginx connection handling.

## HTTPS Load Balancing Test

Run:

```bash
for i in {1..5}; do
  curl -s -D - https://app.team1.test:8443/ -o /dev/null | grep X-Backend
done
```

Expected result: responses from both Backend A and Backend B.

## Result

nginx successfully operated as the reverse proxy and load balancer. The `X-Backend` response header provides direct evidence identifying which backend served each request.

## Evidence

nginx and load-balancing screenshots:

```text
phase1/evidence/04-nginx/
```

Raw packet captures:

```text
phase1/wireshark/07-load-balancing/
```

nginx configuration:

```text
phase1/configuration/nginx/nginx.conf
```

Backend source code:

```text
phase1/backends/backend-a/
phase1/backends/backend-b/
```