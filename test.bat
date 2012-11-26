@echo off
hg init test
cd test
echo a x>.hgbranches
echo b y>>.hgbranches
echo >d
hg add d
hg ci -m"default branch"
hg branch a
echo >a
hg add a
hg ci -m"branch a, will be renamed to x"
hg branch b
echo >b
hg add b
hg ci -m"branch b, will be renamed to y"
echo.
echo Before .hgbranches:
hg log --template "Branch {branch}: {desc}\n"
hg add .hgbranches
hg ci -m"added .hgbranches"
echo.
echo After .hgbranches:
hg log --template "Branch {branch}: {desc}\n"
echo Current branch is y, renamed from b:
hg branch
echo.
hg update x
echo >x
hg add x
hg ci -m"branch x, was a"
hg update default
echo >d2
hg add d2
hg ci -m"default branch"
echo.
echo Using a renamed branch:
hg log --template "Branch {branch}: {desc}\n"
echo.
echo Attempting to create existing branch with old name:
hg branch b
echo Attempting to create existing branch with new name:
hg branch y
echo.
echo Updating to pre-.hgbranches
hg update 2 -C
hg log --template "Branch {branch}: {desc}\n"
hg update x
echo Current branch, after swithcing to x, renamed from a:
hg branch
echo >c
hg branch c
hg add c
hg ci -m"branch c, will be locally renamed to z"
echo.
echo Before local .hgbranches:
hg log --template "Branch {branch}: {desc}\n"
echo.
echo c z>.hg\.hgbranches
echo After local .hgbranches:
hg log --template "Branch {branch}: {desc}\n"
echo Current branch is z, was renamed from c:
hg branch
echo.
echo Deleting local .hgbranches:
del .hg\.hgbranches
hg log --template "Branch {branch}: {desc}\n"
echo Current branch is c, was renamed to z:
hg branch
cd ..
rd test /s/q