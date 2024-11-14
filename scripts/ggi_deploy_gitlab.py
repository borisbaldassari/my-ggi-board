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

import gitlab

from ggi_deploy import *


def main():
    """
    Main GITLAB.
    """
    args = parse_args()

    print("* Using GitLab backend.")
    metadata, params, init_scorecard = retrieve_env()
    setup_gitlab(metadata, params, init_scorecard, args)
    
    print("\nDone.")


def create_gitlab_label(project, existing_labels, new_label, label_args):
    """
    Creates a set of labels in the GitLab project.
    """
    if new_label in existing_labels:
        print(f" Ignore label: {new_label}")
    else:
        print(f" Create label: {new_label}")
        project.labels.create(label_args)


def setup_gitlab(metadata, params: dict, init_scorecard, args: dict):
    """
    Executes the following deployment sequence on a GitLab instance:
    * Reads gitlab-specific variables.
    * Connect to GitLab
    * Create labels & activities
    * Create Goals board
    * Create schedule for pipeline
    """
    if 'CI_SERVER_URL' in os.environ:
        print("- Use GitLab URL from environment variable")
        params['GGI_GITLAB_URL'] = os.environ['CI_SERVER_URL']
    else:
        print("- Use GitLab URL from configuration file")
        params['GGI_GITLAB_URL'] = params['gitlab_url']
    print(params['GGI_GITLAB_URL'])
    
    if 'CI_PROJECT_PATH' in os.environ:
        print("- Use GitLab Project from environment variable")
        params['GGI_GITLAB_PROJECT'] = os.environ['CI_PROJECT_PATH']
    else:
        print("- Use GitLab URL from configuration file")
        params['GGI_GITLAB_PROJECT'] = params['gitlab_project']
    print(params['GGI_GITLAB_PROJECT'])

    # if 'CI_PAGES_URL' in os.environ:
    #     print("- Using GGI_PAGES_URL from environment variable.")
    #     params['CI_PAGES_URL'] = os.environ['CI_PAGES_URL']
    # else:
    #     print("- Cannot find an env var for GGI_PAGES_URL. Computing it from conf.")
    #     pieces = tldextract.extract(params['GGI_GITLAB_URL'])
    #     params['CI_PAGES_URL'] = 'https://' + params['GGI_GITLAB_PROJECT'].split('/')[0] + \
    #         "." + pieces.domain + ".io/" + params['GGI_GITLAB_PROJECT'].split('/')[-1]

    if 'GGI_GITLAB_TOKEN' in os.environ:
        print("- Using ggi_gitlab_token from env var.")
        params['GGI_GITLAB_TOKEN'] = os.environ['GGI_GITLAB_TOKEN']
    else:
        print("- Cannot find env var GGI_GITLAB_TOKEN. Please set it and re-run me.")
        exit(1)

    params['GGI_URL'] = urllib.parse.urljoin(params['GGI_GITLAB_URL'], params['GGI_GITLAB_PROJECT'])
    params['GGI_ACTIVITIES_URL'] = os.path.join(params['GGI_URL'] + '/', '-/boards')
    
    print(f"\n# Connection to GitLab at {params['GGI_GITLAB_URL']} " +
          f"- {params['GGI_GITLAB_PROJECT']}.")
    gl = gitlab.Gitlab(url=params['GGI_GITLAB_URL'],
                       per_page=50,
                       private_token=params['GGI_GITLAB_TOKEN'])
    project = gl.projects.get(params['GGI_GITLAB_PROJECT'])

    # Update current project description with Website URL
    if args.opt_projdesc:
        print("\n# Update Project description")
        if 'CI_PAGES_URL' in params:
            ggi_activities_url = params['GGI_ACTIVITIES_URL']
            ggi_handbook_version = metadata["handbook_version"]
            ggi_pages_url = params['CI_PAGES_URL']
            desc = (
                'Your own Good Governance Initiative project.\n\n'
                'Here you will find '
                f'[**your dashboard**]({ggi_pages_url})\n'
                f'and the [**GitLab Board**]({ggi_activities_url}) with all activities describing the local GGI '
                f'deployment, based on the version {ggi_handbook_version} of the [GGI handbook]('
                f'https://ospo-alliance.org/ggi/)\n\n'
                'For more information please see the official project home page at https://ospo-alliance.org/'
            )
            print(f"\nNew description:\n<<<---------\n{desc}\n--------->>>\n")

            project.description = desc
            project.save()
        else:
            print("Cannot find environment variable 'CI_PAGES_URL', skipping.")

    #
    # Create labels & activities
    #
    if args.opt_activities:

        print("\n# Manage labels")
        existing_labels = [i.name for i in project.labels.list()]

        # Create role labels if needed
        print("\n Roles labels")
        for label, colour in metadata['roles'].items():
            create_gitlab_label(project, existing_labels, label, {'name': label, 'color': colour})

        # Create labels for activity tracking
        print("\n Progress labels")
        for name, label in params['progress_labels'].items():
            create_gitlab_label(project, existing_labels, label, {'name': label, 'color': '#ed9121'})

        # Create goal labels if needed
        print("\n Goal labels")
        for goal in metadata['goals']:
            create_gitlab_label(project, existing_labels, goal['name'],
                         {'name': goal['name'], 'color': goal['colour']})

        # # Read the custom scorecard init file.
        # print(f"\n# Reading scorecard init file from {init_scorecard_file}.")
        # with open(init_scorecard_file, 'r', encoding='utf-8') as f:
        #     init_scorecard = f.readlines()
    
        # Create issues with their associated labels.
        print("\n# Create activities.")
        # First test the existence of Activities Issues:
        #   if at least one Issue is found bearing one Goal label,
        #   consider that all Issues exist and do not add any.
        issues_test = project.issues.list(state='opened')
        if len(issues_test) > 0:
            print(" Ignore, Issues already exist")
        else:
            for activity in metadata['activities']:
                progress_label = ''
                if args.opt_random:
                    # randomly choose among valid progress labels
                    # + artificially introduce an extra option for no progress label
                    progress_idx = random.choice(list(params['progress_labels']) + ['none'])
                    if progress_idx != 'none':
                        progress_label = params['progress_labels'][progress_idx]
                labels = \
                    [activity['goal']] + \
                    activity['roles'] + \
                    [progress_label]
                print(f"  - Issue: {activity['name']:<60} Labels: {labels}")
                ret = project.issues.create({'title': activity['name'],
                                             'description': extract_sections(args, init_scorecard, activity),
                                             'labels': labels})

    #
    # Create Goals board
    #
    if args.opt_board:
        print(f"\n# Create Goals board: {ggi_board_name}")
        boards_list=project.boards.list()
        board_exists=False
        for b in boards_list:
            if b.name == ggi_board_name:
                board_exists=True
                break
        if board_exists:
            print(" Ignore, Board already exists")
        else:
            board = project.boards.create({'name': ggi_board_name})
            print('\n# Create Goals board lists.')
            # First build an ordered list of goals
            goal_lists = []
            for g in metadata['goals']:
                for l in project.labels.list():
                    if l.name == g['name']:
                        goal_lists.append(l)
                        break
        
            # Then create the lists in gitlab
            for goal_label in goal_lists:
                print(f"  - Create list for {goal_label.name}")
                b_list = board.lists.create({'label_id': goal_label.id})

    # Create a scheduled pipeline trigger, if none exist yet.
    if args.opt_schedulepipeline:
        print(f"\n# Schedule nightly pipeline to refresh the Dashboard")
        nb_pipelines=len(project.pipelineschedules.list())
        if nb_pipelines > 0:
            print(f" Ignore, already {nb_pipelines} scheduled pipeline(s)")
        else:
            sched = project.pipelineschedules.create({
                'ref': 'main',
                'description': 'Nightly Update',
                'cron': '0 3 * * *'})
            print(f" Pipeline created: '{sched.description}'")




if __name__ == '__main__':    
    main()
