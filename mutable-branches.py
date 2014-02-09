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
    _deserialise(_hgbranches, lines)

def _serialise(hgbranches):
    return '\n'.join('"%s" "%s"' % (old,new) for old, new in hgbranches.items())

def _deserialise(hgbranches, lines):
    for line in lines:
        items = shlex.split(line)
        hgbranches[items[0]] = items[1]

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
        except Exception as e:
            ui.debug('"%s" reading hgbranches cache\n' % e[0])
            ui.warn("hgbranches cache corrupt, it will be recreated\n")
            os.remove(repo.vfs.join("cache/hgbranches"))

    #otherwise read .hgbranches from repo
    #conflicting renames from newer heads overwrite older heads
    if not _hgbranches:
        for head in reversed(repo.heads()):
            if '.hgbranches' in repo[head]:
                try:
                    _parse(repo[head]['.hgbranches'].data().splitlines())
                except Exception as e:
                    ui.warn('"%s" reading .hgbranches\n' % e[0])
                    raise util.Abort(".hgbranches is corrupt.\n"
                    "Please disable mutable-branches and fix it.")
        #write .hgbranches cache
        try:
            with repo.vfs("cache/hgbranches", 'w') as cache:
                cache.write(hex(repo.changelog.tip()) + '\n')
                cache.write(_serialise(_hgbranches))
        except Exception as e:
            ui.debug('"%s" writing hgbranches cache\n' % e[0])
            ui.warn("The hgbranches cache could not be written.\n")

    #read .hg/.hgbranches
    if repo.vfs.exists(".hgbranches"):
        try:
            _parse(repo.vfs(".hgbranches"))
        except Exception as e:
            ui.warn('"%s" reading local .hgbranches\n' % e[0])
            raise util.Abort("local .hgbranches is corrupt")

    #build a list of changes from the last run
    if repo.vfs.exists("hgbranches-prev"):
        changes = {}
        previous = {}
        try:
            _deserialise(previous, repo.vfs("hgbranches-prev"))
        except Exception as e:
            ui.warn('"%s" reading .hg/.hgbranches-prev\n' % e[0])
            raise util.Abort(".hg/hgbranches-prev is corrupt.\n"
            "If you delete it, .hg/cache/branchheads* should also be deleted.\n"
            "You may also need to reset the current branch.")

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
        repo.vfs.write("hgbranches-prev", _serialise(_hgbranches))

        #update dirstate
        dirstate = repo.dirstate
        branch = dirstate.branch()
        if branch in changes:
            dirstate.setbranch(changes[branch])

        #update branchheads
        branchheads = ["branchheads"]
        try:
            #process the filtered branchhead caches introduced in 2.5
            from mercurial import repoview
            branchheads.extend("%s-%s" % (branchheads[0], filter) for filter in repoview.filtertable)
            #process the new branchhead cache format introduced in 2.9
            branchheads.extend("branch2-" + filter for filter in repoview.filtertable)
        except ImportError:
            pass

        for file in ("cache/" + file for file in branchheads):
            if not repo.vfs.exists(file): continue
            new = []
            with repo.vfs(file) as old:
                new.append(old.next()) #tip tracker
                for line in old:
                    if "branch2" in file:
                        rest1, rest2, branch = line.strip().split(" ", 2)
                        rest = rest1 + " " + rest2
                    else:
                        rest, branch = line.strip().split(" ", 1)
                    if branch in changes: branch = changes[branch]
                    new.append(rest + " " + branch + "\n")
            repo.vfs.write(file, "".join(new))

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

testedwith = '2.3 2.4 2.5 2.6 2.7 2.8 2.9'
buglink = 'http://code.accursoft.com/mutable-branches/issues'