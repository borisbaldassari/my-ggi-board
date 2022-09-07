#!/usr/bin/python3
# ######################################################################
# Copyright (c) 2022 Boris Baldassari and others
#
# This program and the accompanying materials are made
# available under the terms of the Eclipse Public License 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0/
#
# SPDX-License-Identifier: EPL-2.0
######################################################################

# This script:
# - reads the metadata defined in the `conf` directory,
# - downloads the set of activities described in the gitlab repository on the 
#   `main` branch,
# - merges both and creates a single JSON file with all the information.
# - optionally creates the activities on a new (empty) gitlab project,
# - optionally creates a board and its lists to display activities.

# usage: ggi_deploy [-h] [-a] [-b]
# 
# optional arguments:
#   -h, --help        show this help message and exit
#   -a, --activities  Create activities
#   -b, --board       Create board
# 

import gitlab
import json
import requests 
import tarfile
import argparse
import tldextract
import urllib.parse, glob, os
from fileinput import FileInput

# Define some variables.

file_conf = 'conf/ggi_deployment.json'
file_meta = 'conf/ggi_activities_metadata.json'
file_json_out = 'ggi_activities_full.json'

path_activities = 'ggi-main-handbook-content/handbook/content/'
tmp_gz_file = 'ggi_content.tar.bz2'


#
# Parse arguments from command line.
#

parser = argparse.ArgumentParser(prog='ggi_deploy')
parser.add_argument('-a', '--activities', 
    dest='opt_activities', 
    action='store_true', 
    help='Create activities')
parser.add_argument('-b', '--board', 
    dest='opt_board', 
    action='store_true', 
    help='Create board')
args = parser.parse_args()


#
# Read metadata for activities and deployment options.
#

print(f"\n# Reading metadata from {file_meta}.")
with open(file_meta, 'r', encoding='utf-8') as f:
    metadata = json.load(f)
  
print(f"# Reading deployment options from {file_conf}.")
with open(file_conf, 'r', encoding='utf-8') as f:
    conf = json.load(f)

if os.environ['GGI_ACCESS_TOKEN']:
    print("- Using access_token from env var.")
else:
    print(" Cannot find env var GGI_ACCESS_TOKEN. Please set it and re-run me.")
    exit(1)
    
#
# Build activities
#

# Download activities content from the main gitlab project.
url_activities = conf['activities_url']
if conf['proxy_url'] != '':
    proxy = {conf['proxy_url']}
    print(f"\n# Downloading file from {url_activities} with proxy {proxy}.")
    resp = requests.get(url_activities, proxies=proxy)
else:
    print(f"\n# Downloading file from {url_activities}.")
    resp = requests.get(url_activities)

# And store content as a gz file.
with open(tmp_gz_file, 'wb') as fd:
    for chunk in resp.iter_content(chunk_size=128):
        fd.write(chunk)

activities = []
print("\n# Building activities.")
tf = tarfile.open(tmp_gz_file, 'r:bz2')
for activity in metadata['activities']:
    print(f"  - Building activity [{activity['id']}]..")
    content = tf.extractfile(
          'ggi-main-handbook-content/handbook/content/' 
          + activity['path']
      ).readlines()
    activity['content'] = "".join( [ i.decode() for i in content ] )
    activities.append(activity)

# Write down intermediate file with all merged activities.
with open(file_json_out, 'w', encoding='utf-8') as f:
    json.dump(activities, f, ensure_ascii=False, indent=4)


#
# Connect to GitLab
#

if (args.opt_activities) or (args.opt_board):
    print(f"\n# Connection to GitLab at {conf['gitlab_url']}.")
    gl = gitlab.Gitlab(url=conf['gitlab_url'], per_page=50, private_token=os.environ['GGI_ACCESS_TOKEN'])
    project = gl.projects.get(conf['gitlab_project'])


#
# Create activities
#

if (args.opt_activities):

    print("\n# Manage labels.")
    # Check existing labels
    existing_labels = [i.name for i in project.labels.list()]
    print(f"  - Existing labels: {existing_labels}.")
    # Create role labels if needed
    for label in metadata['roles'].keys():
        if label not in existing_labels:
            print(f"  - Creating label: {label}.")
            project.labels.create(
                {'name': label, 'color': metadata['roles'][label]}
              )

    # Create labels for activity tracking
    for label in conf['progress_labels'].keys():
        if label not in existing_labels:
            name = conf['progress_labels'][label]
            print(f"  - Creating label: {name}.")
            project.labels.create(
                {'name': name, 'color': '#ed9121'}
              )

    # Create goal labels if needed
    for goal in metadata['goals']:
        if goal['name'] not in existing_labels:
            print(f"  - Creating label: {goal['name']}.")
            project.labels.create(
                {'name': goal['name'], 'color': goal['colour']}
              )

    # Create issues with their associated labels.
    print("\n# Create activities.")
    for activity in activities:
      print(f"  - Creating issue [{activity['name']}]..")
      labels = [activity['goal']] + activity['roles'] \
          + [conf['progress_labels']['not_started']]
      print(f"    with labels {labels}")
      description = "".join( [i for i in activity['content']] )
      ret = project.issues.create({'title': activity['name'],
                                   'description': description, 
                                   'labels': labels})


#
# Create Goals board
#

if (args.opt_board):
    print('\n# Creating Goals board.')
    board = project.boards.create({'name': 'GGI Activities/Goals'})

    print('\n# Creating Goals board lists.')
    # First build an ordered list of goals
    goal_lists = []
    for g in metadata['goals']:
        for l in project.labels.list():
            if l.name == g['name']:
                goal_lists.append(l)
                break
    
    # Then create the lists in gitlab
    for goal_label in goal_lists: 
        print(f"  - Creating list for {goal_label.name} - {goal_label.id}.")
        b_list = board.lists.create({'label_id': goal_label.id})
    
print("Done.")


#
# Setup website
#


print("\n# Replacing keywords in static website.")

# List of strings to be replaced.
pieces = tldextract.extract(conf['gitlab_url'])
ggi_url = urllib.parse.urljoin(
    conf['gitlab_url'], conf['gitlab_project'])
ggi_pages_url = 'https://' + conf['gitlab_project'].split('/')[0] + "." + pieces.domain + ".io/" + conf['gitlab_project'].split('/')[-1]
ggi_activities_url = os.path.join(ggi_url, '-/boards')
keywords = {
    '[GGI_URL]': ggi_url,
    '[GGI_PAGES_URL]': ggi_pages_url,
    '[GGI_ACTIVITIES_URL]': ggi_activities_url
}

[ print(f"- {k} {keywords[k]}") for k in keywords.keys() ]


# Replace keywords in md files.
def update_keywords(file_in, keywords):
    occurrences = []
    for keyword in keywords:
        for line in FileInput(file_in, inplace=1, backup='.bak'):
            if keyword in line:
                occurrences.append(f'- Changing "{keyword}" to "{keywords[keyword]}" in {file_in}.')
                line = line.replace(keyword, keywords[keyword])
            print(line, end='')
    [ print(o) for o in occurrences ]

update_keywords('web/config.toml', keywords)
update_keywords('README.md', keywords)
files = glob.glob("web/content/*.md")
files_ = [ f for f in files if os.path.isfile(f) ]
for file in files_:
    update_keywords(file, keywords)
    
print("Done.")

