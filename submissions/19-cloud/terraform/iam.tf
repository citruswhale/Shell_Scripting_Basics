# Role the EC2 instance assumes.
data "aws_iam_policy_document" "ec2_assume" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "web" {
  name               = "${var.project_name}-web-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume.json
}

# Least privilege: list and read only the assets bucket, nothing else.
data "aws_iam_policy_document" "read_assets" {
  statement {
    sid       = "ListAssetsBucket"
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.assets.arn]
  }

  statement {
    sid       = "ReadAssetsObjects"
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.assets.arn}/*"]
  }
}

resource "aws_iam_role_policy" "read_assets" {
  name   = "read-assets-bucket"
  role   = aws_iam_role.web.id
  policy = data.aws_iam_policy_document.read_assets.json
}

resource "aws_iam_instance_profile" "web" {
  name = "${var.project_name}-web-profile"
  role = aws_iam_role.web.name
}
