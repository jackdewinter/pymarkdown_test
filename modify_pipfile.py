


import os
import sys

current_python_version = sys.version
index = current_python_version.index("(")
current_python_version = current_python_version[:index].strip()

file_path = "Pipfile"
with open(file_path, "rt", encoding="utf-8") as input_file:
    all_lines = input_file.readlines()

modified_lines = []
did_find = False
for i in all_lines:
    if not did_find and i == 'python_version = "3.8"\n':
        i = f'python_version = "{current_python_version}"\n'
        did_find = True
    modified_lines.append(i)

assert did_find, "Did not find and replace python version with current version."
with open(file_path, "wt", encoding="utf-8") as output_file:
    output_file.writelines(modified_lines)
