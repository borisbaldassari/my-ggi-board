

# Welcome

This is the home of your own Good Governance Initiative tracking board.

Once set up (see below), you can find the published website at [GGI_PAGES_URL].

The goal is
- to fork the [my-ggi-board repository](https://gitlab.ow2.org/ggi/my-ggi-board) in your own GitLab space.
- fill the configuration file - including a GitLab token
- then run a script that will automatically create
  - appropriate labels
  - GitLab Issues that will stand for the GGI activities
  - an Issues Board for a clear overview of you current activities
  - a static website to share progress and current work

## Setup

### Fork the repository
Multiple options here: you may want, for example, to use the Import feature proposed by GitLab, or fork manually.

**Manually Fork**  
- Create an empty project on your target GitLab instance.
<img src="resources/setup_create-project.png" width="50%" height="50%">

- Clone the [my-ggi-board repository](https://gitlab.ow2.org/ggi/my-ggi-board) to your new project.

To do so, clone the my-ggi-board repository locally, and add the new project's reference to the remotes:
```
$ git clone --origin ow2-upstream https://gitlab.ow2.org/ggi/my-ggi-board.git
$ cd my-ggi-board
$ git remote add origin https://gitlab.com/<your-gitlab-space>/my-ggi-board.git
$ git push --set-upstream origin main
```

Your remotes should look like this:
```
$ git remote -v
origin  https://gitlab.com/<your-gitlab-space>/my-ggi-board.git (fetch)
origin  https://gitlab.com/<your-gitlab-space>/my-ggi-board.git (push)
ow2-upstream    https://gitlab.ow2.org/ggi/my-ggi-board.git (fetch)
ow2-upstream    https://gitlab.ow2.org/ggi/my-ggi-board.git (push)
```

**GitLab Import Project**  
Probably simpler, but be aware that all branches and tags from the upstream repository will be duplicated to you own repo.

In your own GitLab space:
- Create a new project
- Choose: _Import project_
- Choose: _Repository by URL_
- Enter `https://gitlab.ow2.org/ggi/my-ggi-board.git`

<img src="resources/setup_import-project.png" width="50%" height="50%">

### Create your GitLab token
Two possibilities to create your [GitLab token](https://docs.gitlab.com/ee/security/token_overview.html), depending on your GitLab environment: use a [Project access tokens](https://docs.gitlab.com/ee/user/project/settings/project_access_tokens.html#project-access-tokens) of a [Personal access tokens](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html)

**Project access tokens**  
Create an access token (Project settings > Access Tokens) with the `api` privilege and with role `Maintainer`. Remember it, you will never see it again.
<img src="resources/setup_project-token.png" width="50%" height="50%">

**Personal access tokens**  
In case the instance admin has disabled the _project_ access token, you can use an _personal_ access token, although we recommend creating a dedicated account for security purposes in that case. Go to Preferences > Access Tokens and create the token from there.

<img src="resources/setup_personal-token.png" width="50%" height="50%">

### Setup the environment
- Edit the file in `conf/ggi_deployment.json`, and set the variables `gitlab_url` (such as `https://gitlab.com`) and `gitlab_project` (such as `my-ggi-board`)
- Commit and publish that file to your reporisory
- Export the access token as an environment variable: `export GGI_GITLAB_TOKEN=xxxxxxx`.
- Create a CI/CD env variable: go to Settings > CI/CD > Variables, then add a variable named `GGI_GITLAB_TOKEN` and set the access token as the value. Make it `Protected` (cannot be used in non-protected branches) and `Masked` (will not be shown in Jobs logs.)
<img src="resources/setup_create-variable-1.png" width="50%" height="50%"> <img src="resources/setup_create-variable-2.png" width="50%" height="50%">
- Create a virtual env and install requirements.
```
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```
- Run the deploy script: `python3 scripts/ggi_deploy.py --activities --board`. That will:
  - Create labels, activities, board.
  - Setup the static website configuration.
  - Replace the URL in the README.
- Commit your changes: `git commit -m 'initial commit' -a`
- Push to the local gitlab instance on the `main` branch: `git push my-ggi`. That will:
  - Create a pipeline and gitlab page thanks to the `.gitlab_ci.yml` file.
  - Execute the ggi_update_website script, updating the website's content.
  - Publish the gitlab page.

## Notes

* Prerequisites for ptyhon are registered in `requirements.txt`. You are encouraged to create a virtual environment to execute the scripts, althought it is not required.
* GitLab CE doesn't allow to create Boards through the API.


## Testing

The `ggi_test_scenario.py` script takes as argument a GitLab instance URL and a project ID, executes the creation scripts and then checks that everything is in its right place.
