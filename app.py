import os
from flask import Flask, request, render_template, send_file, jsonify
from werkzeug.utils import secure_filename
import tempfile
import shutil
import zipfile
import io
from cf_to_tf_converter import process_cf_file

app = Flask(__name__)

ALLOWED_EXTENSIONS = {'yaml', 'yml', 'json', 'zip'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_and_save(file_path, output_dir):
    filename = os.path.basename(file_path)
    tf_output = process_cf_file(file_path)
    output_filename = os.path.splitext(filename)[0] + '.tf'
    output_path = os.path.join(output_dir, output_filename)
    with open(output_path, 'w') as f:
        f.write(tf_output)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert_files():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    # Create a temporary directory for this request
    temp_dir = tempfile.mkdtemp()
    input_dir = os.path.join(temp_dir, 'input')
    output_dir = os.path.join(temp_dir, 'output')
    os.makedirs(input_dir)
    os.makedirs(output_dir)

    try:
        files = request.files.getlist('file')
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(input_dir, filename)
                file.save(file_path)

                if filename.endswith('.zip'):
                    with zipfile.ZipFile(file_path, 'r') as zip_ref:
                        zip_ref.extractall(input_dir)
                    os.remove(file_path)  # Remove the original zip file
                else:
                    process_and_save(file_path, output_dir)

        # Process all files in the input directory (including those extracted from zip)
        for root, _, files in os.walk(input_dir):
            for file in files:
                if allowed_file(file):
                    file_path = os.path.join(root, file)
                    process_and_save(file_path, output_dir)

        # Create a zip file in memory
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w') as zipf:
            for root, _, files in os.walk(output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, output_dir)
                    zipf.write(file_path, arcname)

        # Seek to the beginning of the stream
        memory_file.seek(0)

        return send_file(
            memory_file,
            as_attachment=True,
            download_name='converted_files.zip',
            mimetype='application/zip'
        )

    except Exception as e:
        return jsonify({'error': f'Conversion failed: {str(e)}'}), 500
    finally:
        # Clean up the temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == '__main__':
    app.run(debug=True)