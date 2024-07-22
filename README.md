# CloudFormation to Terraform Converter

## Table of Contents
1. [Introduction](#introduction)
2. [Features](#features)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
5. [Usage](#usage)
6. [Project Structure](#project-structure)
7. [How It Works](#how-it-works)
8. [Customization](#customization)
9. [Limitations](#limitations)
10. [Troubleshooting](#troubleshooting)
11. [Contributing](#contributing)

## Introduction

The CloudFormation to Terraform Converter is a web-based tool that simplifies the process of migrating AWS CloudFormation templates to Terraform configuration files. This tool is designed for cloud engineers and DevOps professionals who are transitioning from AWS-specific infrastructure-as-code to a more cloud-agnostic approach using Terraform.

## Features

- Web-based interface for easy file uploads
- Supports single file, multiple files, and ZIP file uploads
- Converts CloudFormation (YAML/JSON) to Terraform (.tf) format
- Provides immediate download of converted files
- Allows multiple conversions without page refresh
- Responsive design for various device sizes

## Prerequisites

- Python 3.7+
- Flask
- Werkzeug
- A modern web browser (Chrome, Firefox, Safari, or Edge)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/aperswal/CloudFormation_To_Terraform.git
   cd CloudFormation_To_Terraform
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Start the Flask server:
   ```
   python app.py
   ```

2. Open a web browser and navigate to `http://localhost:5000`

3. Click on the "Pick Your Files" button and select your CloudFormation template(s) or a ZIP file containing multiple templates.

4. The conversion will start automatically, and you'll receive a ZIP file with the converted Terraform files.

## Project Structure

```
CloudFormation_To_Terraform/
│
├── app.py                 # Main Flask application
├── cf_to_tf_converter.py  # Core conversion logic
├── templates/
│   └── index.html         # Main page template
├── static/
│   └── css/
│       └── styles.css     # (Optional) Additional styles
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## How It Works

1. The user selects CloudFormation files through the web interface.
2. Files are uploaded to the server and saved in a temporary directory.
3. The `cf_to_tf_converter.py` script processes each file, converting CloudFormation syntax to Terraform.
4. Converted files are zipped and sent back to the user's browser for download.
5. Temporary files are cleaned up on the server.

## Customization

- Modify `index.html` to change the user interface.
- Adjust styles in `static/css/styles.css` (if you decide to separate CSS from HTML).
- Extend `cf_to_tf_converter.py` to support additional CloudFormation resource types or improve conversion accuracy.

## Limitations

- Not all CloudFormation resources may have direct Terraform equivalents.
- Complex CloudFormation templates with custom resources or intrinsic functions may require manual adjustment after conversion.
- The tool does not currently support AWS-specific features that don't have Terraform counterparts.

## Troubleshooting

- If conversions fail, check the server logs for detailed error messages.
- Ensure your CloudFormation templates are valid before attempting conversion.
- For large files or many concurrent users, you may need to adjust Flask's configuration for better performance.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request
