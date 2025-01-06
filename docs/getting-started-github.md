## GitHub deployment

### Fork the repository
Multiple options here: you may want, for example, to use the Import feature proposed by GitHub, or fork manually.

**GitHub Import Project**
Probably simpler, but be aware that all branches will be duplicated to you own repo.

In your own GitHub space:
- Create a new project
- Choose: _Import project_
- In 'The URL for your source repository' field, enter `https://gitlab.ow2.org/ggi/my-ggi-board.git`
- Choose the owner and the repository name
- Click on _Begin import_

    <img src="resources/setup_create-project_github.png" width="50%" height="50%">

**Manually Fork**

1. Create an empty project on your target GitHub instance.
1. Clone the [my-ggi-board repository](https://gitlab.ow2.org/ggi/my-ggi-board) to your new project.

To do so, clone the my-ggi-board repository locally, and add the new project's reference to the remotes:
```
$ git clone https://gitlab.ow2.org/ggi/my-ggi-board.git
$ git remote add my-ggi git@github.com:<your-GitHub-space>/my-ggi-board.git
$ git push my-ggi-board
```

### Create your GitHub token

**Personal access tokens**  
1. Go to Settings > Developer setting > Personal access tokens > Tokens (classic).
1. Click on 'Generate a new token' then 'Generate new token (classic)'
1. Name it 'my-ggi-board', choose an expiration and select scopes 'Repo' and 'Workflow'
1. Click on 'Generate token'

    <img src="resources/setup_personal-token_github.png" width="50%" height="50%">

### Setup the environment

1. Edit the file in `conf/ggi_deployment.json`, and set the variables `github_url` (such as `https://github.com`) and `github_project` (such as `my-ggi-board`)
1. Commit and publish that file to your repository
1. Export the access token as an environment variable: `export GGI_GITHUB_TOKEN=xxxxxxx`.
1. Go to repository Settings > General > Features and enable 'Issues' and 'Projects'. 
1. Create a GitHub Actions env variable: go to Settings > Secrets and Variables > Actions, then add a new repository secret named `GGI_GITHUB_TOKEN` and set the access token as the value. Click on 'Add secret'.

    <img src="resources/setup_create-variable_github.png" width="50%" height="50%"> 
   
1. Execute the GitHub action workflow called 'My GGI Deploy deployment' by clicking on 'Run the workflow' button. This will:
  - Create labels, activities and board.
  - Setup the static website configuration.
  - Replace the URL in the description.
  - Update the website's content.
  - Publish the result on GitHub pages.

    <img src="resources/setup_run-pipeline_github.png" width="50%" height="50%"> 