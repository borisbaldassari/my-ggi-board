

## Usage

1. Create a new, empty project in a GitLab instance.

2. Clone the [my-ggi-board repository](https://gitlab.ow2.org/ggi/my-ggi-board) to your new project.

To do so, clone the my-ggi-board repository locally, add the new project's reference to the remotes, and push it to the new remote:
```
git clone https://gitlab.ow2.org/ggi/my-ggi-board
git remote add my-ggi git@gitlab.com:bbaldassari/my-ggi.git
git push my-ggi
```

Example:
```
boris@kadath:~/Projects/my-ggi-board$ git remote -v
my-ggi	git@gitlab.com:bbaldassari/my-ggi.git (fetch)
my-ggi	git@gitlab.com:bbaldassari/my-ggi.git (push)
origin	https://gitlab.ow2.org/ggi/my-ggi-board (fetch)
origin	https://gitlab.ow2.org/ggi/my-ggi-board (push)
boris@kadath:~/Projects/my-ggi-board$ git push my-ggi
Énumération des objets: 186, fait.
Décompte des objets: 100% (186/186), fait.
Compression par delta en utilisant jusqu'à 8 fils d'exécution
Compression des objets: 100% (144/144), fait.
Écriture des objets: 100% (186/186), 160.42 Kio | 26.74 Mio/s, fait.
Total 186 (delta 17), réutilisés 182 (delta 17), réutilisés du pack 0
remote: Resolving deltas: 100% (17/17), done.
To gitlab.com:bbaldassari/my-ggi.git
 * [new branch]      main -> main
boris@kadath:~/Projects/my-ggi-board$
```

3. Create an access token (Project settings > Access Tokens) with the `api` privilege and with role `Maintainer`.

4. Edit the file in `conf/ggi_deployment.json`, and set the variables `gitlab_url`, `gitlab_project`, `gitlab_token`.

5. Run the deploy script: `python3 scripts/ggi_deploy.py --activities --board`.


## Notes

* Python prerequisites: `python-gitlab`.
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
