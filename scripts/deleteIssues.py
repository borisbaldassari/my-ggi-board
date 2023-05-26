import gitlab
import os

access_token = "" # os.getenv("GGI_GITLAB_TOKEN")
project_id = 2135
# author_username = 'example.user'

gl = gitlab.Gitlab(url='https://gitlab.ow2.org/', private_token=access_token)
project = gl.projects.get(id=project_id)
issues = project.issues.list(iterator=True)

for issue in issues:
    # if issue.author['username'] == author_username:
    issue.delete()
