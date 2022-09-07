#!/usr/bin/python3
# ######################################################################
# Copyright (c) 2022 Boris Baldassari, Nico Toussaint and others
#
# This program and the accompanying materials are made
# available under the terms of the Eclipse Public License 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0/
#
# SPDX-License-Identifier: EPL-2.0
######################################################################

# This script:
# - downloads the Activities Metadata JSON file from the GGI repository
# - saves additional file source information
# - dumps the resulting JSON file in the local filesystem, 
#   so it can be manually committed to the my-gg-board repository.

# usage: ggi_deploy [-h] [-r]
#
# optional arguments:
#   -h, --help        Show this help message and exit
#   -r, --refefence   Target branch or tag
#

import gitlab
import json
import argparse
import base64
import os

local_metadata_file_path = os.getcwd() + '/../conf/ggi_activities_metadata.json'

# Default source:
# https://gitlab.ow2.org/ggi/ggi/-/blob/dev/handbook/content/ggi_activities_metadata.json
remote_git_url='https://gitlab.ow2.org'
remote_git_project='ggi/ggi'
remote_git_reference='dev'
remote_git_metadata_file='handbook/content/ggi_activities_metadata.json'

#
# Parse arguments from command line.
#

parser = argparse.ArgumentParser(prog='ggi_deploy')
parser.add_argument('-r', '--reference',
    dest='target_git_ref',
    action='store',
    default=remote_git_reference,
    help='Specify target branch or tag')
args = parser.parse_args()

# Connect to GitLab
print(f"# Connection to GitLab\nGit remote={remote_git_url}\n")
gl = gitlab.Gitlab(url=remote_git_url, per_page=50)
gl_project = gl.projects.get(remote_git_project)

# Download remote file
print(f"# Download Metadata file\nGit ref={args.target_git_ref}\n")
metadata = gl_project.files.get(file_path=remote_git_metadata_file, ref=args.target_git_ref)

# Add source info
metadata_dict = json.loads(base64.b64decode(metadata.content))
metadata_dict.update({"source": {}})
metadata_source = metadata_dict.get("source")
metadata_source.update({"git-remote" : remote_git_url})
metadata_source.update({"git-project" : remote_git_project})
metadata_source.update({"git-reference" : metadata.ref})
metadata_source.update({"git-commit-id" : metadata.commit_id})
print(f"# Added source information:\n" + json.dumps(metadata_source, indent=True) + "\n")

# Save file locally
print(f"# Save file in filesystem\nFilepath={local_metadata_file_path}\n")
with open(local_metadata_file_path, 'w') as metadata_file:
    json.dump(metadata_dict, metadata_file, indent=2)
