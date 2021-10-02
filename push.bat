@echo off
set UserName=mohsinjamal
set Name=awsbot
set Version="1.0.0"
if exist dist (
    del /F /S /Q dist
    rd /S /Q dist
)

if not exist .git (
    git init
    git config --global core.autocrlf true
    git config --global credential.helper store
    git remote add origin https://github.com/%UserName%/%Name%.git
)

git add --all
git commit -m "%Version%"
git push -u origin master
pause

#git remote add origin https://mohsinjamal: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@github.com/mohsinjamal/Main_control_system.git