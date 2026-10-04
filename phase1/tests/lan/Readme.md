# LAN Connectivity Test

## Objective

Verify that all three team Macs are connected to the same private LAN and can reach each other using ICMP.

## Network Inventory

| Machine | IP Address | Interface |
|---|---|---|
| Mac 1 | `10.7.6.223` | `en0` |
| Mac 2 | `10.7.28.44` | `en0` |
| Mac 3 | `10.7.31.67` | `en0` |

Subnet:

```text
255.255.224.0 (/19)
```

Gateway:

```text
10.7.0.1
```

## Connectivity Tests

### Mac 1 → Mac 2

```bash
ping -c 4 10.7.28.44
```

Result: 4/4 packets received, 0% packet loss.

### Mac 1 → Mac 3

```bash
ping -c 4 10.7.31.67
```

Result: 4/4 packets received, 0% packet loss.

### Mac 2 → Mac 3

```bash
ping -c 4 10.7.31.67
```

Result: 4/4 packets received, 0% packet loss.

### Mac 3 → Mac 2

```bash
ping -c 4 10.7.28.44
```

Result: 4/4 packets received, 0% packet loss.

## Additional Verification

ICMP traffic was captured using Wireshark to verify:

- ICMP Echo Request
- ICMP Echo Reply
- Source and destination IP addresses
- Packet count

## Result

All required LAN connectivity paths were successfully verified.

Initial incoming ICMP filtering toward Mac 1 was caused by macOS Stealth Mode. After disabling Stealth Mode on Mac 1, connectivity from the other Macs was successfully verified.

## Evidence

Screenshots:

```text
phase1/evidence/01-lan/
```

Raw Wireshark captures:

```text
phase1/wireshark/01-icmp/
```