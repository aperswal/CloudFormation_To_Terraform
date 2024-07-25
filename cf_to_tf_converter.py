import yaml
import json
import os
from typing import Dict, Any, List
from security_analyzer import analyze_security, generate_security_report, get_security_score

class CloudFormationLoader(yaml.SafeLoader):
    def __init__(self, stream):
        self._root = stream.name
        super(CloudFormationLoader, self).__init__(stream)

def construct_cfn_tag(loader, node):
    if isinstance(node, yaml.ScalarNode):
        return f"${{{node.value}}}"
    elif isinstance(node, yaml.SequenceNode):
        return [construct_cfn_tag(loader, item) for item in node.value]
    elif isinstance(node, yaml.MappingNode):
        return {construct_cfn_tag(loader, k): construct_cfn_tag(loader, v) for k, v in node.value}

for tag in ['!Ref', '!GetAtt', '!Sub', '!Join', '!Select', '!Split', '!FindInMap', '!If', '!Equals', '!And', '!Or', '!Not', '!ImportValue']:
    CloudFormationLoader.add_constructor(tag, construct_cfn_tag)

def load_cloudformation_template(file_path: str) -> Dict[str, Any]:
    with open(file_path, 'r') as f:
        if file_path.endswith('.json'):
            return json.load(f)
        else:
            return yaml.load(f, Loader=CloudFormationLoader)

def convert_resource_type(cf_type: str) -> str:
    type_mapping = {
        'AWS::S3::Bucket': 'aws_s3_bucket',
        'AWS::EC2::Instance': 'aws_instance',
        'AWS::IAM::Role': 'aws_iam_role',
        'AWS::Lambda::Function': 'aws_lambda_function',
        'AWS::DynamoDB::Table': 'aws_dynamodb_table',
        'AWS::RDS::DBInstance': 'aws_db_instance',
        'AWS::ElasticLoadBalancingV2::LoadBalancer': 'aws_lb',
        'AWS::ElasticLoadBalancingV2::TargetGroup': 'aws_lb_target_group',
        'AWS::ElasticLoadBalancingV2::Listener': 'aws_lb_listener',
        'AWS::EC2::SecurityGroup': 'aws_security_group',
        'AWS::EC2::VPC': 'aws_vpc',
        'AWS::EC2::Subnet': 'aws_subnet',
        'AWS::EC2::InternetGateway': 'aws_internet_gateway',
        'AWS::EC2::RouteTable': 'aws_route_table',
        'AWS::EC2::Route': 'aws_route',
        'AWS::EC2::EIP': 'aws_eip',
        'AWS::EC2::NatGateway': 'aws_nat_gateway',
        'AWS::IAM::Policy': 'aws_iam_policy',
        'AWS::CloudWatch::Alarm': 'aws_cloudwatch_metric_alarm',
        'AWS::SNS::Topic': 'aws_sns_topic',
        'AWS::SQS::Queue': 'aws_sqs_queue',
        'AWS::KMS::Key': 'aws_kms_key',
        # Add more mappings here
    }
    return type_mapping.get(cf_type, f"aws_{cf_type.lower().replace('::', '_')}")

def convert_property_name(name: str) -> str:
    name_mapping = {
        'BucketName': 'bucket',
        'AccessControl': 'acl',
        'VersioningConfiguration': 'versioning',
        'ServerSideEncryptionConfiguration': 'server_side_encryption_configuration',
        # Add more mappings here
    }
    converted = name_mapping.get(name, name)
    return converted.lower().replace('_', '')

def convert_property_value(value: Any, property_name: str) -> Any:
    if isinstance(value, dict):
        if 'Ref' in value:
            return f"${{var.{value['Ref']}}}"
        elif 'Fn::GetAtt' in value:
            attrs = value['Fn::GetAtt']
            if isinstance(attrs, list):
                return f"${{{convert_resource_type(attrs[0].split('::')[1].lower())}.{attrs[0].lower()}.{attrs[1].lower()}}}"
            else:
                parts = attrs.split('.')
                return f"${{{convert_resource_type(parts[0].split('::')[1].lower())}.{parts[0].lower()}.{parts[1].lower()}}}"
        elif 'Fn::Join' in value:
            delimiter, parts = value['Fn::Join']
            return f"${{join(\"{delimiter}\", {parts})}}"
        elif 'Fn::Sub' in value:
            return f"${{format(\"{value['Fn::Sub']}\", {{}})}}".replace("${", "$${")
        # Add more intrinsic function handlers here
    elif isinstance(value, list):
        if property_name == 'SecurityGroups':
            return [f"${{aws_security_group.{item.lower()}.id}}" for item in value]
        return [convert_property_value(item, property_name) for item in value]
    elif isinstance(value, str):
        return f'"{value}"'
    return value

def convert_resource(name: str, resource: Dict[str, Any]) -> List[str]:
    resource_type = convert_resource_type(resource['Type'])
    properties = resource.get('Properties', {})
    
    tf_resources = []

    if resource_type == 'aws_s3_bucket':
        tf_resources.append(f'resource "aws_s3_bucket" "{name}" {{')
        tf_resources.append(f'  bucket = {convert_property_value(properties.get("BucketName", name), "BucketName")}')
        tf_resources.append('}')

        if 'AccessControl' in properties:
            tf_resources.append(f'resource "aws_s3_bucket_acl" "{name}_acl" {{')
            tf_resources.append(f'  bucket = aws_s3_bucket.{name}.id')
            tf_resources.append(f'  acl    = {convert_property_value(properties["AccessControl"], "AccessControl")}')
            tf_resources.append('}')

        if 'VersioningConfiguration' in properties:
            tf_resources.append(f'resource "aws_s3_bucket_versioning" "{name}_versioning" {{')
            tf_resources.append(f'  bucket = aws_s3_bucket.{name}.id')
            tf_resources.append('  versioning_configuration {')
            tf_resources.append(f'    status = {convert_property_value(properties["VersioningConfiguration"]["Status"], "Status")}')
            tf_resources.append('  }')
            tf_resources.append('}')

        if 'ServerSideEncryptionConfiguration' in properties:
            tf_resources.append(f'resource "aws_s3_bucket_server_side_encryption_configuration" "{name}_encryption" {{')
            tf_resources.append(f'  bucket = aws_s3_bucket.{name}.id')
            tf_resources.append('  rule {')
            tf_resources.append('    apply_server_side_encryption_by_default {')
            tf_resources.append(f'      sse_algorithm = {convert_property_value(properties["ServerSideEncryptionConfiguration"][0]["ServerSideEncryptionByDefault"]["SSEAlgorithm"], "SSEAlgorithm")}')
            tf_resources.append('    }')
            tf_resources.append('  }')
            tf_resources.append('}')
    else:
        tf_resources.append(f'resource "{resource_type}" "{name}" {{')
        for prop_name, prop_value in properties.items():
            tf_name = convert_property_name(prop_name)
            tf_value = convert_property_value(prop_value, prop_name)
            tf_resources.append(f'  {tf_name} = {tf_value}')
        tf_resources.append('}')
    
    return tf_resources

def convert_output(name: str, output: Dict[str, Any]) -> str:
    value = convert_property_value(output.get('Value'), 'Output')
    description = output.get('Description', '')
    
    tf_output = [f'output "{name}" {{']
    if description:
        tf_output.append(f'  description = "{description}"')
    tf_output.append(f'  value       = {value}')
    tf_output.append('}')
    
    return '\n'.join(tf_output)

def convert_to_terraform(cf_template: Dict[str, Any]) -> str:
    tf_output = []
    
    if 'Parameters' in cf_template:
        tf_output.append("# Variables")
        for param_name, param_data in cf_template['Parameters'].items():
            default_value = param_data.get('Default', '')
            tf_output.append(f'variable "{param_name}" {{')
            if 'Description' in param_data:
                tf_output.append(f'  description = "{param_data["Description"]}"')
            tf_output.append(f'  type        = string')
            if default_value:
                tf_output.append(f'  default     = "{default_value}"')
            tf_output.append('}')
        tf_output.append("")

    if 'Resources' in cf_template:
        tf_output.append("# Resources")
        for resource_name, resource_data in cf_template['Resources'].items():
            tf_output.extend(convert_resource(resource_name, resource_data))
            tf_output.append("")

    if 'Outputs' in cf_template:
        tf_output.append("# Outputs")
        for output_name, output_data in cf_template['Outputs'].items():
            tf_output.append(convert_output(output_name, output_data))
            tf_output.append("")

    return '\n'.join(tf_output)

def process_cf_file(file_path: str) -> Dict[str, Any]:
    cf_template = load_cloudformation_template(file_path)
    tf_code = convert_to_terraform(cf_template)
    security_issues = analyze_security(tf_code)
    security_report = generate_security_report(tf_code)
    security_score = get_security_score(security_issues)
    
    return {
        "terraform_code": tf_code,
        "security_report": security_report,
        "security_score": security_score,
        "security_issues": security_issues
    }

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python cf_to_tf_converter.py <cloudformation_template_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    result = process_cf_file(input_file)
    print(result["terraform_code"])
    print("\nSecurity Report:")
    print(result["security_report"])
    print(f"\nSecurity Score: {result['security_score']}/100")