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

def retrieve_gitlab_issues(params: dict):
    """
    Retrieve issues from GitLab instance.
    """
    print(f"\n# Connection to GitLab at {params['GGI_GITLAB_URL']} " +
          f"- {params['GGI_GITLAB_PROJECT']}.")
    gl = gitlab.Gitlab(url=params['GGI_GITLAB_URL'],
                       per_page=50,
                       private_token=params['GGI_GITLAB_TOKEN'])
    project = gl.projects.get(params['GGI_GITLAB_PROJECT'])

    print("# Fetching issues..")
    gl_issues = project.issues.list(state='opened', all=True)
    print(f"  Found {len(gl_issues)} issues.")

    # Define columns for recorded dataframes.
    issues = []

    tasks = []

    hist = []

    count = 1
    workflow = {}
    tasks = []

    for i in gl_issues:
        desc = i.description
        paragraphs = desc.split('\n\n')
        lines = desc.split('\n')
        a_id, description, workflow, a_tasks = extract_workflow(desc)
        for t in a_tasks:
            tasks.append([a_id,
                          'completed' if t['is_completed'] else 'open',
                          t['task']])
        short_desc = '\n'.join(description)
        tasks_total = len(a_tasks)
        tasks_done = len( [ t for t in a_tasks if t['is_completed'] ] )
        issues.append([i.iid, a_id, i.state, i.title, ','.join(i.labels),
                       i.updated_at, i.web_url, short_desc, workflow,
                       tasks_total, tasks_done])

        # Retrieve information about labels.
        for n in i.resourcelabelevents.list():
            event = i.resourcelabelevents.get(n.id)
            n_type = 'label'
            label = n.label['name'] if n.label else ''
            n_action = f"{n.action} {label}"
            user = n.user['username'] if n.user else 'unknown'
            line = [n.created_at, i.iid,
                    n.id, n_type, user, 
                    n_action, i.web_url]
            hist.append(line)
            
        print(f"- {i.iid} - {a_id} - {i.title} - {i.web_url} - {i.updated_at}.")
        
        # Remove these lines when dev/debug is over
        if count == 30:
            break
        else:
            count += 1
