

# Welcome

This the home is your own Good Governance Initiative.

Once set up (see below), you can find the published website at [GGI_PAGES_URL].


## Setup

1. Create a new, empty project in a GitLab instance.

2. Clone the [my-ggi-board repository](https://gitlab.ow2.org/ggi/my-ggi-board) to your new project.

To do so, clone the my-ggi-board repository locally, and add the new project's reference to the remotes:
```
git clone https://gitlab.ow2.org/ggi/my-ggi-board
git remote add my-ggi git@gitlab.com:bbaldassari/my-ggi.git
```

3. Create an access token (Project settings > Access Tokens) with the `api` privilege and with role `Maintainer`. Remember it, you will never see it again.
  - In case the instance admin has disabled the _project_ access token, you can use an _account_ access token, although we recommend creating a dedicated account for security purposes in that case. Go to Preferences > Access Tokens and create the token from there.

4. Edit the file in `conf/ggi_deployment.json`, and set the variables `gitlab_url` and `gitlab_project`.
Export the access token as an environment variable: `export GGI_GITLAB_TOKEN=xxxxxxx`.

5. Create a CI/CD env variable: go to Settings > CI/CD > Variables, then add a variable named `GGI_GITLAB_TOKEN` and set the access token as the value. Make it `Protected` and `Masked`.

6. Create a virtual env and install requirements.
```
python -m venv env
source env/bin/activate
pip install -r requirements.txt
```

7. Run the deploy script: `python3 scripts/ggi_deploy.py --activities --board`. That will:
  - Create labels, activities, board.
  - Setup the static website configuration.
  - Replace the URL in the README.

7. Commit your changes: `git commit -m 'initial commit' -a`.

9. Push to the local gitlab instance on the `main` branch: `git push my-ggi`. That will:
  - Create a pipeline and gitlab page thanks to the `.gitlab_ci.yml` file.
  - Execute the ggi_update_website script, updating the website's content.
  - Publish the gitlab page.

## Notes

* Prerequisites for ptyhon are registered in `requirements.txt`. You are encouraged to create a virtual environment to execute the scripts, althought it is not required.
* GitLab CE doesn't allow to create Boards through the API.


## Structure

```
conf/
├── ggi_activities_metadata.json
└── ggi_deployment.json
scripts/
└── ggi_deploy.py
README.md
```


## Testing

The ggi_test_scenario.py script takes as argument a GitLab instance URL and a project ID, executes the creation scripts and then checks that everything is in its right place.
