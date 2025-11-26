If error about google API NOT SET
To check current env variables:
gci env:

To set variables from env file:
.\EnvVarsFromDotEnv.ps1
(should see then all variables in terminal)

gci env:
Check enviroment vars have been set

Create super user:
uv run manage.py createsuperuser

Do migrations:
uv run manage.py migrate

if docker and githubme both running on port:5173 change in the aiagents repo
ARG USER_UID=1001
ARG USER_GID=1001

Should have opened:
aiagents - with data path linked to the repo ideally at llmrepo/githubme
githubme - run server
frontend - npm run dev or npm i to do installs
rest_mcp_client - running restmcpclient - python
