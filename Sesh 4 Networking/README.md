# Networking Tasks

---

## Task 1 & Task 2: Command Executions, Outputs & Explanations

### 1. `ping` (Packet InterNet Groper)

- **Purpose:** Checks whether a remote host is reachable over the network using ICMP (Internet Control Message Protocol), and measures the round-trip time (RTT) for packets sent to it.

- **Command Executed:**

  ```bash
  ping -c 4 google.com
  ```

- **Terminal Output:**

  ```text
  PING google.com (142.250.195.238): 56 data bytes
  64 bytes from 142.250.195.238: icmp_seq=0 ttl=116 time=18.412 ms
  64 bytes from 142.250.195.238: icmp_seq=1 ttl=116 time=16.890 ms
  64 bytes from 142.250.195.238: icmp_seq=2 ttl=116 time=17.105 ms
  64 bytes from 142.250.195.238: icmp_seq=3 ttl=116 time=19.221 ms

  --- google.com ping statistics ---
  4 packets transmitted, 4 packets received, 0.0% packet loss
  round-trip min/avg/max/stddev = 16.890/17.907/19.221/0.923 ms
  ```

- **What I Understood:** `ping` is a quick way to verify basic layer-3 connectivity to a host. Packet loss or timeouts when pinging usually point to DNS problems, routing issues, ICMP being blocked by a firewall, or the target host being down.

---

### 2. `curl` (Client URL Tool)

- **Purpose:** A command-line tool for transferring data to or from a server over protocols such as HTTP, HTTPS, and FTP.

- **Command Executed:**

  ```bash
  curl -I https://httpbin.org/get
  ```

- **Terminal Output:**

  ```text
  HTTP/2 200 
  date: Wed, 02 Sep 2026 16:05:10 GMT
  content-type: application/json
  content-length: 305
  server: gunicorn/19.9.0
  access-control-allow-origin: *
  access-control-allow-credentials: true
  ```

- **What I Understood:** `curl` is heavily used for testing API endpoints and service health checks, inspecting response headers, checking SSL certificates, and debugging HTTP status codes such as `200 OK`, `404 Not Found`, or `502 Bad Gateway`.

---

### 3. `ifconfig` / `ip` (Network Interface Configuration)

- **Purpose:** Displays (and can configure) network interfaces along with their IP addresses, netmasks, and broadcast addresses.

- **Command Executed:**

  ```bash
  ifconfig lo0
  ```

- **Terminal Output:**

  ```text
  lo0: flags=8049<UP,LOOPBACK,RUNNING,MULTICAST> mtu 16384
    options=1203<RXCSUM,TXCSUM,SHARED,VLAN_HWTAGGING,RSC>
    inet 127.0.0.1 netmask 0xff000000 
    inet6 ::1 prefixlen 128 
    inet6 fe80::1%lo0 prefixlen 64 scopeid 0x1 
    nd6 options=201<PERFORMDN,AUTO_LINKLOCAL>
  ```

- **What I Understood:** This command is handy for finding the local machine's IP address (`inet`), identifying the loopback interface (`127.0.0.1`), checking MAC addresses (`ether`), and confirming an interface's status when binding containers or web servers to a specific network adapter.

---

### 4. `netstat` / `ss` (Socket Statistics)

- **Purpose:** Shows active network connections, listening ports, routing tables, and general socket statistics.

- **Command Executed:**

  ```bash
  netstat -an | grep LISTEN | head -n 5
  ```

- **Terminal Output:**

  ```text
  tcp4       0      0  *.5000                 *.*                    LISTEN
  tcp4       0      0  *.8080                 *.*                    LISTEN
  tcp4       0      0  *.3000                 *.*                    LISTEN
  tcp46      0      0  *.80                   *.*                    LISTEN
  tcp4       0      0  127.0.0.1.6379         *.*                    LISTEN
  ```

- **What I Understood:** Useful for catching port conflicts (like an `Address already in use` error), confirming a web server or database is actually listening on the expected port (e.g., `80`, `443`, `3306`), and reviewing which connections are currently open.

---

### 5. `traceroute` / `tracepath`

- **Purpose:** Traces the path (the sequence of routers, or "hops") that packets take to reach a destination host.

- **Command Executed:**

  ```bash
  traceroute -m 5 8.8.8.8
  ```

- **Terminal Output:**

  ```text
  traceroute to 8.8.8.8 (8.8.8.8), 5 hops max, 52 byte packets
   1  192.168.1.1 (192.168.1.1)  2.105 ms  1.450 ms  1.210 ms
   2  10.230.0.1 (10.230.0.1)  12.314 ms  11.200 ms  10.980 ms
   3  72.14.215.89 (72.14.215.89)  15.430 ms  14.890 ms  15.102 ms
   4  142.250.224.23 (142.250.224.23)  16.120 ms  16.450 ms  16.010 ms
   5  dns.google (8.8.8.8)  16.950 ms  17.110 ms  16.820 ms
  ```

- **What I Understood:** Great for pinpointing exactly where along a route packets are slowing down or getting dropped, which makes it useful when troubleshooting WAN connectivity issues or unexpectedly high latency.

---

### 6. `nslookup` / `dig` (Domain Information Groper)

- **Purpose:** Queries DNS name servers to resolve domain names to IP addresses and to inspect DNS records (A, AAAA, MX, CNAME, TXT).

- **Command Executed:**

  ```bash
  nslookup github.com
  ```

- **Terminal Output:**

  ```text
  Server:       192.168.1.1
  Address:      192.168.1.1#53

  Non-authoritative answer:
  Name:     github.com
  Address:  20.205.243.166
  ```

- **What I Understood:** This is essential for verifying domain-to-IP resolution, confirming that DNS records (like CNAME or A records) have updated correctly after a deployment, and testing internal cluster DNS resolution (e.g., CoreDNS in Kubernetes).

---

### 7. `nmap` (Network Mapper)

- **Purpose:** A network discovery and security auditing tool used to find open ports, detect running services, and fingerprint operating systems.

- **Command Executed:**

  ```bash
  nmap -p 80,443 scanme.nmap.org
  ```

- **Terminal Output:**

  ```text
  Starting Nmap 7.94 ( https://nmap.org ) at 2026-09-02 16:06 IST
  Nmap scan report for scanme.nmap.org (45.33.32.156)
  Host is up (0.21s latency).

  PORT    STATE SERVICE
  80/tcp  open  http
  443/tcp open  https

  Nmap done: 1 IP address (1 host up) scanned in 1.45 seconds
  ```

- **What I Understood:** Security and infrastructure teams rely on `nmap` to audit which ports are open on cloud security groups, double-check that firewall rules are behaving as expected, and confirm that non-essential ports stay closed.
