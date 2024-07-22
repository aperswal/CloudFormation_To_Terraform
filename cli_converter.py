import os
import sys
import argparse
import zipfile
from cf_to_tf_converter import process_cf_file

def convert_files(input_path, output_dir):
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

def convert_single_file(file_path, output_dir):
    try:
        tf_output = process_cf_file(file_path)
        output_filename = os.path.splitext(os.path.basename(file_path))[0] + '.tf'
        output_path = os.path.join(output_dir, output_filename)
        with open(output_path, 'w') as f:
            f.write(tf_output)
        print(f"Converted {file_path} to {output_path}")
    except Exception as e:
        print(f"Error converting {file_path}: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Convert CloudFormation templates to Terraform')
    parser.add_argument('input', help='Input file or directory path')
    parser.add_argument('-o', '--output', default='converted_files', help='Output directory (default: converted_files)')
    args = parser.parse_args()

    input_path = os.path.abspath(args.input)
    output_dir = os.path.abspath(args.output)

    convert_files(input_path, output_dir)
    print(f"Conversion complete. Converted files are in {output_dir}")

if __name__ == '__main__':
    main()