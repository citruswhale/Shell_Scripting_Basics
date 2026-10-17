output "public_ip" {
  description = "Public IP of the web server"
  value       = aws_instance.web.public_ip
}

output "website_url" {
  description = "URL of the nginx page"
  value       = "http://${aws_instance.web.public_ip}"
}

output "instance_id" {
  description = "EC2 instance id"
  value       = aws_instance.web.id
}

output "vpc_id" {
  description = "VPC id"
  value       = aws_vpc.main.id
}

output "subnet_id" {
  description = "Public subnet id"
  value       = aws_subnet.public.id
}

output "bucket_name" {
  description = "App assets bucket name"
  value       = aws_s3_bucket.assets.bucket
}

output "security_group_id" {
  description = "Web security group id"
  value       = aws_security_group.web.id
}
