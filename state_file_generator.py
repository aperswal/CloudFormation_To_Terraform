import boto3
import json
from botocore.exceptions import ClientError
from typing import List, Dict, Any

def generate_state_file(regions: List[str], resource_types: List[str]) -> str:
    state = {
        "version": 4,
        "terraform_version": "1.0.0",
        "serial": 1,
        "lineage": "",
        "outputs": {},
        "resources": []
    }

    for region in regions:
        session = boto3.Session(region_name=region)
        
        for resource_type in resource_types:
            try:
                resources = fetch_resources(session, resource_type)
                state['resources'].extend(resources)
            except Exception as e:
                print(f"Error fetching {resource_type} in {region}: {str(e)}")

    return json.dumps(state, indent=2)

def fetch_resources(session: boto3.Session, resource_type: str) -> List[Dict[str, Any]]:
    resources = []

    if resource_type == 'aws_s3_bucket':
        resources.extend(fetch_s3_buckets(session))
    elif resource_type == 'aws_ec2_instance':
        resources.extend(fetch_ec2_instances(session))
    elif resource_type == 'aws_vpc':
        resources.extend(fetch_vpcs(session))
    elif resource_type == 'aws_subnet':
        resources.extend(fetch_subnets(session))
    elif resource_type == 'aws_security_group':
        resources.extend(fetch_security_groups(session))
    # Add more resource types here as needed

    return resources

def fetch_s3_buckets(session: boto3.Session) -> List[Dict[str, Any]]:
    s3 = session.client('s3')
    resources = []
    try:
        response = s3.list_buckets()
        for bucket in response['Buckets']:
            resources.append({
                "mode": "managed",
                "type": "aws_s3_bucket",
                "name": bucket['Name'],
                "provider": f"provider[\"registry.terraform.io/hashicorp/aws\"]",
                "instances": [
                    {
                        "schema_version": 0,
                        "attributes": {
                            "bucket": bucket['Name'],
                            "arn": f"arn:aws:s3:::{bucket['Name']}",
                            "region": s3.get_bucket_location(Bucket=bucket['Name'])['LocationConstraint'] or 'us-east-1'
                        }
                    }
                ]
            })
    except ClientError as e:
        print(f"Error fetching S3 buckets: {e}")
    return resources

def fetch_ec2_instances(session: boto3.Session) -> List[Dict[str, Any]]:
    ec2 = session.resource('ec2')
    resources = []
    try:
        for instance in ec2.instances.all():
            resources.append({
                "mode": "managed",
                "type": "aws_instance",
                "name": instance.id,
                "provider": f"provider[\"registry.terraform.io/hashicorp/aws\"]",
                "instances": [
                    {
                        "schema_version": 1,
                        "attributes": {
                            "id": instance.id,
                            "instance_type": instance.instance_type,
                            "ami": instance.image_id,
                            "vpc_id": instance.vpc_id,
                            "subnet_id": instance.subnet_id,
                            "private_ip": instance.private_ip_address,
                            "public_ip": instance.public_ip_address,
                        }
                    }
                ]
            })
    except ClientError as e:
        print(f"Error fetching EC2 instances: {e}")
    return resources

def fetch_vpcs(session: boto3.Session) -> List[Dict[str, Any]]:
    ec2 = session.resource('ec2')
    resources = []
    try:
        for vpc in ec2.vpcs.all():
            resources.append({
                "mode": "managed",
                "type": "aws_vpc",
                "name": vpc.id,
                "provider": f"provider[\"registry.terraform.io/hashicorp/aws\"]",
                "instances": [
                    {
                        "schema_version": 1,
                        "attributes": {
                            "id": vpc.id,
                            "cidr_block": vpc.cidr_block,
                            "enable_dns_hostnames": vpc.describe_attribute(Attribute='enableDnsHostnames')['EnableDnsHostnames']['Value'],
                            "enable_dns_support": vpc.describe_attribute(Attribute='enableDnsSupport')['EnableDnsSupport']['Value'],
                        }
                    }
                ]
            })
    except ClientError as e:
        print(f"Error fetching VPCs: {e}")
    return resources

def fetch_subnets(session: boto3.Session) -> List[Dict[str, Any]]:
    ec2 = session.resource('ec2')
    resources = []
    try:
        for subnet in ec2.subnets.all():
            resources.append({
                "mode": "managed",
                "type": "aws_subnet",
                "name": subnet.id,
                "provider": f"provider[\"registry.terraform.io/hashicorp/aws\"]",
                "instances": [
                    {
                        "schema_version": 1,
                        "attributes": {
                            "id": subnet.id,
                            "vpc_id": subnet.vpc_id,
                            "cidr_block": subnet.cidr_block,
                            "availability_zone": subnet.availability_zone,
                            "map_public_ip_on_launch": subnet.map_public_ip_on_launch,
                        }
                    }
                ]
            })
    except ClientError as e:
        print(f"Error fetching subnets: {e}")
    return resources

def fetch_security_groups(session: boto3.Session) -> List[Dict[str, Any]]:
    ec2 = session.client('ec2')
    resources = []
    try:
        response = ec2.describe_security_groups()
        for sg in response['SecurityGroups']:
            resources.append({
                "mode": "managed",
                "type": "aws_security_group",
                "name": sg['GroupName'],
                "provider": f"provider[\"registry.terraform.io/hashicorp/aws\"]",
                "instances": [
                    {
                        "schema_version": 1,
                        "attributes": {
                            "id": sg['GroupId'],
                            "name": sg['GroupName'],
                            "description": sg['Description'],
                            "vpc_id": sg['VpcId'],
                            "ingress": [rule for rule in sg.get('IpPermissions', [])],
                            "egress": [rule for rule in sg.get('IpPermissionsEgress', [])]
                        }
                    }
                ]
            })
    except ClientError as e:
        print(f"Error fetching security groups: {e}")
    return resources

def save_state_file(state: str, filename: str):
    with open(filename, 'w') as f:
        f.write(state)

if __name__ == "__main__":
    regions = ["us-west-2", "us-east-1"]  # Add or modify regions as needed
    resource_types = ["aws_s3_bucket", "aws_ec2_instance", "aws_vpc", "aws_subnet", "aws_security_group"]
    state = generate_state_file(regions, resource_types)
    save_state_file(state, "terraform.tfstate")
    print("Terraform state file generated: terraform.tfstate")