echo "you may need to git submodule add git@github.com:lingster/aiagents.git"
docker build -t hilly:latest .

#
#ENTRYPOINT ["/dockerstartup/kasm_default_profile.sh" "/dockerstartup/vnc_startup.sh" "/dockerstartup/kasm_startup.sh"]
#CMD ["--wait"]


