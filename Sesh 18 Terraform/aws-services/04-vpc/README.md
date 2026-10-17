# AWS VPC (Virtual Private Cloud)

**Name:** Srinidhi Narendran · **Roll No:** 24BCS10037

My notes on VPC networking. This is the part I need most for Terraform, because the GearLoan EKS cluster in `ap-south-1` will sit inside a VPC with 2 public subnets.

---

## What is VPC

A VPC is my own private network inside AWS. I control the IP range, the subnets, the routing and the firewalls.

- A VPC belongs to **one region**, but it spans all AZs in that region.
- Every account has a **default VPC** in each region. For projects I make my own.
- Resources like EC2, EKS nodes, RDS and load balancers run inside a VPC.
- VPCs are isolated from each other unless I connect them (peering, Transit Gateway).

Main building blocks:

| Part | What it does |
|---|---|
| CIDR block | IP range of the VPC |
| Subnet | A slice of the range in one AZ |
| Route table | Where traffic goes |
| Internet Gateway | Door to the internet |
| NAT Gateway | Lets private subnets go out to the internet |
| Security Group | Firewall on the instance |
| Network ACL | Firewall on the subnet |

## CIDR

CIDR notation describes an IP range: `IP/prefix`. The prefix says how many bits are fixed. The rest are for hosts.

- VPC size can be from `/16` (65,536 IPs) to `/28` (16 IPs).
- Use private ranges (RFC 1918): `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`.
- Plan the range so it does not overlap with other networks I may connect later.

Breakdown for GearLoan:

```
VPC              10.0.0.0/16   -> 10.0.0.0 to 10.0.255.255   (65,536 IPs)
 |
 +-- public-a    10.0.1.0/24   -> 10.0.1.0 to 10.0.1.255     (256 IPs, ap-south-1a)
 +-- public-b    10.0.2.0/24   -> 10.0.2.0 to 10.0.2.255     (256 IPs, ap-south-1b)
 +-- (free for later private subnets: 10.0.11.0/24, 10.0.12.0/24 ...)
```

Quick math: a `/24` has 32 - 24 = 8 host bits, so 2^8 = 256 addresses.

| Prefix | Total IPs | Usable in AWS subnet |
|---|---|---|
| /16 | 65,536 | 65,531 |
| /20 | 4,096 | 4,091 |
| /24 | 256 | 251 |
| /28 | 16 | 11 |

## Subnets

A subnet is a range of IPs inside the VPC, and it lives in **exactly one AZ**.

AWS reserves **5 IPs** in every subnet. For `10.0.1.0/24`:

| IP | Reserved for |
|---|---|
| 10.0.1.0 | Network address |
| 10.0.1.1 | VPC router |
| 10.0.1.2 | DNS (Amazon provided) |
| 10.0.1.3 | Future use |
| 10.0.1.255 | Broadcast (not supported, still reserved) |

- To be highly available, I put subnets in at least 2 AZs.
- EKS needs subnets in **at least two AZs**, which is why GearLoan has `public-a` and `public-b`.
- For EKS to create internet-facing load balancers, public subnets are tagged `kubernetes.io/role/elb = 1`.

```bash
aws ec2 create-subnet --vpc-id vpc-0abc123example \
  --cidr-block 10.0.1.0/24 --availability-zone ap-south-1a
```

## Route tables

A route table is a list of rules that decide where network traffic goes.

- Each subnet is linked to one route table. If not linked, it uses the VPC's **main** route table.
- Every route table has a `local` route for the VPC CIDR. It cannot be removed.
- The most specific route (longest prefix) wins.

Public route table for GearLoan:

| Destination | Target |
|---|---|
| 10.0.0.0/16 | local |
| 0.0.0.0/0 | igw-0abc123example |

A private route table would point `0.0.0.0/0` to a NAT Gateway instead.

## Internet Gateway

An Internet Gateway (IGW) connects the VPC to the internet.

- One IGW per VPC. It is managed by AWS and scales on its own.
- It does not cost anything by itself (data transfer and public IPv4 addresses are charged).
- It does NAT between an instance's private IP and its public IP.

For an instance to reach the internet through the IGW it needs all three:
1. The IGW attached to the VPC.
2. A route `0.0.0.0/0 -> igw` in the subnet's route table.
3. A public IP or Elastic IP on the instance.

## NAT Gateway

A NAT Gateway lets instances in a **private** subnet start connections to the internet (for updates, pulling images), but the internet cannot start a connection to them.

- A public NAT Gateway is placed in a **public subnet** and uses an Elastic IP.
- The private subnet's route table sends `0.0.0.0/0` to the NAT Gateway.
- For high availability, one NAT Gateway per AZ.
- Cost: NAT Gateway is charged per hour plus per GB of data processed. It is one of the costs students often forget to delete.

For GearLoan I am **not** using a NAT Gateway, to keep the cost low. The nodes run in public subnets with public IPs. For a real production setup I would put the nodes in private subnets behind NAT.

## Security Groups

Security groups are stateful firewalls attached to network interfaces (EC2, EKS nodes, RDS, load balancers).

- Only allow rules.
- Stateful: return traffic is allowed automatically.
- All rules are checked together.
- Can reference another security group, e.g. "allow 5432 from the app SG".

Example: RDS allows PostgreSQL only from the EKS node security group.

| Inbound | Port | Source |
|---|---|---|
| TCP | 5432 | sg-eks-nodes |

## Network ACLs

A Network ACL (NACL) is a firewall at the **subnet** level.

- Has both **allow** and **deny** rules.
- **Stateless**: I must allow return traffic separately (ephemeral ports 1024-65535).
- Rules are checked in order by rule number, lowest first. The first match wins.
- The default NACL allows all traffic in and out. A new custom NACL denies everything until I add rules.

| | Security Group | Network ACL |
|---|---|---|
| Level | Instance (ENI) | Subnet |
| Rules | Allow only | Allow and deny |
| State | Stateful | Stateless |
| Order | All rules evaluated | Numbered, first match |
| Typical use | Main firewall | Extra layer, block bad IPs |

## Public vs private subnet

The only real difference is the route table.

| | Public subnet | Private subnet |
|---|---|---|
| Route to 0.0.0.0/0 | Internet Gateway | NAT Gateway (or none) |
| Instances get public IP | Usually yes (auto-assign) | No |
| Reachable from internet | Yes, if SG allows | No |
| Typical resources | Load balancers, bastion, NAT GW | App servers, databases, EKS nodes in production |

GearLoan layout summary:

```
Region ap-south-1
 VPC 10.0.0.0/16
  IGW attached
  public-a 10.0.1.0/24 (ap-south-1a) -> public route table -> IGW
  public-b 10.0.2.0/24 (ap-south-1b) -> public route table -> IGW
  EKS nodes + load balancer in both subnets
```

I will build all of this with Terraform, so I can destroy it after each lab and avoid charges.
