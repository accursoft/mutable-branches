"""Rename named branches.

To start renaming branches, create a file called .hgbranches in the root of the working directory.
Each line in .hgbranches consists of a space-delimited pair such as oldBranch newBranch.
If the branch name contains spaces, it should be quoted.
Renamings can be kept local by putting them in .hg/.hgbranches.

.. container:: verbose

    Mutable-branches merges the most recent .hgbranches from each head in the repository.
    In case of conflict, the most recent head wins. .hg/.hgbranches always overrides the repository .hgbranches.
"""

import os, shlex
from mercurial import extensions, commands, changelog, localrepo, util
from mercurial.node import hex

def uisetup(ui):
    extensions.wrapcommand(commands.table, 'branch', branch_wrapper)

def _parse(lines):
    for line in lines:
        items = shlex.split(line)
        _hgbranches[items[0]] = items[1]

def reposetup(ui, repo):
    #only interested in local repositories
    if not isinstance(repo, localrepo.localrepository): return

    global _hgbranches
    _hgbranches = {}

    #attempt to read .hgbranches from cache
    if repo.vfs.exists("cache/hgbranches"):
        try:
            cache = repo.vfs("cache/hgbranches").read().splitlines()
            if cache[0] == hex(repo.changelog.tip()): _parse(cache[1:])
        except:
            ui.warn("hgbranches cache corrupt, it will be deleted\n")
            os.remove(repo.vfs.join("cache/hgbranches"))

    #read .hgbranches from repo if not cached
    #conflicting renames from newer heads overwrite older heads
    if not _hgbranches:
        for head in reversed(repo.heads()):
            if '.hgbranches' in repo[head]:
                _parse(repo[head]['.hgbranches'].data().splitlines())

    #write .hgbranches cache
    with repo.vfs("cache/hgbranches", 'w') as cache:
        cache.write(hex(repo.changelog.tip()) + '\n')
        for old, new in _hgbranches.items():
            cache.write('"%s" "%s"\n' % (old,new))

    #read .hg/.hgbranches
    if repo.vfs.exists(".hgbranches"):
        _parse(repo.vfs(".hgbranches"))

    #build a list of changes from the last run
    if repo.vfs.exists("hgbranches-prev"):
        changes = {}
        previous = eval(repo.vfs("hgbranches-prev").read())
        for old, new in _hgbranches.items():
            if old in previous:
                #has a previous renaming changed?
                if previous[old] != new: changes[previous[old]] = new
            else:
                #new renaming
                changes[old] = new

        #check for deleted renamings
        for old in previous:
            if not old in _hgbranches:
                changes[previous[old]] = old
    else:
        changes = _hgbranches

    if changes:
        repo.vfs.write("hgbranches-prev", repr(_hgbranches))

    #update dirstate
    dirstate = repo.dirstate
    branch = dirstate.branch()
    if branch in changes:
        dirstate.setbranch(changes[branch])

    #update branchheads
    if repo.vfs.exists("cache/branchheads"):
        new = []
        with repo.vfs("cache/branchheads") as old:
            new.append(old.next()) #tip tracker
            for line in old:
                node, branch = line.strip().split(" ", 1)
                if branch in changes: branch = changes[branch]
                new.append(node + " " + branch + "\n")
        repo.vfs.write("cache/branchheads", "".join(new))

    #wrap changelog methods
    extensions.wrapfunction(changelog.changelog, 'add', add_wrapper)
    extensions.wrapfunction(changelog.changelog, 'read', read_wrapper)

def branch_wrapper(orig, ui, *args, **kwargs):
    """Remove the "branches are permanent and global" warning from branch's output."""
    if len(args) > 1 and args[1] in _hgbranches:
        raise util.Abort("branch " + args[1] + " has been renamed to " + _hgbranches[args[1]])
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