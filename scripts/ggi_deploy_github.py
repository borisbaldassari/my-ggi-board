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
import time
import urllib.parse
import requests

from ggi_deploy import *
from github import Github, GithubException
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

def get_owner_id(owner, gh_token):
    url = 'https://api.github.com/graphql'

    headers = {
        'Authorization': f'bearer {gh_token}',
        'Content-Type': 'application/json'
    }

    query = """
        query ($owner: String!) {
          user(login: $owner) {
            id
            next_global_id
          }
          organization(login: $owner) {
            id
            next_global_id
          }
        }
    """

    variables = {"owner": owner}
    response = requests.post(url, headers=headers, json={'query': query, 'variables': variables})

    if response.status_code == 200:
        data = response.json()
        print("Réponse GitHub pour owner ID:", data)  # DEBUG

        # Vérifier si c'est un utilisateur
        if data.get('data', {}).get('user'):
            user_data = data['data']['user']
            return user_data.get('next_global_id', user_data['id'])  # Utilise next_global_id si disponible

        # Vérifier si c'est une organisation
        elif data.get('data', {}).get('organization'):
            org_data = data['data']['organization']
            return org_data.get('next_global_id', org_data['id'])  # Utilise next_global_id si disponible

        else:
            raise Exception("Impossible de récupérer l'ID du propriétaire.")

    else:
        raise Exception(f"Query failed with status {response.status_code}: {response.text}")

def setup_github(metadata, params: dict, init_scorecard, args: dict):
    """
    Executes the following deployment sequence on a GitHub instance:
    * Reads github-specific variables.
    * Connect to GitHub
    * Create labels & activities
    * Create Goals board
    * Create schedule for pipeline
    """

    # Get conf: Token
    if 'GGI_GITHUB_TOKEN' in os.environ:
        print("- Using token from env var 'GGI_GITHUB_TOKEN'")
        params['github_token'] = os.environ['GGI_GITHUB_TOKEN']
    else:
        print("- Cannot find env var GGI_GITHUB_TOKEN. Please set it and re-run me.")
        exit(1)
    auth = Auth.Token(params['github_token'])

    # Get conf: URL
    public_github="https://github.com"
    if 'GGI_GITHUB_URL' in os.environ:
        params['github_url'] = os.environ['GGI_GITHUB_URL']
        print("- Using URL from env var 'GGI_GITHUB_URL'")
    elif 'github_url' in params and params['github_url'] != None:
        print("- Using URL from configuration file")
    else:
        params['github_url'] = public_github
        print("- Using default public URL")

    if params['github_url'].startswith(public_github):
        # Public Web Github
        print("- Using public GitHub instance.")
        g = Github(auth=auth)
    else:
        print(f"- Using GitHub on-premise host {params['github_url']} ")
        # Github Enterprise with custom hostname
        params['github_url'] = f"{params['github_url']}/api/v3"
        g = Github(auth=auth, base_url=params['github_url'])

    # Gett conf: Project
    if 'GGI_GITHUB_PROJECT' in os.environ:
        params['github_project'] = os.environ['GGI_GITHUB_PROJECT']
        print("- Using Project from env var 'GGI_GITHUB_PROJECT'")
    elif 'github_project' in params and params['github_project'] != None:
        print(f"- Using Project from configuration file")
    else:
        print("I need a project (org + repo), e.g. ospo-alliance/" +
              "my-ggi-board. Exiting.")
        exit(1)


    params['github_repo_url'] = urllib.parse.urljoin(params['github_url'], params['github_project'])
    params['github_activities_url'] = params['github_repo_url'] + '/projects'

    print("Configuration:")
    print("URL     : " + params['github_url'])
    print("Project : " + params['github_project'])
    print("Full URL: " + params['github_repo_url'])


    headers = {
        "Authorization": f"Bearer {params['github_token']}",
        "Accept": "application/vnd.github.inertia-preview+json"  # Needed for project board access
    }

    # Connecting to the GitHub instance.

    print(f"\n# Retrieving project from GitHub at {params['github_repo_url']}.")
    repo = g.get_repo(params['github_project'])

    # Update current project description with Website URL
    if args.opt_projdesc:
        print("\n# Update Project description")
        ggi_activities_url = params['github_activities_url']

        repo_fullname = os.getenv("GITHUB_REPOSITORY", "unknown/repo")  # "username/repository-name"
        repo_owner = os.getenv("GITHUB_REPOSITORY_OWNER", "unknown")  # "username"
        repo_name = repo_fullname.split("/")[-1]
        github_pages_url = f"https://{repo_owner}.github.io/{repo_name}/"

        desc = (
            'Here you will find your dashboard: ' + github_pages_url + ' and the issues board: ' + ggi_activities_url + ' with all activities describing the local GGI'
        )
        print(f"nNew description:\n<<<---------\n{desc}\n--------->>>\n")

        # Update the repository description
        repo.edit(description=desc, homepage="https://ospo-alliance.org/")

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
            print("Ignore, Issues already exist")
        else:
            for activity in metadata['activities']:
                progress_label = params['progress_labels']['not_started']
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
                try:
                    issue = repo.create_issue(
                        title=activity['name'],
                        body=extract_sections(args, init_scorecard, activity),
                        labels=labels
                    )
                    time.sleep(2)
                except GithubException as e:
                    print(f"Status: {e.status}, Data: {e.data}")

    # Create Goals board
    if args.opt_board:
        create_project_graphql(params)

    # Close the connection.
    g.close()

def create_project_graphql(params):
    print(f"\n# Create Goals board: {ggi_board_name}")

    access_token = params['github_token']
    headers = {'Authorization': f'bearer {access_token}'}
    graphql_url = 'https://api.github.com/graphql'

    repo_infos = params['github_project'].split("/")
    repo_owner = repo_infos[0]
    repo_name = repo_infos[1]

    # Query to check for an existing project
    query = """
        query ($repo_owner: String!, $repo_name: String!, $project_name: String!) {
          repository(owner: $repo_owner, name: $repo_name) {
            projects(search: $project_name, first: 10) {
              nodes {
                id
                name
              }
            }
          }
        }
        """
    variables = {
        "repo_owner": repo_owner,
        "repo_name": repo_name,
        "project_name": "Goals Project"
    }
    response = requests.post(graphql_url, json={'query': query, 'variables': variables}, headers=headers)
    projects_data = json.loads(response.text)

    # Check if project exists and find its ID
    project_id = None
    for project in projects_data['data']['repository']['projects']['nodes']:
        if project['name'] == variables['project_name']:
            project_id = project['id']
            break

    # If the project does not exist, create it
    if not project_id:
        mutation_create_project = """
            mutation ($title: String!, $owner_id: ID!) {
              createProjectV2(input: {title: $title, ownerId: $owner_id}) {
                projectV2 {
                  id
                  title
                }
              }
            }
        """

        # Fetching the repository ID for ownerId in mutation
        repo_id_query = """
            query ($repo_owner: String!, $repo_name: String!) {
              repository(owner: $repo_owner, name: $repo_name) {
                id
              }
            }
            """

        variables = {
            "repo_owner": repo_owner,
            "repo_name": repo_name
        }
        repo_response = requests.post(graphql_url, json={'query': repo_id_query, 'variables': variables}, headers=headers)
        repo_id = json.loads(repo_response.text)['data']['repository']['id']
        print("repo ID = " + repo_id)

        owner_id_query = """
            query ($repo_owner: String!) {
              user(login: $repo_owner) {
                id
              }
              organization(login: $repo_owner) {
                id
              }
            }
        """

        variables = {"repo_owner": repo_owner}
        owner_response = requests.post(graphql_url, json={'query': owner_id_query, 'variables': variables},
                                       headers=headers)
        owner_data = owner_response.json()

        print("Réponse GitHub pour owner ID:", owner_data)  # Vérification

        # Vérifie si c'est un utilisateur ou une organisation
        if owner_data.get('data', {}).get('user'):
            owner_id = owner_data['data']['user']['id']
        elif owner_data.get('data', {}).get('organization'):
            owner_id = owner_data['data']['organization']['id']
        else:
            raise Exception("Impossible de récupérer l'ID du propriétaire.")

        print(f"Owner ID récupéré : {owner_id}")  # Vérifie que cet ID est correct


        # Creating the project
        create_variables = {
            "title": "Goals Project",
            "owner_id": owner_id
        }


        project_response = requests.post(graphql_url,
                                         json={'query': mutation_create_project, 'variables': create_variables},
                                         headers=headers)
        project_data = json.loads(project_response.text)
        # Print the entire response to inspect what GitHub API returned
        print("GitHub API response:", project_data)

        # Check if 'errors' key is present in the response
        if 'errors' in project_data:
            print("Errors returned from the GitHub API:", project_data['errors'])
        else:
            project_id = project_data['data']['createProjectV2']['projectV2']['id']
            print(f"Created new project: {project_data['data']['createProjectV2']['projectV2']['title']} (ID: {project_data['data']['createProjectV2']['projectV2']['id']})")

            # Définition des valeurs du champ "Single Select"
            options = [
                {"name": "Culture Goal", "description": "A culture-related goal", "color": "GREEN"},
                {"name": "Engagement Goal", "description": "An engagement-related goal", "color": "GREEN"},
                {"name": "Strategy Goal", "description": "A strategy-related goal", "color": "GREEN"},
                {"name": "Trust Goal", "description": "A trust-related goal", "color": "GREEN"},
                {"name": "Usage Goal", "description": "A usage-related goal", "color": "GREEN"}
            ]

            # Définition de la mutation GraphQL
            mutation_add_field = """
                mutation ($project_id: ID!, $name: String!, $options: [ProjectV2SingleSelectFieldOptionInput!]!) {
                  createProjectV2Field(input: { 
                    projectId: $project_id, 
                    name: $name, 
                    dataType: SINGLE_SELECT,
                    singleSelectOptions: $options
                  }) {
                    projectV2Field {
                      ... on ProjectV2SingleSelectField {
                        id
                        name
                        options {
                          id
                          name
                          description
                          color
                        }
                      }
                    }
                  }
                }
            """

            # Variables pour la mutation
            variables = {
                "project_id": project_id,
                "name": "Goal Category",
                "options": options
            }

            # Exécution de la requête
            response = requests.post(graphql_url, json={"query": mutation_add_field, "variables": variables},
                                     headers=headers)
            data = response.json()

            # Vérification de la réponse
            print("Réponse GitHub:", json.dumps(data, indent=4))

            if "errors" in data:
                print("❌ Erreur:", data["errors"])
            else:
                print(f"✅ Champ créé: {data['data']['createProjectV2Field']['projectV2Field']['name']}")
                for option in data['data']['createProjectV2Field']['projectV2Field']['options']:
                    print(f"   - Option: {option['name']} (ID: {option['id']}, Color: {option['color']}, Description: {option['description']})")

            # 🔹 Correspondance labels → options du champ "Goal Category"
            goal_mapping = {
                "Culture Goal": "Culture Goal",
                "Engagement Goal": "Engagement Goal",
                "Strategy Goal": "Strategy Goal",
                "Trust Goal": "Trust Goal",
                "Usage Goal": "Usage Goal"
            }

            # # 🔹 Étape 1 : Récupérer les issues et leurs labels
            # query_issues = """
            #     query ($repo_owner: String!, $repo_name: String!) {
            #       repository(owner: $repo_owner, name: $repo_name) {
            #         issues(first: 25) {
            #           nodes {
            #             id
            #             title
            #             labels(first: 10) {
            #               nodes {
            #                 name
            #               }
            #             }
            #           }
            #         }
            #       }
            #     }
            # """
            #
            # variables = {"repo_owner": repo_owner, "repo_name": repo_name}
            # response = requests.post(graphql_url, json={"query": query_issues, "variables": variables}, headers=headers)
            # issues_data = response.json()
            #
            # issues = issues_data.get("data", {}).get("repository", {}).get("issues", {}).get("nodes", [])
            # print(f"🔹 {len(issues)} issues trouvées")
            #
            # # 🔹 Étape 2 : Ajouter chaque issue au projet et assigner le champ Goal Category
            # mutation_add_issue = """
            #     mutation ($project_id: ID!, $issue_id: ID!) {
            #       addProjectV2ItemById(input: {projectId: $project_id, contentId: $issue_id}) {
            #         item {
            #           id
            #         }
            #       }
            #     }
            # """
            #
            # # Récupérer l'ID du champ "Goal Category" et ses options
            # query_project_fields = """
            #     query ($project_id: ID!) {
            #       node(id: $project_id) {
            #         ... on ProjectV2 {
            #           fields(first: 20) {
            #             nodes {
            #               __typename
            #               ... on ProjectV2Field {
            #                 id
            #                 name
            #               }
            #               ... on ProjectV2SingleSelectField {
            #                 id
            #                 name
            #                 options {
            #                   id
            #                   name
            #                 }
            #               }
            #             }
            #           }
            #         }
            #       }
            #     }
            # """
            #
            # print(f"🔹 Vérification : Project ID utilisé = {project_id}")
            #
            # response = requests.post(graphql_url,
            #                          json={"query": query_project_fields, "variables": {"project_id": project_id}},
            #                          headers=headers)
            # fields_data = response.json()
            #
            # # Vérifier que "data" est présent
            # if "data" not in fields_data:
            #     print("❌ Erreur: La réponse de GitHub ne contient pas 'data'. Voici la réponse complète :")
            #     print(json.dumps(fields_data, indent=4))
            #     exit()
            #
            # goal_field = None
            # goal_options = {}
            #
            # for field in fields_data["data"]["node"]["fields"]["nodes"]:
            #     if field["__typename"] == "ProjectV2SingleSelectField" and field["name"] == "Goal Category":
            #         goal_field = field["id"]
            #         for option in field["options"]:
            #             goal_options[option["name"]] = option["id"]
            #
            # print("📌 Options disponibles pour 'Goal Category':", goal_options)
            #
            # if not goal_field:
            #     print("❌ Le champ 'Goal Category' n'a pas été trouvé dans le projet.")
            #     exit()
            # else:
            #     print(f"✅ Champ 'Goal Category' trouvé avec ID: {goal_field}")
            #
            # # 🔹 Étape 3 : Assigner la valeur correcte au champ "Goal Category"
            # mutation_update_field = """
            #     mutation ($project_id: ID!, $item_id: ID!, $field_id: ID!, $option_id: ID!) {
            #       updateProjectV2ItemFieldValue(input: {
            #         projectId: $project_id,
            #         itemId: $item_id,
            #         fieldId: $field_id,
            #         value: {singleSelectOptionId: $option_id}
            #       }) {
            #         projectV2Item {
            #           id
            #         }
            #       }
            #     }
            # """
            #
            # for issue in issues:
            #     issue_id = issue["id"]
            #     labels = [label["name"] for label in issue["labels"]["nodes"]]
            #
            #     # Déterminer l'option en fonction du label
            #     goal_option_id = None
            #     for label in labels:
            #         if label in goal_mapping:
            #             goal_option_name = goal_mapping[label]
            #             goal_option_id = goal_options.get(goal_option_name)
            #             break
            #
            #     # Ajouter l'issue au projet
            #     add_response = requests.post(graphql_url, json={"query": mutation_add_issue,
            #                                                     "variables": {"project_id": project_id,
            #                                                                   "issue_id": issue_id}}, headers=headers)
            #     add_data = add_response.json()
            #
            #     if "errors" in add_data:
            #         print("❌ Erreur ajout issue:", add_data["errors"])
            #         continue
            #
            #     item_id = add_data["data"]["addProjectV2ItemById"]["item"]["id"]
            #
            #     # Vérifier que l'option est trouvée
            #     if not goal_option_id:
            #         print(f"⚠️ Aucun ID d'option trouvé pour l'issue '{issue['title']}', vérifie les labels.")
            #         continue  # Passe à l'issue suivante
            #
            #     # Mise à jour du champ
            #     print(f"🔹 Mise à jour de l'issue {issue_id} avec {goal_option_id} pour le champ {goal_field}")
            #     print(f"🛠 Vérification: Type de goal_option_id = {type(goal_option_id)}, valeur = {goal_option_id}")
            #
            #     update_response = requests.post(graphql_url, json={"query": mutation_update_field,
            #                                                        "variables": {"project_id": project_id,
            #                                                                      "item_id": item_id,
            #                                                                      "field_id": goal_field,
            #                                                                      "option_id": goal_option_id}},
            #                                     headers=headers)
            #     update_data = update_response.json()
            #
            #     print("Réponse GitHub mise à jour:", json.dumps(update_data, indent=4))
            #
            #     if "errors" in update_data:
            #         print(f"❌ Erreur mise à jour du champ pour l'issue '{issue['title']}':", update_data["errors"])
            #     else:
            #         print(f"✅ Assigné {goal_option_name} à l'issue '{issue['title']}'")


def get_repo_id(headers):
    graphql_url = 'https://api.github.com/graphql'

    # GraphQL query to get repository owner ID
    query = """
    query ($repo_owner: String!, $repo_name: String!) {
      repository(owner: $repo_owner, name: $repo_name) {
        owner {
          id
          login
          __typename
        }
      }
    }
    """

    # Variables for the query
    variables = {
        "repo_owner": "Sebastienlejeune",  # e.g., 'octocat'
        "repo_name": "my-ggi-board"  # e.g., 'Hello-World'
    }

    # Make the request to GitHub GraphQL API
    response = requests.post(graphql_url, json={'query': query, 'variables': variables}, headers=headers)
    response_data = json.loads(response.text)
    return response_data


if __name__ == '__main__':
    main()
