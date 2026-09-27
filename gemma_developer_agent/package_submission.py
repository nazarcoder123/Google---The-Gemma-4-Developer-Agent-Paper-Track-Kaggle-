"""
Package Google ADK Agent directory into competition-compliant submission.zip
"""

import os
import zipfile


def create_submission_zip(source_dir: str, output_zip: str):
    print(f"Creating submission zip from {source_dir} -> {output_zip}...")
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, source_dir)
                zf.write(full_path, rel_path)
    print(f"[SUCCESS] Created {output_zip} ({os.path.getsize(output_zip)} bytes).")


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    src_agent_dir = os.path.join(base_dir, "adk_agent")
    out_zip = os.path.join(base_dir, "submission.zip")
    create_submission_zip(src_agent_dir, out_zip)
