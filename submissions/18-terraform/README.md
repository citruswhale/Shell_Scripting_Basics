# Session 18 – Terraform & Infrastructure as Code

**Name:** Srinidhi Narendran · **Roll No:** 24BCS10037 · **Batch:** B

## Task 1 – Terraform S3 demo → [`terraform-s3-demo/`](terraform-s3-demo/README.md)

I created a private, encrypted (SSE-S3), versioned S3 bucket with Terraform on my AWS account (`ap-south-1`). I ran **init → fmt → validate → plan → apply → show → output → destroy**, checked the bucket with the AWS CLI, showed versioning keeping old copies, and destroyed it all.

| Step | Result |
|---|---|
| `terraform plan` | `Plan: 7 to add, 0 to change, 0 to destroy.` |
| `terraform apply` | `Apply complete! Resources: 7 added` → bucket `srinidhi-24bcs10037-s18-daacd98e` |
| checks | versioning `Enabled`, `AES256`, all 4 public-access blocks `true`, file readable |
| `terraform destroy` | `Destroy complete! Resources: 7 destroyed.`, state empty, bucket `404 Not Found` |

Real output: [`outputs/terraform-s3-demo-run.txt`](outputs/terraform-s3-demo-run.txt)

## Task 2 – AWS services research → [`aws-services/`](aws-services/)

| Service | README |
|---|---|
| IAM – governance | [`01-iam`](aws-services/01-iam/README.md) |
| EC2 – compute | [`02-ec2`](aws-services/02-ec2/README.md) |
| S3 – storage | [`03-s3`](aws-services/03-s3/README.md) |
| VPC – networking | [`04-vpc`](aws-services/04-vpc/README.md) |
| DynamoDB & RDS – databases | [`05-dynamodb-rds`](aws-services/05-dynamodb-rds/README.md) |

## What I learned
- Terraform compares **desired state** (my `.tf` files) with **real state** (the state file + AWS) and only changes the difference.
- `plan` is safe: it never changes anything, so I always read it before `apply`.
- The state file is how Terraform knows what it owns. It must be kept safe and never committed.
- Changing things outside Terraform creates **drift**, and the next `plan` shows it (exit code 2).
