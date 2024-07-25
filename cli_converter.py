import os
import sys
import argparse
import zipfile
from cf_to_tf_converter import process_cf_file
from docs_generator import generate_docs, save_docs
from state_file_generator import generate_state_file
from diff_tool import generate_diff_report

def convert_files(input_path, output_dir, regions):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if os.path.isfile(input_path):
        if input_path.endswith('.zip'):
            with zipfile.ZipFile(input_path, 'r') as zip_ref:
                zip_ref.extractall(output_dir)
            for root, _, files in os.walk(output_dir):
                for file in files:
                    if file.endswith(('.yaml', '.yml', '.json')):
                        file_path = os.path.join(root, file)
                        convert_single_file(file_path, output_dir)
        else:
            convert_single_file(input_path, output_dir)
    elif os.path.isdir(input_path):
        for root, _, files in os.walk(input_path):
            for file in files:
                if file.endswith(('.yaml', '.yml', '.json')):
                    file_path = os.path.join(root, file)
                    convert_single_file(file_path, output_dir)
    else:
        print(f"Error: {input_path} is not a valid file or directory")
        sys.exit(1)

    # Generate state file
    resource_types = ["aws_s3_bucket", "aws_ec2_instance", "aws_vpc", "aws_subnet", "aws_security_group"]
    state_file = generate_state_file(regions, resource_types)
    state_file_path = os.path.join(output_dir, 'terraform.tfstate')
    with open(state_file_path, 'w') as f:
        f.write(state_file)
    print(f"State file generated: {state_file_path}")

def convert_single_file(file_path, output_dir):
    try:
        result = process_cf_file(file_path)
        tf_output = result["terraform_code"]
        security_report = result["security_report"]
        security_score = result["security_score"]
        security_issues = result["security_issues"]

        output_filename = os.path.splitext(os.path.basename(file_path))[0]
        tf_output_path = os.path.join(output_dir, f"{output_filename}.tf")
        report_output_path = os.path.join(output_dir, f"{output_filename}_security_report.txt")
        docs_output_path = os.path.join(output_dir, f"{output_filename}_docs.md")
        diff_output_path = os.path.join(output_dir, f"{output_filename}_diff.txt")

        with open(tf_output_path, 'w') as f:
            f.write(tf_output)
        with open(report_output_path, 'w') as f:
            f.write(f"Security Score: {security_score}/100\n\n")
            f.write(security_report)

        # Generate and save documentation
        docs = generate_docs(tf_output, security_issues)
        save_docs(docs, docs_output_path)

        # Generate diff report
        with open(file_path, 'r') as cf_file, open(tf_output_path, 'r') as tf_file:
            diff_report = generate_diff_report(cf_file.read(), tf_file.read())
        with open(diff_output_path, 'w') as f:
            f.write(diff_report)

        print(f"Converted {file_path} to {tf_output_path}")
        print(f"Security report saved to {report_output_path}")
        print(f"Documentation saved to {docs_output_path}")
        print(f"Diff report saved to {diff_output_path}")
        print(f"Security Score: {security_score}/100")
    except Exception as e:
        print(f"Error converting {file_path}: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Convert CloudFormation templates to Terraform')
    parser.add_argument('input', help='Input file or directory path')
    parser.add_argument('-o', '--output', default='converted_files', help='Output directory (default: converted_files)')
    parser.add_argument('-r', '--regions', nargs='+', default=['us-west-2'], help='AWS regions for state file generation (default: us-west-2)')
    args = parser.parse_args()

    input_path = os.path.abspath(args.input)
    output_dir = os.path.abspath(args.output)

    convert_files(input_path, output_dir, args.regions)
    print(f"Conversion complete. Converted files are in {output_dir}")

if __name__ == '__main__':
    main()