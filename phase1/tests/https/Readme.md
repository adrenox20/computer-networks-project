# HTTPS and TLS Test

## Objective

Verify that nginx on Mac 2 terminates TLS and provides secure access to the application through the private domain `app.team1.test`.

## HTTPS Service

```text
Mac 2
IP: 10.7.28.44
Service: nginx
HTTPS Port: 8443
Domain: app.team1.test
```

## HTTPS Request Test

Run:

```bash
curl -i https://app.team1.test:8443/
```

Expected result:

```text
HTTP/1.1 200 OK
```

The response should contain:

```text
X-Backend: A
```

or:

```text
X-Backend: B
```

## Certificate Validation

The Team 1 local CA certificate was installed in the client trust store.

The HTTPS demonstration uses normal certificate validation.

The `-k` option is not used.

## TLS Handshake Verification

A Wireshark capture was performed while accessing:

```text
https://app.team1.test:8443/
```

The capture demonstrates the TLS handshake, including:

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

After the TLS handshake, application data is encrypted and cannot be read as plaintext in the packet capture.

## Result

HTTPS access through `app.team1.test` was successfully verified using the local CA certificate and nginx TLS termination on Mac 2 (`10.7.28.44`).

## Evidence

TLS screenshots:

```text
phase1/evidence/05-tls/
```

Raw TLS capture:

```text
phase1/wireshark/05-tls/
```

TLS configuration:

```text
phase1/configuration/tls/
```

nginx configuration:

```text
phase1/configuration/nginx/nginx.conf
```