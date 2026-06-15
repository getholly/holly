#!/bin/sh
# Git askpass helper: returns the token in GIT_PASSWORD for HTTPS auth so the
# credential is never written into a repo's .git/config or command line.
echo "$GIT_PASSWORD"
