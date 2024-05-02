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
import urllib.parse

from ggi_deploy import *

from github import Github
from github import Auth


def main():
    """
    Main GITHUB.
    """
    args = parse_args()

    print("* Using GitHub backend.")
    metadata, params, init_scorecard = retrieve_env()
    setup_github(metadata, params, init_scorecard, args)

    print("\nDone.")

def create_github_label(repo, existing_labels, new_label, label_args):
    """
    Creates a set of labels in the GitHub project.
    """
    if new_label in existing_labels:
        print(f" Ignore label: {new_label}")
    else:
        print(f" Create label: {new_label}")
        name = label_args['name']
        color = label_args['color'].replace("#","")
        repo.create_label(name, color)


def setup_github(metadata, params: dict, init_scorecard, args: dict):
    """
    Executes the following deployment sequence on a GitHub instance:
    * Reads gitlab-specific variables.
    * Connect to GitHub
    * Create labels & activities
    * Create Goals board
    * Create schedule for pipeline
    """

    # Get environment / vars.

    if 'github_project' in params:
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

    # Using an access token
    auth = Auth.Token(params['GGI_GITHUB_TOKEN'])

    # Connecting to the GitHub instance.
    if 'github_host' in params and params['github_host'] != 'null':
        print(f"- Using GitHub on-premise host {params['github_host']} " +
              "from configuration file.")
        # Github Enterprise with custom hostname
        github_url = f"{params['github_host']}/api/v3"
        g = Github(auth=auth,
                   base_url=github_url)
        params['GGI_GITHUB_URL'] = params['github_host']
    else:
        # Public Web Github
        print("- Using public GitHub instance.")
        g = Github(auth=auth)
        params['GGI_GITHUB_URL'] = "https://github.com/"

    params['GGI_GITHUB_URL'] = params['GGI_GITHUB_URL'] + "/" + params["github_project"]

    print(f"\n# Retrieving project from GitHub at {params['GGI_GITHUB_URL']}.")
    repo = g.get_repo(params["github_project"])

    if args.opt_activities:

        # Create labels.
        existing_labels = repo.get_labels()
        # existing_labels = [i.name for i in project.labels.list()]
        print('DBG', existing_labels)
        # Create role labels if needed
        print("\n Roles labels")
        for label, colour in metadata['roles'].items():
            create_github_label(repo, existing_labels, label, {'name': label, 'color': colour})

        # Create labels for activity tracking
        print("\n Progress labels")
        for name, label in params['progress_labels'].items():
            create_github_label(repo, existing_labels, label, {'name': label, 'color': 'ed9121'})

        # Create goal labels if needed
        print("\n Goal labels")
        for goal in metadata['goals']:
            create_github_label(repo, existing_labels, goal['name'],
                                {'name': goal['name'], 'color': goal['colour']})

    # Create issue with labels.
    # label = repo.get_label("My Label")

    # Close the connection.
    g.close()

if __name__ == '__main__':
    main()
