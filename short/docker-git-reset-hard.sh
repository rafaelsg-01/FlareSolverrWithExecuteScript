#!/bin/bash
cd $HOME/content-proxy-web || true

echo "Git Reset Hard (Update Local Force) rafaelsg-01/FlareSolverrWithExecuteScript..."

ggit fetch --all
git reset --hard origin/master

echo "Git Reset Hard (Update Local Force) atualizado."
