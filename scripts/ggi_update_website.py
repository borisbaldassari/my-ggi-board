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
# - retrieves information from the gitlab project,
# - updates the static website with new information and plots


import gitlab
import json
#import requests 
import tarfile
import argparse
import pandas as pd

# Define some variables.

file_conf = 'conf/ggi_deployment.json'
file_meta = 'conf/ggi_activities_metadata.json'
file_json_out = 'ggi_activities_full.json'


#
# Parse arguments from command line.
#

parser = argparse.ArgumentParser(prog='ggi_update_website')
#parser.add_argument('-a', '--activities', 
#    dest='opt_activities', 
#    action='store_true', 
#    help='Create activities')
parser.add_argument('-i', '--issues', 
    dest='opt_issues_csv', 
    help='Read issues from csv file.')
args = parser.parse_args()

if args.opt_issues_csv:
    issues_csv_file = args.opt_issues_csv 

#
# Read metadata for activities and deployment options.
#

#print(f"\n# Reading metadata from {file_meta}.")
#with open(file_meta, 'r', encoding='utf-8') as f:
#    metadata = json.load(f)
  
print(f"# Reading deployment options from {file_conf}.")
with open(file_conf, 'r', encoding='utf-8') as f:
    conf = json.load(f)
    
issues = []
hist = []
if args.opt_issues_csv:
    print(f"# Reading issues from {issues_csv_file}.")
    with open(issues_csv_file, 'r') as f:
        issues = pd.read_csv(issues_csv_file)
    for index, row in issues.iterrows():
        print(f"- {row[0]} {row[2]}.")
else:
    print(f"\n# Connection to GitLab at {conf['gitlab_url']} - {conf['gitlab_project']}.")
    gl = gitlab.Gitlab(url=conf['gitlab_url'], per_page=50, private_token=conf['gitlab_token'])
    project = gl.projects.get(conf['gitlab_project'])

    print("# Fetching issues..")
    gl_issues = project.issues.list(state='opened', all=True)

    #pd.DataFrame(columns=['time', 'issue_id', 'event_id', 'type', 'author', 'action', 'url'])
    for i in gl_issues:
        print(f"- {i.iid} - {i.title} - {i.web_url} - {i.updated_at}.")
        issues.append([i.iid, i.state, i.title, ','.join(i.labels), i.updated_at, i.web_url])
    
        # Retrieve information about labels.
        for n in i.resourcelabelevents.list():
            event = i.resourcelabelevents.get(n.id)
            n_type = 'label'
            label = n.label['name'] if n.label else ''
            n_action = f"{n.action} {label}"
            line = [n.created_at, i.iid,
                    n.id, n_type, n.user['username'], 
                    n_action, i.web_url]
            hist.append(line)

# Convert lists to dataframes
issues = pd.DataFrame(issues, columns=['issue_id', 'state', 'title', 'labels', 'updated_at', 'url'])
hist = pd.DataFrame(hist, columns=['time', 'issue_id', 'event_id', 'type', 'author', 'action', 'url'])


issues_in_progress = []
issues_done = []
print(issues)
print(f" len issues {len(issues)}.")
for issue in issues.itertuples():
    print(f"- i {conf['progress_labels']['in_progress']} {issue.issue_id} {issue[4].split(',')}.")
    if conf['progress_labels']['in_progress'] in issue[4].split(','):
        print(f"- {issue.issue_id} in progress.")
        issues_in_progress.append([issue.issue_id, issue.state, issue.title, ','.join(issue.labels), issue.updated_at, issue.url])

    if conf['progress_labels']['done'] in issue[4].split(','):
        print(f"- {issue.issue_id} done.")
        issues_done.append([issue.issue_id, issue.state, issue.title, ','.join(issue.labels), issue.updated_at, issue.url])

issues_in_progress = pd.DataFrame(issues_in_progress, columns=['issue_id', 'state', 'title', 'labels', 'updated_at', 'url'])
issues_done = pd.DataFrame(issues_done, columns=['issue_id', 'state', 'title', 'labels', 'updated_at', 'url'])

# Print all rows to CSV file
issues.to_csv('web/content/includes/issues.csv', index=False)
hist.to_csv('web/content/includes/labels_hist.csv', index=False)

# Generate list of current activities
state_in_progress = conf['progress_labels']['in_progress']
with open('web/content/includes/current_activities.inc', 'w') as f:
    my_issues = []
    print(f"issue in progress {issues_in_progress['issue_id']}")
    for x, y, z in zip(issues_in_progress['issue_id'], issues_in_progress['title'], issues_in_progress['url']):
        print(f" {x}, {y}, {z}")
        my_issues.append(f"* {x} [{y}]({z}).")
    print(f"f {my_issues}.")
    f.write('\n'.join(my_issues))

# Generate list of past activities
state_done = conf['progress_labels']['in_progress']
with open('web/content/includes/past_activities.inc', 'w') as f:
    my_issues = []
    print(f"issue done {issues_done['issue_id']}")
    for x, y, z in zip(issues_done['issue_id'], issues_done['title'], issues_done['url']):
        print(f" {x}, {y}, {z}")
        my_issues.append(f"* {x} [{y}]({z}).")
    print(f"f {my_issues}.")
    f.write('\n'.join(my_issues))

#
# Replace 
#

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
            
