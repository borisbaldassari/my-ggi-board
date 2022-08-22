######################################################################
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
import urllib.request 
import tarfile
import argparse

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
    

#
# Build activities
#

# Download activities content from the main gitlab project.
url_activities = conf['activities_url']
print(f"\n# Downloading file from {url_activities}.")
urllib.request.urlretrieve(url_activities, tmp_gz_file)

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

print(f"\n# Connection to GitLab at {conf['gitlab_url']}.")
gl = gitlab.Gitlab(url=conf['gitlab_url'], per_page=50, private_token=conf['gitlab_token'])
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
      labels = [activity['goal']] + activity['roles']
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






