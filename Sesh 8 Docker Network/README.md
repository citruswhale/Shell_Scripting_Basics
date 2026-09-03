# Docker Networking & Volumes

---

## Task 1: Docker Container Networking

### Goal

Create three containers — **frontend**, **backend**, and **database** — spread across three separate Docker networks, with the backend attached to two of them, and verify connectivity between the containers.

### Step 1: Create Three Docker Networks

```bash
docker network create frontend-net
docker network create backend-net
docker network create db-net
```

*Expected Output:*

```text
a1b2c3d4e5f6...
b2c3d4e5f6a7...
c3d4e5f6a7b8...
```

### Step 2: List the Networks

```bash
docker network ls
```

*Expected Output:*

```text
NETWORK ID     NAME            DRIVER    SCOPE
a1b2c3d4e5f6   frontend-net    bridge    local
b2c3d4e5f6a7   backend-net     bridge    local
c3d4e5f6a7b8   db-net          bridge    local
```

### Step 3: Create the Frontend Container (Nginx) on `frontend-net`

```bash
docker run -d --name frontend --network frontend-net nginx:alpine
```

### Step 4: Create the Backend Container (Alpine) — Joined to 2 Networks

```bash
# Attach to the first network at creation time
docker run -d --name backend --network frontend-net alpine sleep infinity

# Connect the same container to the second network
docker network connect backend-net backend
```

### Step 5: Create the Database Container (MySQL) on `db-net`

```bash
docker run -d --name database --network db-net \
  -e MYSQL_ROOT_PASSWORD=rootpass \
  -e MYSQL_DATABASE=appdb \
  mysql:8.0
```

### Step 6: Verify Network Membership

```bash
docker network inspect frontend-net --format '{{range .Containers}}{{.Name}} {{end}}'
docker network inspect backend-net --format '{{range .Containers}}{{.Name}} {{end}}'
docker network inspect db-net --format '{{range .Containers}}{{.Name}} {{end}}'
```

*Expected Output:*

```text
frontend backend
backend
database
```

This confirms:
- `frontend-net` contains **frontend** and **backend**.
- `backend-net` contains **backend** only.
- `db-net` contains **database** only.

### Step 7: Check Connectivity Between Containers

**Frontend ↔ Backend** (both share `frontend-net`, so this should succeed):

```bash
docker exec frontend ping -c 3 backend
```

*Expected Output:*

```text
PING backend (172.18.0.3): 56 data bytes
64 bytes from 172.18.0.3: seq=0 ttl=64 time=0.089 ms
64 bytes from 172.18.0.3: seq=1 ttl=64 time=0.075 ms
64 bytes from 172.18.0.3: seq=2 ttl=64 time=0.081 ms

--- backend ping statistics ---
3 packets transmitted, 3 packets received, 0% packet loss
```

**Backend ↔ Database** (both reachable via `backend-net`/`db-net` since backend is on both):

```bash
docker exec backend ping -c 3 database
```

*Expected Output:*

```text
PING database (172.19.0.2): 56 data bytes
64 bytes from 172.19.0.2: seq=0 ttl=64 time=0.102 ms
64 bytes from 172.19.0.2: seq=1 ttl=64 time=0.097 ms
64 bytes from 172.19.0.2: seq=2 ttl=64 time=0.099 ms

--- database ping statistics ---
3 packets transmitted, 3 packets received, 0% packet loss
```

**Frontend ↔ Database** (should FAIL — frontend has no route to `db-net`):

```bash
docker exec frontend ping -c 3 database
```

*Expected Output:*

```text
ping: bad address 'database'
```

### Key Takeaway

Docker's default bridge networks provide **isolation by design**. Containers can only resolve and reach each other by name if they share a common user-defined network. Since the backend container is attached to both `frontend-net` and `backend-net`/`db-net`, it can talk to both the frontend and the database, but the frontend and database — having no network in common — cannot reach each other directly. This is a common pattern for enforcing tiered access (e.g., only the backend/API layer should ever be able to reach the database).

---

## Task 2: Host Network

### Goal

Run an Apache2 container using the host's network stack directly, so the container's ports map 1:1 onto the host without any NAT/port-forwarding layer.

### Step 1: Pull the Apache2 Image

```bash
docker pull httpd:latest
```

*Expected Output:*

```text
latest: Pulling from library/httpd
Status: Downloaded newer image for httpd:latest
docker.io/library/httpd:latest
```

### Step 2: Run the Container Using the Host Network

```bash
docker run -d --name apache-host --network host httpd:latest
```

### Step 3: Verify the Container Is Running

```bash
docker ps
```

*Expected Output:*

```text
CONTAINER ID   IMAGE          COMMAND              CREATED         STATUS         PORTS     NAMES
d4e5f6a7b8c9   httpd:latest   "httpd-foreground"   5 seconds ago   Up 5 seconds             apache-host
```

Note that no `PORTS` mapping is shown — with `--network host`, the container shares the host's network namespace entirely, so Apache is listening directly on the host's port 80.

### Step 4: Access the Apache Website

```bash
curl http://localhost:80
```

*Expected Output:*

```text
<html><body><h1>It works!</h1></body></html>
```

### Key Takeaway

The `host` network driver removes network isolation between the container and the Docker host — the container uses the host's IP and ports directly. This gives the best possible network performance (no NAT overhead) but sacrifices isolation and can cause port conflicts if the host already has something listening on the same port. It's typically used for performance-sensitive services or tools that need to observe host-level network traffic.

---

## Task 3: Bind Mount

### Goal

Serve a local `index.html` file inside an Nginx container using a bind mount, then confirm that edits made on the host are reflected live without restarting the container.

### Step 1: Create a Local Folder and `index.html`

```bash
mkdir -p ~/bind-mount-demo
echo "Hello students" > ~/bind-mount-demo/index.html
```

*(This repository includes the same folder at `bind-mount-demo/index.html` for reference.)*

### Step 2: Run an Nginx Container with the Folder Bind-Mounted

```bash
docker run -d --name nginx-bindmount \
  -p 8080:80 \
  -v ~/bind-mount-demo:/usr/share/nginx/html:ro \
  nginx:alpine
```

### Step 3: Access the Website and Verify the Content

```bash
curl http://localhost:8080
```

*Expected Output:*

```text
Hello students
```

### Step 4: Modify `index.html` on the Host

```bash
echo "Hello students - updated content!" > ~/bind-mount-demo/index.html
```

### Step 5: Verify the Change Without Restarting the Container

```bash
curl http://localhost:8080
```

*Expected Output:*

```text
Hello students - updated content!
```

### Key Takeaway

A bind mount links a specific path on the host directly into the container's filesystem. Since it's a live reference to the host path (not a copy), any changes made on the host are immediately visible inside the container — no rebuild or restart required. This makes bind mounts ideal for local development workflows, though for production and multi-host setups, named volumes are generally preferred since they aren't tied to a specific host path.

---

## Task 4: Overlay Network — Research Notes

### What Is an Overlay Network?

An **overlay network** is a virtual network that spans multiple Docker hosts, letting containers running on different physical or virtual machines communicate with each other as if they were on the same local network. Docker implements this using **VXLAN** encapsulation, which wraps container-to-container traffic in an outer packet that can be routed across the underlying physical network between hosts.

Overlay networks are primarily used with **Docker Swarm** (Docker's native clustering/orchestration tool), where each node in the swarm can host containers that still need to talk to each other regardless of which physical machine they land on.

### Use Cases

- **Multi-host microservices:** Services split across several Docker hosts (e.g., a Swarm cluster) can discover and communicate with each other by service name, regardless of which node they're scheduled on.
- **High availability & scaling:** As replicas of a service are scheduled across different nodes for redundancy, the overlay network ensures they all remain reachable under one logical network.
- **Service isolation across a cluster:** Multiple overlay networks can be created to segment traffic between different application stacks, similar to how bridge networks isolate containers on a single host — but extended across the whole cluster.
- **Secure encrypted inter-node traffic:** Overlay networks support optional IPsec encryption, protecting traffic that flows over the underlying physical network between hosts.

### How It Works Across Multiple Hosts

1. A **key-value store** (Docker Swarm uses its own built-in Raft-based store) keeps track of network state, IP address assignments, and which containers belong to which overlay network — this metadata is synced across every node in the cluster.
2. When two containers on different hosts need to communicate, Docker encapsulates their traffic using **VXLAN**, which tags each packet with a Virtual Network Identifier (VNI) so multiple overlay networks can coexist on the same physical infrastructure without their traffic mixing.
3. Each Docker host runs a piece of networking infrastructure that decapsulates incoming VXLAN packets and delivers them to the correct local container, and encapsulates outgoing packets destined for containers on remote hosts.
4. From the container's point of view, this is all transparent — it simply sees a normal virtual network interface and can resolve and reach other containers by name via Docker's embedded DNS, exactly as it would on a single-host bridge network.

### Creating an Overlay Network (for reference, requires Swarm mode)

```bash
# Initialize Swarm mode first (only needed once per manager node)
docker swarm init

# Create an overlay network
docker network create -d overlay my-overlay-net

# Deploy a service onto the overlay network
docker service create --name web --network my-overlay-net --replicas 3 nginx:alpine
```

### Key Takeaway

Bridge networks solve container-to-container communication on a **single host**; overlay networks solve the same problem across a **cluster of hosts**, making it possible to build and scale distributed applications while still letting containers address each other by simple service names.

---

## Summary

| Task | Concept Demonstrated |
| :--- | :--- |
| Task 1 | User-defined bridge networks, multi-network container attachment, and network-based isolation between tiers. |
| Task 2 | The `host` network driver — no NAT, container shares the host's network namespace directly. |
| Task 3 | Bind mounts — live, two-way sync between a host folder and a container's filesystem. |
| Task 4 | Overlay networks — cross-host container communication using VXLAN, typically paired with Docker Swarm. |
