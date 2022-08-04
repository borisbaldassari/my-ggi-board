

## Usage

1. Create a new, empty project in a GitLab instance. 
2. Create an access token (Project settings > Access Tokens) with the `api` privilege and with role `Maintainer`.
3. Edit the file in `conf/ggi_deployment.json`, and set the variables `gitlab_url`, `gitlab_project`, `gitlab_token`.
4. Run the deploy script: `python3 scripts/ggi_deploy.py --activities --board`.


## Notes

* Prerequisites: `python-gitlab`.
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
