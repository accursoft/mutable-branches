"""Rename named branches.

To start renaming branches, create a file called .hgbranches in the root of the working directory.
Each line in .hgbranches consists of a space-delimited pair such as oldBranch newBranch.
If the branch name contains spaces, it should be quoted.

Mutable-branches merges the most recent .hgbranches from each head in the repository.
In case of conflict, the most recent head wins.
"""

import os, shlex
from mercurial import extensions, commands, changelog, localrepo

def uisetup(ui):
    extensions.wrapcommand(commands.table, 'branch', branch_wrapper)

def reposetup(ui, repo):
    #only interested in local repositories
    if not isinstance(repo, localrepo.localrepository): return
    
    #add .hgbranches from each head
    #conflicting renames from newer heads overwrite older heads
    global _hgbranches
    _hgbranches = {}
    for head in reversed(repo.heads()):
        if '.hgbranches' in repo[head]:
            for line in repo[head]['.hgbranches'].data().splitlines():
                items = shlex.split(line)
                _hgbranches[items[0]] = items[1]

    #build a list of changes from the last run
    if repo.vfs.exists("cache/hgbranches"):
        changes = {}
        previous = eval(repo.vfs("cache/hgbranches").read())
        for old, new in hgbranches.items():
            if old in previous:
                #has a previous renaming changed?
                if previous[old] != new: changes[previous[old]] = new
            else:
                #new renaming
                changes[old] = new
    else:
        changes = _hgbranches

    #update dirstate
    dirstate = repo.dirstate
    branch = dirstate.branch()
    if branch in changes:
        dirstate.setbranch(changes[branch])

    #delete the old branch cache
    if repo.opener.exists("cache/branchheads"):
        os.remove(repo.opener.join("cache/branchheads"))

    #wrap changelog methods
    extensions.wrapfunction(changelog.changelog, 'add', add_wrapper)
    extensions.wrapfunction(changelog.changelog, 'read', read_wrapper)

def branch_wrapper(orig, ui, *args, **kwargs):
    """Remove the "branches are permanent and global" warning from branch's output."""
    ui.pushbuffer()
    ret = orig(ui, *args, **kwargs)
    lines = ui.popbuffer().splitlines(True)
    if lines[-1].startswith("(branches are permanent and global"): lines.pop()
    ui.write(''.join(lines))
    return ret

def add_wrapper(orig, ui, *args, **kwargs):
    branch = args[8]['branch']
    #map renamed branch to canonical name
    for old, new in _hgbranches.items():
        if branch == new:
            args[8]['branch'] = old
            break
    return orig(ui, *args, **kwargs)

def read_wrapper(orig, ui, *args, **kwargs):
    ret = orig(ui, *args, **kwargs)
    branch = ret[5]['branch']
    #rename branch
    if branch in _hgbranches: ret[5]['branch'] = _hgbranches[branch]
    return ret

testedwith = '2.3 2.4'
buglink = 'http://code.accursoft.com/mutable-branches/issues'