import difflib
from cf_to_tf_converter import convert_to_terraform, load_cloudformation_template

def compare_cf_tf(cf_content, tf_content):
    # Convert CloudFormation to Terraform
    cf_template = load_cloudformation_template(cf_content)
    cf_as_tf = convert_to_terraform(cf_template)

    # Compare
    diff = difflib.unified_diff(
        cf_as_tf.splitlines(keepends=True),
        tf_content.splitlines(keepends=True),
        fromfile='CloudFormation (converted)',
        tofile='Existing Terraform'
    )

    return ''.join(diff)

def generate_diff_report(cf_content, tf_content):
    diff = compare_cf_tf(cf_content, tf_content)
    report = f"Diff between converted CloudFormation and existing Terraform:\n\n{diff}"
    return report

if __name__ == "__main__":
    cf_file = "path/to/cloudformation.yaml"
    tf_file = "path/to/terraform.tf"
    with open(cf_file, 'r') as cf, open(tf_file, 'r') as tf:
        report = generate_diff_report(cf.read(), tf.read())
    print(report)