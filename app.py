import os
import time
import uuid
from flask import Flask, request, render_template, send_file, jsonify
from werkzeug.utils import secure_filename
import tempfile
import shutil
import zipfile
import io
from cf_to_tf_converter import process_cf_file
from docs_generator import generate_docs, save_docs
from state_file_generator import generate_state_file
from diff_tool import generate_diff_report


app = Flask(__name__)

ALLOWED_EXTENSIONS = {'yaml', 'yml', 'json', 'zip'}
TEMP_DIR = os.path.join(tempfile.gettempdir(), 'cf2tf_converter')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert_files():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    files = request.files.getlist('file')
    if not files or files[0].filename == '':
        return jsonify({'error': 'No selected file'}), 400

    conversion_id = str(uuid.uuid4())
    conversion_dir = os.path.join(TEMP_DIR, conversion_id)
    input_dir = os.path.join(conversion_dir, 'input')
    output_dir = os.path.join(conversion_dir, 'output')
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    try:
        results = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(input_dir, filename)
                file.save(file_path)

                if filename.endswith('.zip'):
                    with zipfile.ZipFile(file_path, 'r') as zip_ref:
                        zip_ref.extractall(input_dir)
                    os.remove(file_path)
                else:
                    result = process_cf_file(file_path)
                    results.append(result)
                    
                    # Generate and save documentation
                    docs = generate_docs(result["terraform_code"], result["security_issues"])
                    docs_filename = os.path.splitext(filename)[0] + '_docs.md'
                    docs_path = os.path.join(output_dir, docs_filename)
                    save_docs(docs, docs_path)
                    
                    # Save Terraform code
                    tf_filename = os.path.splitext(filename)[0] + '.tf'
                    tf_path = os.path.join(output_dir, tf_filename)
                    with open(tf_path, 'w') as f:
                        f.write(result["terraform_code"])
                    
                    # Generate diff report
                    with open(file_path, 'r') as cf_file, open(tf_path, 'r') as tf_file:
                        diff_report = generate_diff_report(cf_file.read(), tf_file.read())
                    diff_filename = os.path.splitext(filename)[0] + '_diff.txt'
                    diff_path = os.path.join(output_dir, diff_filename)
                    with open(diff_path, 'w') as f:
                        f.write(diff_report)

        # Process any extracted files from zip
        for root, _, files in os.walk(input_dir):
            for file in files:
                if allowed_file(file):
                    file_path = os.path.join(root, file)
                    result = process_cf_file(file_path)
                    results.append(result)
                    
                    # Generate and save documentation
                    docs = generate_docs(result["terraform_code"], result["security_issues"])
                    docs_filename = os.path.splitext(file)[0] + '_docs.md'
                    docs_path = os.path.join(output_dir, docs_filename)
                    save_docs(docs, docs_path)
                    
                    # Save Terraform code
                    tf_filename = os.path.splitext(file)[0] + '.tf'
                    tf_path = os.path.join(output_dir, tf_filename)
                    with open(tf_path, 'w') as f:
                        f.write(result["terraform_code"])
                    
                    # Generate diff report
                    with open(file_path, 'r') as cf_file, open(tf_path, 'r') as tf_file:
                        diff_report = generate_diff_report(cf_file.read(), tf_file.read())
                    diff_filename = os.path.splitext(file)[0] + '_diff.txt'
                    diff_path = os.path.join(output_dir, diff_filename)
                    with open(diff_path, 'w') as f:
                        f.write(diff_report)

        # Generate state file
        regions = ["us-west-2", "us-east-1"]  # You might want to make this configurable
        resource_types = ["aws_s3_bucket", "aws_ec2_instance", "aws_vpc", "aws_subnet", "aws_security_group"]
        state_file = generate_state_file(regions, resource_types)
        state_file_path = os.path.join(output_dir, 'terraform.tfstate')
        with open(state_file_path, 'w') as f:
            f.write(state_file)

        # Create a zip file of all converted files
        zip_filename = f'converted_files_{conversion_id}.zip'
        zip_path = os.path.join(conversion_dir, zip_filename)
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for root, _, files in os.walk(output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, output_dir)
                    zipf.write(file_path, arcname)

        return jsonify({
            "results": results,
            "download_url": f"/download_converted_files/{conversion_id}"
        })

    except Exception as e:
        return jsonify({'error': f'Conversion failed: {str(e)}'}), 500
    finally:
        # Don't remove temp_dir here, as we need it for the download
        pass

@app.route('/download_converted_files/<conversion_id>', methods=['GET'])
def download_converted_files(conversion_id):
    conversion_dir = os.path.join(TEMP_DIR, conversion_id)
    zip_filename = f'converted_files_{conversion_id}.zip'
    zip_path = os.path.join(conversion_dir, zip_filename)
    
    if not os.path.exists(zip_path):
        return jsonify({'error': 'Converted files not found'}), 404

    return send_file(zip_path, as_attachment=True, download_name=zip_filename)

def safe_remove(path):
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.isfile(path):
            os.remove(path)
    except Exception as e:
        app.logger.error(f"Error removing {path}: {str(e)}")

@app.teardown_appcontext
def cleanup_temp_files(error):
    if os.path.exists(TEMP_DIR):
        for d in os.listdir(TEMP_DIR):
            path = os.path.join(TEMP_DIR, d)
            try:
                if os.path.isdir(path) and (time.time() - os.path.getmtime(path)) > 3600:
                    safe_remove(path)
            except Exception as e:
                app.logger.error(f"Error cleaning up {path}: {str(e)}")

if __name__ == '__main__':
    os.makedirs(TEMP_DIR, exist_ok=True)
    app.run(debug=True)