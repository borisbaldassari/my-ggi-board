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
# - reads the metadata defined in the `conf` directory,
# - connects to the GitLab uinstance as configured in the ggi_deployment.json file
# - optionally creates the activities on a new (empty) gitlab project,
# - optionally creates a board and its lists to display activities.
#
# The script expects your GitLab private key in the environment variable: GGI_GITLAB_TOKEN

# usage: ggi_deploy [-h] [-a] [-b]
# 
# optional arguments:
#   -h, --help        show this help message and exit
#   -a, --activities  Create activities
#   -b, --board       Create board
# 

import gitlab
import json
import argparse
import tldextract
import urllib.parse, glob, os
from fileinput import FileInput

# Define some variables.
conf_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+'/conf'
activities_file = conf_dir + '/ggi_activities_full.json'
conf_file = conf_dir + '/ggi_deployment.json'

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
print(f"\n# Reading metadata from {activities_file}.")
with open(activities_file, 'r', encoding='utf-8') as f:
    metadata = json.load(f)
  
print(f"# Reading deployment options from {conf_file}.")
with open(conf_file, 'r', encoding='utf-8') as f:
    conf = json.load(f)

#
# Connect to GitLab
#
if not os.environ['GGI_GITLAB_TOKEN']:
    print("Expecting GitLab private token in env variable 'GGI_GITLAB_TOKEN'")
    exit(1)

if (args.opt_activities) or (args.opt_board):
    print(f"\n# Connection to GitLab at {conf['gitlab_url']}.")
    gl = gitlab.Gitlab(url=conf['gitlab_url'], per_page=50, private_token=os.environ['GGI_GITLAB_TOKEN'])
    project = gl.projects.get(conf['gitlab_project'])

def create_label(existing_labels, new_label, label_args):
    if new_label in existing_labels:
        print(f" Ignore label: {new_label}")
    else:
        print(f" Create label: {new_label}")
        project.labels.create(label_args)

#
# Create labels & activities
#
if (args.opt_activities):

    print("\n# Manage labels")
    existing_labels = [i.name for i in project.labels.list()]
    print(f"  - Existing labels: {existing_labels}.")

    # Create role labels if needed
    print("\n Roles labels")
    for label, colour in metadata['roles'].items():
        create_label(existing_labels, label, {'name': label, 'color': colour})

    # Create labels for activity tracking
    print("\n Progress labels")
    for name, label in conf['progress_labels'].items():
        create_label(existing_labels, label, {'name': label, 'color': '#ed9121'})

    # Create goal labels if needed
    print("\n Goal labels")
    for goal in metadata['goals']:
        create_label(existing_labels, goal['name'], {'name': goal['name'], 'color': goal['colour']})

    # Create issues with their associated labels.
    print("\n# Create activities.")
    for activity in metadata['activities']:
      print(f"  - Create issue [{activity['name']}]")
      labels = \
        [activity['goal']] + \
        activity['roles'] + \
        [conf['progress_labels']['not_started']]
      print(f"    with labels  {labels}")
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
ggi_activities_url = os.path.join(ggi_url, '-/issues')
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
