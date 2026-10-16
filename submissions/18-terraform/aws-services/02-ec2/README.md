# AWS EC2 (Elastic Compute Cloud)

**Name:** Srinidhi Narendran · **Roll No:** 24BCS10037

My notes on EC2. EC2 matters for my GearLoan project because the EKS worker nodes are EC2 instances under the hood.

---

## What is EC2

EC2 gives virtual servers in the cloud. AWS calls each server an **instance**.

- I choose the OS, CPU, memory, storage and network.
- I can start and stop instances any time.
- Billing depends on the instance type and how long it runs (per second for Linux in most cases).
- Instances live in a **subnet** inside a **VPC**, in one **Availability Zone**.

Ways to pay:

| Option | When to use |
|---|---|
| On-Demand | Default, no commitment, good for learning |
| Savings Plans / Reserved | Steady workloads for 1 or 3 years |
| Spot | Spare capacity, much cheaper, but AWS can take it back with 2 minutes notice |
| Dedicated Hosts | Licensing or compliance needs |

## AMI

An **AMI (Amazon Machine Image)** is the template used to launch an instance. It has the OS and any pre-installed software.

- AMIs are **regional**. An AMI ID in `ap-south-1` is different from the same image in `us-east-1`.
- Sources: AWS (Amazon Linux 2023, Ubuntu, Windows), AWS Marketplace, community, or my own custom AMI.
- I can make my own AMI from a running instance after setting it up.
- For EKS, AWS provides **EKS optimized AMIs** (Amazon Linux 2023 or Bottlerocket) for the worker nodes.

Finding the latest Amazon Linux 2023 AMI in Mumbai:

```bash
aws ssm get-parameter \
  --name /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 \
  --region ap-south-1 --query "Parameter.Value" --output text
```

## Instance types

The instance type sets the CPU, memory and network capacity. The name has a pattern:

```
m7g.large
| |\ \___ size (nano, micro, small, medium, large, xlarge, 2xlarge ...)
| | \____ extra feature (g = Graviton ARM, i = Intel, a = AMD, d = local NVMe disk)
| \______ generation
\________ family
```

| Family | Meant for | Example |
|---|---|---|
| T (burstable) | Small apps, dev, low steady CPU | `t3.micro`, `t4g.small` |
| M (general purpose) | Balanced CPU and memory | `m7i.large` |
| C (compute optimized) | CPU heavy work | `c7g.xlarge` |
| R (memory optimized) | Big caches, in-memory DBs | `r7g.large` |
| G / P (accelerated) | GPU, ML training | `g5.xlarge` |
| I (storage optimized) | High disk IO | `i4i.large` |

For GearLoan, I plan to use small general purpose or burstable nodes (like `t3.medium`) because it is a student project with low traffic.

## Key pairs

A key pair is used to log in to a Linux instance with SSH.

- AWS keeps the **public key**. I download the **private key** (`.pem`) only once.
- If I lose the private key, I cannot download it again.
- Key types: RSA and ED25519.
- Windows instances use the key to decrypt the admin password.

```bash
aws ec2 create-key-pair --key-name gearloan-key --key-type ed25519 \
  --query "KeyMaterial" --output text > gearloan-key.pem
chmod 400 gearloan-key.pem
ssh -i gearloan-key.pem ec2-user@<public-ip>
```

I also learned that **SSM Session Manager** can open a shell without SSH or open port 22. That is safer.

## Security Groups

A security group is a virtual firewall attached to an instance (to its network interface).

- Rules only **allow**. There are no deny rules.
- It is **stateful**: if inbound traffic is allowed, the reply is allowed out automatically.
- By default: all inbound blocked, all outbound allowed.
- A rule can point to another security group instead of an IP range.

Example for a web server:

| Direction | Protocol | Port | Source |
|---|---|---|---|
| Inbound | TCP | 443 | 0.0.0.0/0 |
| Inbound | TCP | 22 | my IP only (e.g. 203.0.113.10/32) |
| Outbound | All | All | 0.0.0.0/0 |

Mistake to avoid: opening port 22 to `0.0.0.0/0`.

## EBS

**EBS (Elastic Block Store)** is a network disk attached to an instance.

- An EBS volume lives in **one AZ** and attaches to an instance in the same AZ.
- Data stays even if the instance is stopped.
- The root volume is deleted on terminate by default (the "Delete on termination" flag).
- **Snapshots** back up a volume to S3 (managed by AWS). They are incremental.
- Volumes can be encrypted with KMS.

| Volume type | Kind | Notes |
|---|---|---|
| gp3 | SSD | Default choice, set IOPS and throughput separately |
| gp2 | SSD | Older, IOPS tied to size |
| io2 Block Express | SSD | High IOPS for big databases |
| st1 | HDD | Throughput, big sequential reads |
| sc1 | HDD | Cold data, lowest cost |

**Instance store** is different. It is a disk physically on the host. It is fast, but data is lost when the instance stops or terminates.

## Public vs private IP

| | Private IP | Public IP |
|---|---|---|
| Reachable from | Inside the VPC (and connected networks) | The internet |
| Given from | Subnet CIDR | AWS pool |
| On stop/start | Stays the same | Changes |
| Cost | Free | AWS charges for public IPv4 addresses |

- An **Elastic IP** is a fixed public IPv4 that I can keep and move between instances.
- An instance gets a public IP only if the subnet has "auto-assign public IP" on, or I request it at launch.
- The instance OS only sees its private IP. The Internet Gateway maps the public IP to it.

Since GearLoan uses 2 **public subnets**, the EKS nodes there need a public IP to reach the internet (to pull images), because there is no NAT Gateway.

## Instance lifecycle

```
pending --> running --> stopping --> stopped --> (start) --> pending
               |                        |
               +--> shutting-down --> terminated
               +--> rebooting --> running
```

| State | Billed for compute? |
|---|---|
| pending | No |
| running | Yes |
| stopping / stopped | No (but EBS and Elastic IPs still cost) |
| hibernate (stopping) | Yes while saving RAM to disk |
| terminated | No, the instance is gone |

Useful commands:

```bash
aws ec2 describe-instances --region ap-south-1 \
  --query "Reservations[].Instances[].[InstanceId,State.Name,InstanceType]" --output table
aws ec2 stop-instances --instance-ids i-0abc123example
```

Reboot keeps the same public IP. Stop and start usually moves the instance to new hardware and gives a new public IP.

## Common use cases

- Hosting web apps and APIs
- Worker nodes for Kubernetes (EKS managed node groups use EC2)
- Running CI/CD build agents (e.g. Jenkins agents)
- Batch jobs and data processing, often on Spot
- Self-managed databases when RDS does not fit
- Bastion hosts or dev machines
- GPU instances for machine learning

For GearLoan, I will not launch EC2 by hand. The EKS managed node group in Terraform will create the instances, but knowing AMIs, instance types, security groups and EBS helps me understand what it builds.
