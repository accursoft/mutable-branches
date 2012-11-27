@echo off
hg init test
cd test
echo "a a" "x.x">.hgbranches
echo "b,b" "y y">>.hgbranches
echo >d
hg add d
hg ci -m"default branch"
hg branch "a a"
echo >a
hg add a
hg ci -m"branch a a, will be renamed to x.x"
hg branch "b,b"
echo >b
hg add b
hg ci -m"branch b,b, will be renamed to y y"
echo.
echo Before .hgbranches:
hg log --template "Branch {branch}: {desc}\n"
hg add .hgbranches
hg ci -m"added .hgbranches"
echo.
echo After .hgbranches:
hg log --template "Branch {branch}: {desc}\n"
echo Current branch is y y, renamed from b,b:
hg branch
echo.
hg update "x.x"
echo >x
hg add x
hg ci -m"branch x.x, was a a"
hg update default
echo >d2
hg add d2
hg ci -m"default branch"
echo.
echo Using a renamed branch:
hg log --template "Branch {branch}: {desc}\n"
echo.
echo Attempting to create existing branch with old name:
hg branch "b,b"
echo Attempting to create existing branch with new name:
hg branch "y y"
echo.
echo Updating to pre-.hgbranches
hg update 2 -C
hg log --template "Branch {branch}: {desc}\n"
hg update "x.x"
echo Current branch is x.x, renamed from a a:
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