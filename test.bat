@echo off
hg init test
copy test.hgbranches test\.hgbranches >nul
cd test
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
cd ..
rd test /s/q