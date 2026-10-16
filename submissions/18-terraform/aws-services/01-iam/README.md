# AWS IAM (Identity and Access Management)

**Name:** Srinidhi Narendran · **Roll No:** 24BCS10037

These are my notes on IAM. I read the AWS docs and tried a few commands in my own account. I also wrote down how IAM fits into my project, GearLoan, which will run on EKS in `ap-south-1` (Mumbai).

---

## What is IAM

IAM is the AWS service that decides **who** can do **what** on **which** resource.

- Authentication: who are you? (user, role, password, access key)
- Authorization: are you allowed to do this action?
- IAM is a **global** service. It is not tied to one region.
- IAM itself has no extra cost.

When I first create an AWS account I get a **root user**. The root user can do everything, including closing the account. I learned that I should not use it for daily work. I only use it for a few account-level tasks.

Every API call in AWS (from the console, CLI, Terraform or an app) goes through IAM. If no policy allows the action, it is denied by default.

## Users

An IAM user is one identity with long-term credentials.

| Credential | Used for |
|---|---|
| Password | Logging into the AWS console |
| Access key ID + secret key | CLI, SDK, Terraform |
| MFA device | Extra check at login |

Notes:
- One user should map to one person or one tool. Users should not share logins.
- For human logins, AWS now recommends **IAM Identity Center** (SSO) instead of making many IAM users. It gives short-term credentials.
- Access keys are long-lived, so they are risky if they leak (for example, pushed to GitHub).

Creating a user from the CLI:

```bash
aws iam create-user --user-name srinidhi-dev
aws iam list-users --query "Users[].UserName"
```

## Groups

A group is a collection of users. I attach policies to the group, and every user in it gets those permissions.

- Groups make it easy to manage many users at once.
- A user can be in more than one group.
- Groups cannot be nested (no group inside a group).
- A group is not an identity. You cannot log in as a group.

Example for a small team:

| Group | Members | Policy |
|---|---|---|
| `developers` | 3 students | Read EKS, push to ECR |
| `admins` | 1 lead | AdministratorAccess |
| `auditors` | faculty | ReadOnlyAccess |

```bash
aws iam create-group --group-name developers
aws iam add-user-to-group --group-name developers --user-name srinidhi-dev
```

## Roles

A role is an identity with permissions, but it has **no password or access keys**. Someone or something "assumes" the role and gets **temporary credentials** from AWS STS.

Who can assume a role:
- An AWS service (for example, EC2 or Lambda)
- A user in the same or another AWS account
- A user from an outside identity provider (SSO, GitHub Actions through OIDC)
- A Kubernetes pod on EKS

Each role has two parts:
1. **Trust policy**: who is allowed to assume it.
2. **Permission policy**: what the role can do after it is assumed.

For GearLoan on EKS:
- The EKS cluster needs a **cluster role**.
- The worker nodes need a **node role** (to pull images from ECR, join the cluster).
- The GearLoan backend pod needs access to an S3 bucket for equipment photos. I learned that I should give this through **EKS Pod Identity** or **IRSA** (IAM Roles for Service Accounts), not by putting access keys inside the container.

## Policies

A policy is a JSON document that lists permissions.

Types I came across:

| Type | Notes |
|---|---|
| AWS managed | Made by AWS, e.g. `ReadOnlyAccess` |
| Customer managed | I write it and can reuse it |
| Inline | Attached directly to one user/group/role only |
| Resource-based | Attached to a resource, e.g. an S3 bucket policy |
| Trust policy | Special resource policy on a role |

Parts of a policy statement:
- `Effect`: `Allow` or `Deny`
- `Action`: the API calls, like `s3:GetObject`
- `Resource`: the ARN the action applies to
- `Condition` (optional): extra rules, like source IP or MFA

## Permissions

How AWS decides if a request is allowed:

1. By default everything is **denied** (implicit deny).
2. If any policy has an **explicit Deny**, the request is denied. Deny always wins.
3. If there is an **Allow** and no Deny, the request is allowed.

There are also guardrails above normal policies, like **permission boundaries** and **Service Control Policies** (SCPs) in AWS Organizations. They set the maximum a user or account can do. They do not grant anything by themselves.

## Least privilege

Least privilege means giving only the permissions needed for the job, and nothing more.

Bad example (what I should avoid):

```json
{
  "Effect": "Allow",
  "Action": "s3:*",
  "Resource": "*"
}
```

Better example for the GearLoan backend. It can only read and write photos in one folder of one bucket:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "GearLoanPhotosReadWrite",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::gearloan-equipment-photos/uploads/*"
    },
    {
      "Sid": "ListOnlyUploadsPrefix",
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::gearloan-equipment-photos",
      "Condition": {
        "StringLike": { "s3:prefix": "uploads/*" }
      }
    }
  ]
}
```

What I noticed:
- No `s3:DeleteObject`, because the app does not need to delete photos.
- `ListBucket` is on the bucket ARN, but `GetObject`/`PutObject` are on the object ARN (`/*`). I got this wrong the first time.

Tools that help: **IAM Access Analyzer** can suggest a policy based on what a role actually used, and "last accessed" info shows unused permissions.

## IAM best practices

- Turn on **MFA** for the root user and lock away its credentials.
- Do not create access keys for the root user.
- Use **IAM Identity Center** for people and **roles** for apps and services.
- Prefer temporary credentials over long-term access keys.
- Follow least privilege. Start small and add permissions when needed.
- Use groups to assign permissions, not one user at a time.
- Rotate or delete old access keys. Remove unused users and roles.
- Never put keys in code, Docker images or Git. Use roles or Secrets Manager.
- Turn on **CloudTrail** so every API call is logged.
- Use conditions (MFA, source IP, tags) where it makes sense.

Quick check of who I am logged in as:

```bash
aws sts get-caller-identity
```

## Common use cases

| Use case | How IAM is used |
|---|---|
| Team members logging into the console | Identity Center or IAM users in groups, with MFA |
| EC2 app reading from S3 | Instance profile with an IAM role |
| Pod on EKS reading S3 or DynamoDB | EKS Pod Identity or IRSA |
| CI/CD (GitHub Actions) deploying to AWS | OIDC trust with a role, no stored keys |
| Terraform creating infra | A role or user with only the needed permissions |
| Access from another AWS account | Cross-account role with a trust policy |
| Auditor needs to look only | `ReadOnlyAccess` or `SecurityAudit` managed policy |

### What I will do for GearLoan

- Use an IAM user with MFA only for my own Terraform runs while learning.
- Create the EKS cluster role and node role with AWS managed policies for EKS.
- Give the backend pod its own role, scoped to the photos bucket and the GearLoan DynamoDB table.
- Keep CloudTrail on in `ap-south-1`.
