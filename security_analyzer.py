import re
from typing import List, Dict, Any

def analyze_security(terraform_code: str) -> List[Dict[str, Any]]:
    issues = []

    # Check for hardcoded secrets
    secret_pattern = r'(password|secret|key)\s*=\s*"[^"]*"'
    for match in re.finditer(secret_pattern, terraform_code, re.IGNORECASE):
        issues.append({
            "severity": "High",
            "type": "Hardcoded Secret",
            "description": f"Potential hardcoded secret detected: {match.group(0)}",
            "line": terraform_code.count('\n', 0, match.start()) + 1
        })

    # Check for public S3 buckets
    if 'acl    = "public-read"' in terraform_code or 'acl    = "public-read-write"' in terraform_code:
        issues.append({
            "severity": "High",
            "type": "Public S3 Bucket",
            "description": "S3 bucket with public read or read-write access detected",
            "line": terraform_code.index('acl    = "public-read"') if 'acl    = "public-read"' in terraform_code else terraform_code.index('acl    = "public-read-write"')
        })

    # Check for unrestricted security group ingress
    if 'ingress {' in terraform_code and 'cidr_blocks      = ["0.0.0.0/0"]' in terraform_code:
        issues.append({
            "severity": "Medium",
            "type": "Unrestricted Ingress",
            "description": "Unrestricted security group ingress rule detected",
            "line": terraform_code.index('ingress {')
        })

    # Check for unencrypted resources
    if 'encrypted        = false' in terraform_code:
        issues.append({
            "severity": "Medium",
            "type": "Unencrypted Resource",
            "description": "Unencrypted resource detected",
            "line": terraform_code.index('encrypted        = false')
        })

    # Check for use of default VPC
    if 'vpc_id      = aws_default_vpc' in terraform_code:
        issues.append({
            "severity": "Low",
            "type": "Default VPC Usage",
            "description": "Usage of default VPC detected. Consider creating a custom VPC for better security",
            "line": terraform_code.index('vpc_id      = aws_default_vpc')
        })

    # Check for unencrypted S3 bucket
    if 'resource "aws_s3_bucket"' in terraform_code and 'server_side_encryption_configuration {' not in terraform_code:
        issues.append({
            "severity": "Medium",
            "type": "Unencrypted S3 Bucket",
            "description": "S3 bucket without server-side encryption detected",
            "line": terraform_code.index('resource "aws_s3_bucket"')
        })

    # Check for unrestricted outbound traffic
    if 'egress {' in terraform_code and 'cidr_blocks      = ["0.0.0.0/0"]' in terraform_code:
        issues.append({
            "severity": "Low",
            "type": "Unrestricted Egress",
            "description": "Unrestricted outbound traffic detected in security group",
            "line": terraform_code.index('egress {')
        })

    return issues

def generate_security_report(terraform_code: str) -> str:
    issues = analyze_security(terraform_code)
    
    if not issues:
        return "No security issues detected."
    
    report = "Security Analysis Report:\n\n"
    for issue in issues:
        report += f"[{issue['severity']}] {issue['type']} (Line {issue['line']}):\n"
        report += f"  {issue['description']}\n\n"
    
    return report

def get_security_score(issues: List[Dict[str, Any]]) -> int:
    severity_scores = {"High": 10, "Medium": 5, "Low": 2}
    total_score = 100 - sum(severity_scores[issue['severity']] for issue in issues)
    return max(0, total_score)  # Ensure score doesn't go below 0

if __name__ == "__main__":
    # For testing purposes
    test_code = """
    resource "aws_s3_bucket" "example" {
      bucket = "my-bucket"
      acl    = "public-read"
    }

    resource "aws_security_group" "example" {
      name        = "allow_all"
      description = "Allow all inbound traffic"
      
      ingress {
        from_port   = 0
        to_port     = 0
        protocol    = "-1"
        cidr_blocks = ["0.0.0.0/0"]
      }
    }

    resource "aws_db_instance" "example" {
      engine               = "mysql"
      instance_class       = "db.t3.micro"
      name                 = "mydb"
      username             = "foo"
      password             = "foobarbaz"
      skip_final_snapshot  = true
      encrypted            = false
    }
    """

    issues = analyze_security(test_code)
    report = generate_security_report(test_code)
    score = get_security_score(issues)

    print(report)
    print(f"Security Score: {score}/100")