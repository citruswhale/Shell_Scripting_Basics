# AWS S3 (Simple Storage Service)

**Name:** Srinidhi Narendran · **Roll No:** 24BCS10037

My study notes on S3. In GearLoan I want to use S3 for equipment photos and for the Terraform state file.

---

## What is S3

S3 is object storage. I can store any file (called an **object**) inside a container (called a **bucket**) and get it back over HTTPS.

- It is not a file system and not a disk. There are no real folders.
- Storage is practically unlimited. I pay for what I store, requests and data transfer out.
- AWS designs S3 for 99.999999999% (11 nines) durability for most storage classes.
- S3 has **strong read-after-write consistency**. After a successful write, the next read gets the new data.
- Data is stored in a region I pick, like `ap-south-1`.

## Buckets

A bucket is the top-level container for objects.

- Bucket names are **globally unique** across all AWS accounts.
- Name rules: 3 to 63 characters, lowercase letters, numbers, hyphens and dots.
- A bucket is created in one region.
- New buckets have **Block Public Access** turned on and ACLs disabled by default.

```bash
aws s3 mb s3://gearloan-equipment-photos --region ap-south-1
aws s3 ls
```

Bucket names I plan for GearLoan:

| Bucket | Purpose |
|---|---|
| `gearloan-equipment-photos` | Photos uploaded for each item |
| `gearloan-tfstate-24bcs10037` | Terraform remote state |

## Objects

An object is a file plus its metadata.

| Part | Example |
|---|---|
| Key | `uploads/item-1042/front.jpg` |
| Value | The file bytes |
| Metadata | `Content-Type: image/jpeg` |
| Version ID | Only if versioning is on |
| Tags | `project=gearloan` |

- The key is the full "path". The `/` only looks like folders in the console.
- For big files I should use **multipart upload**. The `aws s3 cp` command does this automatically for large files.

```bash
aws s3 cp front.jpg s3://gearloan-equipment-photos/uploads/item-1042/front.jpg
aws s3 ls s3://gearloan-equipment-photos/uploads/ --recursive
```

## Storage classes

Different classes trade storage cost for access cost and speed.

| Class | Good for | Notes |
|---|---|---|
| S3 Standard | Frequently used data | Default |
| S3 Intelligent-Tiering | Unknown or changing access | Moves data between tiers automatically |
| S3 Standard-IA | Rarely used, but needs fast access | Retrieval fee, min storage time |
| S3 One Zone-IA | Re-creatable, rarely used data | Only one AZ |
| S3 Express One Zone | Very low latency, high request rate | Uses directory buckets in one AZ |
| S3 Glacier Instant Retrieval | Archive, read in milliseconds | Around once a quarter |
| S3 Glacier Flexible Retrieval | Archive, minutes to hours to restore | Backups |
| S3 Glacier Deep Archive | Long-term archive, hours to restore | Lowest storage cost |

The cheaper the storage, the more I pay to read it back, and some classes have a minimum storage duration.

## Versioning

Versioning keeps every version of an object in the bucket.

- States: unversioned (default), enabled, suspended. Once enabled, it cannot go back to unversioned, only suspended.
- Deleting an object adds a **delete marker**. The old versions are still there and can be restored.
- It protects against accidental overwrite or delete.
- Old versions still cost storage, so I should pair it with a lifecycle rule.

```bash
aws s3api put-bucket-versioning --bucket gearloan-tfstate-24bcs10037 \
  --versioning-configuration Status=Enabled
```

Versioning is a must for the Terraform state bucket. If the state file gets corrupted, I can go back to an older version.

## Lifecycle policies

Lifecycle rules move or delete objects automatically based on age.

Two kinds of actions:
- **Transition**: move to a cheaper class after some days.
- **Expiration**: delete after some days.

Example idea for GearLoan photos:

| Age | Action |
|---|---|
| 0 days | Upload to Standard |
| 90 days | Move to Standard-IA |
| 365 days | Move to Glacier Flexible Retrieval |
| Old versions after 30 days | Delete |
| Incomplete multipart uploads after 7 days | Abort |

```json
{
  "Rules": [
    {
      "ID": "photos-tiering",
      "Status": "Enabled",
      "Filter": { "Prefix": "uploads/" },
      "Transitions": [
        { "Days": 90, "StorageClass": "STANDARD_IA" },
        { "Days": 365, "StorageClass": "GLACIER" }
      ],
      "NoncurrentVersionExpiration": { "NoncurrentDays": 30 },
      "AbortIncompleteMultipartUpload": { "DaysAfterInitiation": 7 }
    }
  ]
}
```

## Encryption

**In transit:** use HTTPS (TLS). A bucket policy can deny any request that is not over HTTPS.

**At rest:** since January 2023 every new object is encrypted by default with SSE-S3.

| Option | Key managed by | Notes |
|---|---|---|
| SSE-S3 | AWS (S3) | Default, no setup |
| SSE-KMS | AWS KMS key | Audit key use in CloudTrail, control who can decrypt |
| DSSE-KMS | AWS KMS key | Two layers of encryption |
| SSE-C | Me (I send the key) | AWS does not store the key |
| Client-side | Me | I encrypt before upload |

With SSE-KMS, turning on **S3 Bucket Keys** cuts down the number of KMS calls.

## Bucket policies

A bucket policy is a resource-based JSON policy attached to a bucket. It controls who can access the bucket and its objects, including other accounts.

Example: deny any request that is not using HTTPS.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyInsecureTransport",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::gearloan-equipment-photos",
        "arn:aws:s3:::gearloan-equipment-photos/*"
      ],
      "Condition": { "Bool": { "aws:SecureTransport": "false" } }
    }
  ]
}
```

Things I learned:
- Access works if the IAM policy **or** the bucket policy allows it (same account), and nothing denies it.
- Block Public Access overrides any policy that tries to make the bucket public.
- To show photos to users without making the bucket public, I can use **presigned URLs** or CloudFront.

## Common use cases

- Storing user uploads (images, documents)
- Hosting a static website (often with CloudFront in front)
- Backups and archives
- Terraform remote state (with versioning; newer Terraform versions can lock state with S3 directly using `use_lockfile`)
- Log storage (ALB logs, CloudTrail logs)
- Data lake for analytics (Athena can query files in S3)
- Storing build artifacts from CI/CD

For GearLoan, the backend pod on EKS will upload photos to `gearloan-equipment-photos` using a least-privilege IAM role, and the frontend will show them with short-lived presigned URLs.
