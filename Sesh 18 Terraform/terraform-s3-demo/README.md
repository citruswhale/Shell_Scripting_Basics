# Terraform S3 Demo

**Name:** Srinidhi Narendran · **Roll No:** 24BCS10037

Creates one **private, encrypted, versioned** S3 bucket with Terraform and uploads a small file into it. I ran the whole workflow on my AWS account (region `ap-south-1`, profile `devops-lab`) and then destroyed everything.

Full real output: [`../outputs/terraform-s3-demo-run.txt`](../outputs/terraform-s3-demo-run.txt)

## Files

| File | What's in it |
|---|---|
| [`provider.tf`](provider.tf) | `required_providers` (aws `~> 6.69`, random `~> 3.9`), the AWS provider with my region and default tags (`Project`, `Owner`, `ManagedBy`) |
| [`variables.tf`](variables.tf) | `aws_region`, `bucket_prefix`, `environment` |
| [`terraform.tfvars`](terraform.tfvars) | values for those variables, with **no secrets** (credentials come from my local AWS profile) |
| [`main.tf`](main.tf) | `random_id` suffix, the bucket, public access block, ownership controls, versioning, SSE-S3 encryption, one object |
| [`outputs.tf`](outputs.tf) | bucket name, ARN, region, versioning status, object key |
| `.terraform.lock.hcl` | exact provider versions, so every run uses the same ones |

## The workflow

```bash
export AWS_PROFILE=devops-lab
terraform init
terraform fmt
terraform validate
terraform plan -out=tfplan
terraform apply tfplan
terraform show
terraform output
terraform destroy
```

### init
Downloads the providers listed in the lock file.
```text
Initializing the backend...
Initializing provider plugins...
Terraform has been successfully initialized!
```
### fmt / validate
`fmt` rewrites files to the standard style (it had nothing to change). `validate` checks the syntax and references:
```text
fmt: nothing to change
Success! The configuration is valid.
```
### plan
Shows what will happen, without changing anything:
```text
  # aws_s3_bucket.demo will be created
  # aws_s3_bucket_ownership_controls.demo will be created
  # aws_s3_bucket_public_access_block.demo will be created
  # aws_s3_bucket_server_side_encryption_configuration.demo will be created
  # aws_s3_bucket_versioning.demo will be created
  # aws_s3_object.hello will be created
  # random_id.suffix will be created
Plan: 7 to add, 0 to change, 0 to destroy.
```
### apply
```text
Apply complete! Resources: 7 added, 0 changed, 0 destroyed.
```
### output
```text
bucket_arn = "arn:aws:s3:::srinidhi-24bcs10037-s18-daacd98e"
bucket_name = "srinidhi-24bcs10037-s18-daacd98e"
bucket_region = "ap-south-1"
demo_object_key = "demo/hello.txt"
versioning_status = "Enabled"
```
### show / state
`terraform show` prints every attribute of every resource from the state file (full output in the log). `terraform state list`:
```text
aws_s3_bucket.demo
aws_s3_bucket_ownership_controls.demo
aws_s3_bucket_public_access_block.demo
aws_s3_bucket_server_side_encryption_configuration.demo
aws_s3_bucket_versioning.demo
aws_s3_object.hello
random_id.suffix
```

### Checking the bucket with the AWS CLI
```text
$ aws s3api get-bucket-versioning --bucket srinidhi-24bcs10037-s18-daacd98e
{ "Status": "Enabled" }
$ aws s3api get-bucket-encryption ...
{ "ApplyServerSideEncryptionByDefault": { "SSEAlgorithm": "AES256" }, ... }
$ aws s3api get-public-access-block ...
{ "BlockPublicAcls": true, "IgnorePublicAcls": true, "BlockPublicPolicy": true, "RestrictPublicBuckets": true }
$ aws s3 cp s3://srinidhi-24bcs10037-s18-daacd98e/demo/hello.txt -
Hello from Terraform - Srinidhi Narendran 24BCS10037
```

### Versioning in action
I uploaded a new copy of the file **outside Terraform**. S3 kept both versions:
```text
| IsLatest |        LastModified         | Size  |             VersionId              |
|  True    |  2026-10-16T20:58:19+00:00  |  38   |  DgrVvCcOrYAYddZa02jOkfjRY1UdoDSF  |
|  False   |  2026-10-16T20:57:52+00:00  |  52   |  fH7jgxsZvWJea.cDNVQ220QGtL8E2m3_  |
```
Then `terraform plan -detailed-exitcode` noticed the drift and wanted to put my original content back:
```text
Plan: 0 to add, 1 to change, 0 to destroy.
plan exit code: 2          <- 2 means "there are changes"
```

### destroy
```text
aws_s3_object.hello: Destruction complete after 1s
...
aws_s3_bucket.demo: Destruction complete after 1s
random_id.suffix: Destruction complete after 0s
Destroy complete! Resources: 7 destroyed.

$ terraform state list | wc -l
       0
$ aws s3api head-bucket --bucket srinidhi-24bcs10037-s18-daacd98e
An error occurred (404) when calling the HeadBucket operation: Not Found
```
`force_destroy = true` lets Terraform delete the bucket even though it still held 2 object versions.

## Notes
- The bucket name needs to be unique across **all** AWS accounts, which is why there's a `random_id` suffix.
- `terraform.tfvars` is committed because the assignment asks for it. It only has the region, prefix and environment. A copy is also kept as `terraform.tfvars.example`.
- The state file (`terraform.tfstate`) and plan file (`tfplan`) are gitignored and never committed. State can contain sensitive values.
