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

def create_github_label(repo, new_label, label_args):
    existing_labels = {label.name for label in repo.get_labels()}

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

    # Update current project description with Website URL
    # TODO make this works
    if args.opt_projdesc:
        print("\n# Update Project description")
        if True or 'CI_PAGES_URL' in params:
            ggi_activities_url = "https://tbd.com" #params['GGI_ACTIVITIES_URL']
            ggi_handbook_version = metadata["handbook_version"]
            ggi_pages_url = "https://tbd.com" #params['CI_PAGES_URL']
            desc = (
                'Your own Good Governance Initiative project.\n\n'
                'Here you will find '
                f'[**your dashboard**]({ggi_pages_url})\n'
                f'and the [**GitHub Project Board**]({ggi_activities_url}) with all activities describing the local GGI '
                f'deployment, based on the version {ggi_handbook_version} of the [GGI handbook]('
                f'https://ospo-alliance.org/ggi/)\n\n'
                'For more information please see the official project home page at https://ospo-alliance.org/'
            )
            print(f"\nNew description:\n<<<---------\n{desc}\n--------->>>\n")

            # Update the repository description
            repo.edit(description=desc)
        else:
            print("Cannot find environment variable 'CI_PAGES_URL', skipping.")

    #
    # Create labels & activities
    #
    if args.opt_activities:

        # Create labels.
        print("\n# Manage labels")

        # Create role labels if needed
        print("\n Roles labels")
        for label, colour in metadata['roles'].items():
            create_github_label(repo, label, {'name': label, 'color': colour})

        # Create labels for activity tracking
        print("\n Progress labels")
        for name, label in params['progress_labels'].items():
            create_github_label(repo, label, {'name': label, 'color': 'ed9121'})

        # Create goal labels if needed
        print("\n Goal labels")
        for goal in metadata['goals']:
            create_github_label(repo, goal['name'],
                                {'name': goal['name'], 'color': goal['colour']})

        # Create issues with their associated labels.
        print("\n# Create activities.")
        # First test the existence of Activities Issues:
        #   if at least one Issue is found bearing one Goal label,
        #   consider that all Issues exist and do not add any.
        open_issues = repo.get_issues(state='open')
        if open_issues.totalCount > 0:
            # TODO better check for issues with labels
            print("Ignore, Issues already exist")
        else:
            for activity in metadata['activities']:
                progress_label = ''
                if args.opt_random:
                    # Choix aléatoire parmi les étiquettes de progression valides
                    progress_idx = random.choice(list(params['progress_labels']) + ['none'])
                    if progress_idx != 'none':
                        progress_label = params['progress_labels'][progress_idx]
                labels = [activity['goal']] + activity['roles']
                if progress_label != '':
                    labels = labels + [progress_label]

                print(f"  - Issue: {activity['name']:<60} Labels: {labels}")
                # Création de l'issue
                issue = repo.create_issue(
                    title=activity['name'],
                    body=extract_sections(args, init_scorecard, activity),
                    labels=labels
                )

    #
    # Create Goals board
    # TODO : check why : 410 {"message": "Projects are disabled for this repository"
    if args.opt_board:
        print(f"\n# Create Goals board: {ggi_board_name}")

        # Check if the project already exists
        projects = repo.get_projects()
        project_exists = False
        for project in projects:
            if project.name == ggi_board_name:
                project_exists = True
                break

        if project_exists:
            print(" Ignore, Project already exists")
        else:
            # Create a new project
            project = repo.create_project(name=ggi_board_name)
            print(f"Project '{ggi_board_name}' created.")

            print('\n# Create Goals board columns.')
            # First, ensure all required labels exist in the repo
            existing_labels = {label.name: label for label in repo.get_labels()}
            goal_columns = []
            for g in metadata['goals']:
                if g['name'] in existing_labels:
                    goal_columns.append(existing_labels[g['name']])

            # Then, create columns in GitHub project
            for goal_label in goal_columns:
                print(f"  - Create column for {goal_label.name}")
                column = project.create_column(name=goal_label.name)



    # Close the connection.
    g.close()

if __name__ == '__main__':
    main()
