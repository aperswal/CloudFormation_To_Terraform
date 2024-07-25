import re
from typing import List, Dict, Any

def generate_docs(terraform_code: str, security_issues: List[Dict[str, Any]]) -> str:
    """Generate documentation for the converted Terraform code."""
    docs = ["# Terraform Configuration Documentation\n"]
    
    # Add a section for resources
    docs.append("## Resources\n")
    resources = parse_resources(terraform_code)
    for resource_type, resource_names in resources.items():
        docs.append(f"### {resource_type}\n")
        for name in resource_names:
            docs.append(f"- {name}\n")
        docs.append("\n")
    
    # Add a section for variables
    variables = parse_variables(terraform_code)
    if variables:
        docs.append("## Variables\n")
        for var_name, var_details in variables.items():
            docs.append(f"### {var_name}\n")
            if 'description' in var_details:
                docs.append(f"Description: {var_details['description']}\n")
            if 'type' in var_details:
                docs.append(f"Type: {var_details['type']}\n")
            if 'default' in var_details:
                docs.append(f"Default: {var_details['default']}\n")
            docs.append("\n")

    # Add a section for outputs
    outputs = parse_outputs(terraform_code)
    if outputs:
        docs.append("## Outputs\n")
        for output_name, output_details in outputs.items():
            docs.append(f"### {output_name}\n")
            if 'description' in output_details:
                docs.append(f"Description: {output_details['description']}\n")
            docs.append(f"Value: {output_details['value']}\n\n")

    # Add a section for security analysis
    docs.append("## Security Analysis\n")
    if security_issues:
        for issue in security_issues:
            docs.append(f"- **{issue['type']}** (Severity: {issue['severity']})\n")
            docs.append(f"  - Description: {issue['description']}\n")
            docs.append(f"  - Line: {issue['line']}\n")
            docs.append("\n")
    else:
        docs.append("No security issues detected.\n")
    
    return "\n".join(docs)

def parse_resources(terraform_code: str) -> Dict[str, List[str]]:
    """Parse the Terraform code to extract resource types and names."""
    resources = {}
    resource_pattern = r'resource\s+"(\w+)"\s+"(\w+)"\s+{'
    for match in re.finditer(resource_pattern, terraform_code):
        resource_type, resource_name = match.groups()
        if resource_type not in resources:
            resources[resource_type] = []
        resources[resource_type].append(resource_name)
    return resources

def parse_variables(terraform_code: str) -> Dict[str, Dict[str, str]]:
    """Parse the Terraform code to extract variables."""
    variables = {}
    variable_pattern = r'variable\s+"(\w+)"\s+{([^}]*)}'
    for match in re.finditer(variable_pattern, terraform_code, re.DOTALL):
        var_name, var_block = match.groups()
        variables[var_name] = {}
        if 'description' in var_block:
            variables[var_name]['description'] = re.search(r'description\s*=\s*"([^"]*)"', var_block).group(1)
        if 'type' in var_block:
            variables[var_name]['type'] = re.search(r'type\s*=\s*(\w+)', var_block).group(1)
        if 'default' in var_block:
            variables[var_name]['default'] = re.search(r'default\s*=\s*([^\n]+)', var_block).group(1)
    return variables

def parse_outputs(terraform_code: str) -> Dict[str, Dict[str, str]]:
    """Parse the Terraform code to extract outputs."""
    outputs = {}
    output_pattern = r'output\s+"(\w+)"\s+{([^}]*)}'
    for match in re.finditer(output_pattern, terraform_code, re.DOTALL):
        output_name, output_block = match.groups()
        outputs[output_name] = {}
        if 'description' in output_block:
            outputs[output_name]['description'] = re.search(r'description\s*=\s*"([^"]*)"', output_block).group(1)
        if 'value' in output_block:
            outputs[output_name]['value'] = re.search(r'value\s*=\s*([^\n]+)', output_block).group(1)
    return outputs

def save_docs(docs: str, output_path: str):
    """Save the generated documentation to a file."""
    with open(output_path, 'w') as f:
        f.write(docs)

if __name__ == "__main__":
    # For testing purposes
    test_code = """
    variable "example_var" {
      description = "An example variable"
      type        = string
      default     = "example"
    }

    resource "aws_s3_bucket" "example" {
      bucket = "my-bucket"
      acl    = "private"
    }

    output "bucket_name" {
      description = "The name of the S3 bucket"
      value       = aws_s3_bucket.example.id
    }
    """

    test_security_issues = [
        {
            "severity": "Low",
            "type": "Example Issue",
            "description": "This is an example security issue",
            "line": 5
        }
    ]

    docs = generate_docs(test_code, test_security_issues)
    print(docs)