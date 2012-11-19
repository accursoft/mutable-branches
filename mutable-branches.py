"""Rename named branches.

To start renaming branches, create a file called .hgbranches in the root of the working directory.
Each line in .hgbranches consists of a space-delimited pair such as oldBranch newBranch.
If the branch name contains spaces, it should be quoted.
Only the most recently checked in version of .hgbranches is used.
"""

testedwith = '2.3 2.4'
buglink = 'http://code.accursoft.com/mutable-branches/issues'