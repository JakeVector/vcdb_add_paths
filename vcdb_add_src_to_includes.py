"""
vcdb_add_src_to_includes.py

Reads a commands.txt file (VCDB format) and, for each compile command,
checks whether the directory containing the source file (.c or .cpp) is
already listed as a -I include path.  If it is not, the directory is
inserted as a new -I argument immediately before the source file token.

The modified commands are written to a new file alongside the input file
(same name with a _modified suffix before the extension).

Usage:
    python vcdb_add_src_to_includes.py <commands_file>

Example:
    python vcdb_add_src_to_includes.py commands.txt
"""

import os
import re
import sys


def normalize(path, base_dir):
    """Return a normalised absolute path, resolving relative paths against base_dir."""
    if not os.path.isabs(path):
        path = os.path.join(base_dir, path)
    return os.path.normpath(path)


def extract_includes(tokens, base_dir):
    """
    Return a set of normalised include paths extracted from the token list.
    Handles both '-I path' (separate token) and '-Ipath' (attached) forms.
    """
    includes = set()
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token == '-I' and i + 1 < len(tokens):
            includes.add(normalize(tokens[i + 1], base_dir))
            i += 2
        elif token.startswith('-I') and len(token) > 2:
            includes.add(normalize(token[2:], base_dir))
            i += 1
        else:
            i += 1
    return includes


def find_source_token(tokens):
    """
    Return the index of the first token that looks like a C/C++ source file.
    The token must end with .c or .cpp (case-insensitive) and must not start
    with '-' (so compiler flags like -std=c99 are not matched).
    """
    pattern = re.compile(r'.+\.(c|cpp)$', re.IGNORECASE)
    for idx, token in enumerate(tokens):
        if not token.startswith('-') and pattern.match(token):
            return idx
    return -1


def process_commands(input_path):
    output_path = re.sub(r'(\.[^.]+)$', r'_modified\1', input_path)
    if output_path == input_path:          # no extension found
        output_path = input_path + '_modified'

    current_dir = os.getcwd()
    added_count = 0

    with open(input_path, 'r', encoding='utf-8', errors='replace') as fin, \
         open(output_path, 'w', encoding='utf-8') as fout:

        for raw_line in fin:
            line = raw_line.rstrip('\n').rstrip('\r')

            # Track the working directory declared for subsequent commands
            if line.startswith('dir::'):
                current_dir = line[5:].strip()
                fout.write(raw_line)
                continue

            if not line.startswith('cmd::'):
                fout.write(raw_line)
                continue

            cmd_body = line[5:]          # everything after 'cmd::'
            tokens = cmd_body.split()

            src_idx = find_source_token(tokens)
            if src_idx == -1:
                # No source file found – leave the line unchanged
                fout.write(raw_line)
                continue

            src_token = tokens[src_idx]
            src_dir = os.path.dirname(src_token)

            if not src_dir:
                # Source file has no directory component, nothing to add
                fout.write(raw_line)
                continue

            norm_src_dir = normalize(src_dir, current_dir)
            existing_includes = extract_includes(tokens, current_dir)

            if norm_src_dir not in existing_includes:
                # Insert '-I <src_dir>' immediately before the source file token
                tokens.insert(src_idx, src_dir)
                tokens.insert(src_idx, '-I')
                cmd_body = ' '.join(tokens)
                added_count += 1

            # Preserve the original line ending character(s)
            ending = raw_line[len(raw_line.rstrip('\n').rstrip('\r')):]
            fout.write('cmd::' + cmd_body + ending)

    print(f"Done. {added_count} command(s) updated.")
    print(f"Output written to: {output_path}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    input_file = sys.argv[1]
    if not os.path.isfile(input_file):
        print(f"Error: file not found: {input_file}")
        sys.exit(1)

    process_commands(input_file)
