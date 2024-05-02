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

"""
This script:
- reads the metadata defined in the `conf` directory,
- retrieves information from the gitlab project,
- updates the static website with new information and plots

"""

import argparse
import json
import pandas as pd
import re
import glob, os
from typing import List
from fileinput import FileInput
from datetime import date
from collections import OrderedDict
import tldextract
import urllib.parse

# Define some variables.

file_conf = 'conf/ggi_deployment.json'
file_meta = 'conf/ggi_activities_metadata.json'
file_json_out = 'ggi_activities_full.json'

# Define regexps

# Identify tasks in description:
re_tasks = re.compile(r"^\s*- \[(?P<is_completed>.)\] (?P<task>.+)$")
# Identify tasks in description:
re_activity_id = re.compile(r"^Activity ID: \[(GGI-A-\d\d)\]\(.+\).$")
# Identify sections for workflow parsing.
re_section = re.compile(r"^### (?P<section>.*?)\s*$")
re_subsection = re.compile(r"^#### (?P<subsection>.*?)\s*$")


def parse_args():
    """
    Parse arguments from command line.
    """

    parser = argparse.ArgumentParser(
        description="Regerate website.")
    parser.add_argument('-v', '--verbose',
                        dest='opt_verbose',
                        action='store_true',
                        help='More logging.')
    args = parser.parse_args()

    return args


def extract_workflow(activity_desc: str):
    """
    Extract specific sections from an issue description.
    """
    paragraphs = activity_desc.split('\n')
    content_t = 'Introduction'
    content = OrderedDict()
    content = {content_t: []}
    a_id = ""
    for p in paragraphs:
        activity_id_match = re_activity_id.match(p)
        if activity_id_match:
            a_id = activity_id_match.group(1)
            continue
        match_section = re.search(re_section, p)
        if match_section:
            content_t = match_section.group('section')
            content[content_t] = []
        else:
            content[content_t].append(p)
    subsection = 'Default'
    workflow = {subsection: []}
    # Parse the scorecard section.
    tasks = []
    if 'Scorecard' in content:
        for p in content['Scorecard']:
            match_subsection = re.search(re_subsection, p)
            if match_subsection:
                subsection = match_subsection.group('subsection')
                workflow[subsection] = []
            elif p != '':
                workflow[subsection].append(p)
                # Now identify tasks
                match_tasks = re.search(re_tasks, p)
                if match_tasks:
                    is_completed = match_tasks.group('is_completed')
                    is_completed = True if is_completed == 'x' else False
                    task = match_tasks.group('task')
                    tasks.append({'is_completed': is_completed, 'task': task})
    # Remove first element (useless html stuff)
    del workflow['Default']
    # Remove last two elements (useless html stuff too)
    if len(list(workflow)) > 2:
        del workflow[list(workflow)[-1]][-1]
        del workflow[list(workflow)[-1]][-1]
    return a_id, content['Description'], workflow, tasks


def retrieve_env():
    """
    Read metadata for activities and deployment options.
    
    Determine GitLab server URL and Project name
    * From Environment variable if available, or
    * From configuration file otherwise
    """

    print(f"# Reading deployment options from {file_conf}.")
    with open(file_conf, 'r', encoding='utf-8') as f:
        params = json.load(f)

    if 'CI_SERVER_URL' in os.environ:
        print("- Use GitLab URL from environment variable")
        params['GGI_GITLAB_URL'] = os.environ['CI_SERVER_URL']
    else:
        print("- Use GitLab URL from configuration file")
        params['GGI_GITLAB_URL'] = params['gitlab_url']

    if 'CI_PROJECT_PATH' in os.environ:
        print("- Use GitLab Project from environment variable")
        params['GGI_GITLAB_PROJECT'] = os.environ['CI_PROJECT_PATH']
    else:
        print("- Use GitLab URL from configuration file")
        params['GGI_GITLAB_PROJECT'] = params['gitlab_project']

    if 'GGI_GITLAB_TOKEN' in os.environ:
        print("- Using ggi_gitlab_token from env var.")
        params['GGI_GITLAB_TOKEN'] = os.environ['GGI_GITLAB_TOKEN']
    else:
        print("- Cannot find env var GGI_GITLAB_TOKEN. Please set it and re-run me.")
        exit(1)

    if 'CI_PAGES_URL' in os.environ:
        print("- Using GGI_PAGES_URL from environment variable.")
        params['GGI_PAGES_URL'] = os.environ['CI_PAGES_URL']
    else:
        print("- Cannot find an env var for GGI_PAGES_URL. Computing it from conf.")
        pieces = tldextract.extract(params['GGI_GITLAB_URL'])
        params['GGI_PAGES_URL'] = 'https://' + params['GGI_GITLAB_PROJECT'].split('/')[0] + \
                                  "." + pieces.domain + ".io/" + params['GGI_GITLAB_PROJECT'].split('/')[-1]

    params['GGI_URL'] = urllib.parse.urljoin(params['GGI_GITLAB_URL'], params['GGI_GITLAB_PROJECT'])
    params['GGI_ACTIVITIES_URL'] = os.path.join(params['GGI_URL'] + '/', '-/boards')

    return params


def write_to_csv(issues, tasks, events):
    """
    Print all issues, tasks and events to CSV files.

    CSV files are written directly to the website directory structure,
    and provided to the user as downloads for further analysis.
    """
    print("\n# Writing issues and history to files.")
    issues.to_csv('web/content/includes/issues.csv',
                  columns=['issue_id', 'activity_id', 'state', 'title', 'labels',
                           'updated_at', 'url', 'tasks_total', 'tasks_done'], index=False)
    events.to_csv('web/content/includes/labels_hist.csv', index=False)
    tasks.to_csv('web/content/includes/tasks.csv', index=False)


def write_activities_to_md(issues: List):
    # Generate list of current activities
    print("\n# Writing issues.")

    for local_id, activity_id, activity_date, title, url, desc, workflow, tasks_done, tasks_total in zip(
            issues['issue_id'],
            issues['activity_id'],
            issues['updated_at'],
            issues['title'],
            issues['url'],
            issues['desc'],
            issues['workflow'],
            issues['tasks_done'],
            issues['tasks_total']):
        print(f" {local_id}, {activity_id}, {title}, {url}")

        my_issue = []

        my_issue.append('---')
        my_issue.append(f'title: {title}')
        my_issue.append(f'date: {activity_date}')
        my_issue.append('layout: default')
        my_issue.append('---')

        my_issue.append(
            f"Link to Issue: <a href='{url}' class='w3-text-grey' style='float:right'>[ {activity_id} ]</a>\n\n")
        my_issue.append(f"Tasks: {tasks_done} done / {tasks_total} total.")
        if tasks_total > 0:
            p = int(tasks_done) * 100 // int(tasks_total)
            my_issue.append(f'  <div class="w3-light-grey w3-round">')
            my_issue.append(f'    <div class="w3-container w3-blue w3-round" style="width:{p}%">{p}%</div>')
            my_issue.append(f'  </div><br />')
        else:
            my_issue.append(f'  <br /><br />')
        my_workflow = "\n"
        for subsection in workflow:
            my_workflow += f'**{subsection}**\n\n'
            my_workflow += '\n'.join(workflow[subsection])
            my_workflow += '\n\n'
        my_issue.append(f"{my_workflow}")

        filename = f'web/content/scorecards/activity_{activity_id}.md'
        with open(filename, 'w') as f:
            f.write('\n'.join(my_issue))


def write_data_points(issues, params):
    """
    Generates data points for the various dashboard plots.
    """

    # Identify activities depending on their progress
    issues_not_started = issues.loc[issues['labels'].str.contains(params['progress_labels']['not_started']),]
    issues_in_progress = issues.loc[issues['labels'].str.contains(params['progress_labels']['in_progress']),]
    issues_done = issues.loc[issues['labels'].str.contains(params['progress_labels']['done']),]

    # Generate all activities stats.
    ggi_data_all_activities = f'[{issues_not_started.shape[0]}, {issues_in_progress.shape[0]}, {issues_done.shape[0]}]'
    with open('web/content/includes/ggi_data_all_activities.inc', 'w') as f:
        f.write(ggi_data_all_activities)

    # Generate data points for the dashboard - goals - done
    done_stats = [
        issues_done['labels'].str.contains('Usage').sum(),
        issues_done['labels'].str.contains('Trust').sum(),
        issues_done['labels'].str.contains('Culture').sum(),
        issues_done['labels'].str.contains('Engagement').sum(),
        issues_done['labels'].str.contains('Strategy').sum()
    ]
    with open('web/content/includes/ggi_data_goals_done.inc', 'w') as f:
        f.write(str(done_stats))

    # Generate data points for the dashboard - goals - in_progress
    in_progress_stats = [
        issues_in_progress['labels'].str.contains('Usage').sum(),
        issues_in_progress['labels'].str.contains('Trust').sum(),
        issues_in_progress['labels'].str.contains('Culture').sum(),
        issues_in_progress['labels'].str.contains('Engagement').sum(),
        issues_in_progress['labels'].str.contains('Strategy').sum()
    ]
    with open('web/content/includes/ggi_data_goals_in_progress.inc', 'w') as f:
        f.write(str(in_progress_stats))

    # Generate data points for the dashboard - goals - not_started
    not_started_stats = [
        issues_not_started['labels'].str.contains('Usage').sum(),
        issues_not_started['labels'].str.contains('Trust').sum(),
        issues_not_started['labels'].str.contains('Culture').sum(),
        issues_not_started['labels'].str.contains('Engagement').sum(),
        issues_not_started['labels'].str.contains('Strategy').sum()
    ]
    with open('web/content/includes/ggi_data_goals_not_started.inc', 'w') as f:
        f.write(str(not_started_stats))

    # Generate activities basic statistics, with links to be used from home page.
    activities_stats = f'Identified {issues.shape[0]} activities overall.\n'
    activities_stats += f'* {issues_not_started.shape[0]} are <span class="w3-tag w3-light-grey">not_started</span>\n'
    activities_stats += f'* {issues_in_progress.shape[0]} are <span class="w3-tag w3-light-grey">in_progress</span>\n'
    activities_stats += f'* {issues_done.shape[0]} are <span class="w3-tag w3-light-grey">done</span>\n'
    with open('web/content/includes/activities_stats_dashboard.inc', 'w') as f:
        f.write(activities_stats)

    # Used for the activities table dataset
    activities_dataset = []
    print(issues)
    for index, issue in issues.iterrows():
        # XXX TODO
        issue_id = issue['issue_id']
        status = issue['state']
        title = issue['title']
        tasks_done = issue['tasks_done']
        tasks_total = issue['tasks_total']
        status = "Not started"
        if tasks_done > 0:
            status = "In progress"
            if tasks_done == tasks_total:
                status = "Completed"

        activities_dataset.append([issue_id, status, title, tasks_done, tasks_total])

    with open('web/content/includes/activities.js.inc', 'w') as f:
        f.write(str(activities_dataset))

    # Empty (or not) the initialisation banner text in index
    # if at least one activity is started.
    if issues_not_started.shape[0] < 25:
        with open('web/content/includes/initialisation.inc', 'w') as f:
            f.write('')


def update_keywords(file_in, keywords):
    """
    Reads a file, and replace every occurrence of one keyword with
    its replacement string.
    """
    occurrences = []
    for keyword in keywords:
        for line in FileInput(file_in, inplace=1, backup='.bak'):
            if keyword in line:
                occurrences.append(f'- Changing "{keyword}" to "{keywords[keyword]}" in {file_in}.')
                line = line.replace(keyword, keywords[keyword])
            print(line, end='')
    [print(o) for o in occurrences]
