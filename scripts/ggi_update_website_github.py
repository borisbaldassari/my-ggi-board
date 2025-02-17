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

"""
import glob
import json
import os
import urllib.parse
from datetime import date

import pandas as pd
import tldextract
from github import Auth, Github

from ggi_update_website import *


def retrieve_env():
    """
    Read metadata for activities and deployment options.

    Determine GitHub server URL and Project name
    * From Environment variable if available, or
    * From configuration file otherwise
    """

    print(f"# Reading deployment options from {file_conf}.")
    with open(file_conf, 'r', encoding='utf-8') as f:
        params = json.load(f)

    if 'GGI_GITHUB_REPOSITORY' in os.environ: # github.repository
        params['GGI_GITHUB_PROJECT'] = os.environ['GGI_GITHUB_REPOSITORY']
        print(f"- Using GitHub project {params['GGI_GITHUB_PROJECT']} " +
              "from environment variable file.")
    elif 'github_project' in params:
        params['GGI_GITHUB_PROJECT'] = params['github_project']
        print(f"- Using GitHub project {params['github_project']} " +
              "from configuration file.")
    else:
        print("I need a project (org + repo), e.g. ospo-alliance/" +
              "my-ggi-board. Exiting.")
        exit(1)

    if 'GGI_GITHUB_TOKEN' in os.environ:
        print("- Using ggi_github_token from env var.")
        params['GGI_GITHUB_TOKEN'] = os.environ['GGI_GITHUB_TOKEN']
    else:
        print("- Cannot find env var GGI_GITHUB_TOKEN. Please set it and re-run me.")
        exit(1)

    if 'github_host' in params and params['github_host'] != 'null':
        print(f"- Using GitHub on-premises host {params['github_host']} " +
              "from configuration file.")
        # Github Enterprise with custom hostname
        params['GGI_API_URL'] = f"{params['github_host']}/api/v3"
        params['GGI_GITHUB_URL'] = urllib.parse.urljoin(params['github_host'] + '/', params['GGI_GITHUB_PROJECT'])
        params['GGI_PAGES_URL'] = 'https://fix.me'
    else:
        # Public Web GitHub
        params['GGI_API_URL'] = None
        params['GGI_GITHUB_URL'] = urllib.parse.urljoin('https://github.com/', params['GGI_GITHUB_PROJECT'])
        params['GGI_PAGES_URL'] = urllib.parse.urljoin(
            'https://' + re.sub('/.*$', '', params['GGI_GITHUB_PROJECT']) + '.github.io/', 
            re.sub('^.*/', '', params['GGI_GITHUB_PROJECT']))
        print("- Using public GitHub instance.")

    params['GGI_ACTIVITIES_URL']= urllib.parse.urljoin(params['GGI_GITHUB_URL'] + '/', 'issues')

    return params

def retrieve_github_issues(params: dict):
    print(f"\n# Retrieving project from GitHub at {params['GGI_GITHUB_URL']}.")
    # Using an access token
    auth = Auth.Token(params['GGI_GITHUB_TOKEN'])
    if params['GGI_API_URL'] == None :
        g = Github(auth=auth)
    else:
        g = Github(auth=auth, base_url=params['GGI_API_URL'])
    repo = g.get_repo(params["GGI_GITHUB_PROJECT"])

    """
    Retrieve issues from GitHub instance.
    """

    # Define columns for recorded dataframes.
    issues = []
    tasks = []
    hist = []

    print("# Fetching issues..")
    repo_issues = repo.get_issues()

    print(f"  Found {repo_issues.totalCount} issues.")

    for i in repo_issues:
        desc = i.body
        paragraphs = desc.split('\n\n')
        lines = desc.split('\n')
        a_id, description, workflow, a_tasks = extract_workflow(desc)
        for t in a_tasks:
            tasks.append([a_id,
                          'completed' if t['is_completed'] else 'open',
                          t['task']])
        short_desc = '\n'.join(description)
        tasks_total = len(a_tasks)
        tasks_done = len([t for t in a_tasks if t['is_completed']])
        #TODO comprendre pourquoi i.state et pas le label de progression
        #TODO comprendre pourquoi tasks_total et done sont mal calculés pour GitHub
        issues.append([i.id, a_id, i.state, i.title, ','.join([label.name for label in i.labels]),
                       i.updated_at, i.url, short_desc, workflow,
                       tasks_total, tasks_done])

        # Retrieve information about labels.
        # for n in i.resourcelabelevents.list():
        #     event = i.resourcelabelevents.get(n.id)
        #     n_type = 'label'
        #     label = n.label['name'] if n.label else ''
        #     n_action = f"{n.action} {label}"
        #     user = n.user['username'] if n.user else 'unknown'
        #     line = [n.created_at, i.iid,
        #             n.id, n_type, user,
        #             n_action, i.web_url]
        #     hist.append(line)

        for event in i.get_events():
            if event.event == "labeled" or event.event == "unlabeled":
                n_type = 'label'
                label = event.label.name if event.label else ''
                n_action = f"{event.event} {label}"
                user = event.actor.login if event.actor else 'unknown'
                line = [
                    event.created_at,  # Date de l'événement
                    i.number,  # Numéro de l'issue
                    event.id,  # ID de l'événement
                    n_type,  # Type d'événement (toujours 'label')
                    user,  # Utilisateur qui a déclenché l'événement
                    n_action,  # Action effectuée (labeled/unlabeled)
                    i.html_url  # URL de l'issue
                ]
                hist.append(line)

        #print(f"- {i.id} - {a_id} - {i.title} - {i.url} - {i.updated_at}.")

    return issues, tasks, hist


def main():
    """
    Main sequence.
    """

    args = parse_args()

    params = retrieve_env()
    print(params)

    issues, tasks, hist = retrieve_github_issues(params)

    # Convert lists to dataframes
    issues_cols = ['issue_id', 'activity_id', 'state', 'title', 'labels',
                   'updated_at', 'url', 'desc', 'workflow', 'tasks_total', 'tasks_done']
    issues = pd.DataFrame(issues, columns=issues_cols)
    tasks_cols = ['issue_id', 'state', 'task']
    tasks = pd.DataFrame(tasks, columns=tasks_cols)
    hist_cols = ['time', 'issue_id', 'event_id', 'type', 'author', 'action', 'url']
    hist = pd.DataFrame(hist, columns=hist_cols)

    write_to_csv(issues, tasks, hist)
    write_activities_to_md(issues)
    write_data_points(issues, params)

    #
    # Replace URLs, date
    #
    print("\n# Replacing keywords in static website.")

    # List of strings to be replaced.
    print("\n# List of keywords and values:")
    keywords = {
        '[GGI_URL]': params['GGI_GITHUB_URL'],
        '[GGI_PAGES_URL]': params['GGI_PAGES_URL'],
        '[GGI_ACTIVITIES_URL]': params['GGI_ACTIVITIES_URL'],
        '[GGI_CURRENT_DATE]': str(date.today())
    }
    # Print the list of keywords to be replaced in files.
    [print(f"- {k} {keywords[k]}") for k in keywords.keys()]

    print("\n# Replacing keywords in files.")
    update_keywords('web/config.toml', keywords)
    update_keywords('web/content/includes/initialisation.inc', keywords)
    update_keywords('web/content/scorecards/_index.md', keywords)
    # update_keywords('README.md', keywords)
    files = glob.glob("web/content/*.md")
    for file in files:
        if os.path.isfile(file):
            update_keywords(file, keywords)
    try:
        with open('web/content/_index.md', 'r') as file:
            file_content = file.read()
            print(file_content)
    except FileNotFoundError:
        print('not found')
    except Exception as e:
        print('an error occurred')
    print("Done.")


if __name__ == '__main__':
    main()