"""Script to rename all occurrences of Argus to Argus across the project.
"""
import os
import re

REPLACEMENTS = [
    ("Argus — Delhi Street Hazard Intelligence & Civic Accountability Platform", "Argus — Delhi Street Hazard Intelligence & Civic Accountability Platform"),
    ("Argus", "Argus"),
    ("argus-frontend", "argus-frontend"),
    ("argus", "argus"),
    ("argus-shared-layer", "argus-shared-layer"),
    ("argus-", "argus-"),
    ("Argus", "Argus"),
    ("argus", "argus"),
]

TARGET_EXTENSIONS = ('.py', '.json', '.yaml', '.yml', '.ts', '.tsx', '.html', '.md', '.toml', '.sh')
IGNORE_DIRS = ('.git', 'node_modules', '.venv', '.aws-sam', 'dist', '__pycache__', '.pytest_cache')

modified_files = []

for root, dirs, files in os.walk('.'):
    if any(ig in root for ig in IGNORE_DIRS):
        continue
    for f in files:
        if f.endswith(TARGET_EXTENSIONS):
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='utf-8') as fp:
                    content = fp.read()
                
                new_content = content
                for old_val, new_val in REPLACEMENTS:
                    new_content = new_content.replace(old_val, new_val)
                
                if new_content != content:
                    with open(path, 'w', encoding='utf-8') as fp:
                        fp.write(new_content)
                    modified_files.append(path)
            except Exception as e:
                print(f"Error processing {path}: {e}")

print(f"Successfully replaced 'Argus' with 'Argus' across {len(modified_files)} files:")
for m in modified_files:
    print(f"  {m}")
