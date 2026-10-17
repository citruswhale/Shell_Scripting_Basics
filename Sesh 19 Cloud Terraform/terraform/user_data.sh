#!/bin/bash
set -euxo pipefail

dnf install -y nginx

# Get the instance id using IMDSv2 (token first, then the metadata call).
TOKEN=$(curl -sS -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 300")
INSTANCE_ID=$(curl -sS -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/instance-id)

cat > /usr/share/nginx/html/index.html <<HTML
<!doctype html>
<html>
  <head><meta charset="utf-8"><title>GearLoan infra demo</title></head>
  <body>
    <h1>GearLoan infra demo – Srinidhi Narendran 24BCS10037 – served from EC2 ${INSTANCE_ID}</h1>
  </body>
</html>
HTML

systemctl enable --now nginx
