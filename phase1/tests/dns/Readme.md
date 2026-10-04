# Private DNS Test

## Objective

Verify that Mac 1 provides private DNS resolution for the `team1.test` namespace and that the required application records resolve to Mac 2.

## DNS Server

```text
Mac 1
IP: 10.7.6.223
Service: dnsmasq
Port: 53
Interface: en0
```

## DNS Records

```text
app.team1.test → 10.7.28.44
api.team1.test → 10.7.28.44
```

## Test 1 — app.team1.test

Run:

```bash
dig @10.7.6.223 app.team1.test
```

Expected result:

```text
app.team1.test → 10.7.28.44
```

## Test 2 — api.team1.test

Run:

```bash
dig @10.7.6.223 api.team1.test
```

Expected result:

```text
api.team1.test → 10.7.28.44
```

## Client Resolver Test

Mac 2 and Mac 3 were configured to use Mac 1 as their DNS resolver:

```text
10.7.6.223
```

Resolution was verified from the client Macs.

## Configuration Validation

The dnsmasq configuration was checked using:

```bash
dnsmasq --test -C /opt/homebrew/etc/dnsmasq.conf
```

Expected result:

```text
syntax check OK
```

## Result

Private DNS resolution was successfully demonstrated for both required application records.

## Evidence

DNS screenshots:

```text
phase1/evidence/02-dns/
```

Raw Wireshark captures:

```text
phase1/wireshark/03-dns/
```

DNS configuration:

```text
phase1/configuration/dns/dnsmasq.conf
```