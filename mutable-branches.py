"""Rename named branches.

To start renaming branches, create a file called .hgbranches in the root of the working directory.
Each line in .hgbranches consists of a space-delimited pair such as oldBranch newBranch.
If the branch name contains spaces, it should be quoted.
Only the most recently checked in version of .hgbranches is used.
"""

from mercurial import extensions, commands, changelog

def read_hgbranches():
    global _hgbranches
    if not '_hgbranches' in globals():
        _hgbranches = {'a':'x','b':'y'}
    return _hgbranches

def uisetup(ui):
    extensions.wrapcommand(commands.table, 'branch', branch_wrapper)
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
    for old, new in read_hgbranches().items():
        if branch == new:
            args[8]['branch'] = old
            break
    return orig(ui, *args, **kwargs)

def read_wrapper(orig, ui, *args, **kwargs):
    ret = orig(ui, *args, **kwargs)
    branch = ret[5]['branch']
    hgbranches = read_hgbranches()
    #rename branch
    if branch in hgbranches: ret[5]['branch'] = hgbranches[branch]
    return ret

testedwith = '2.3 2.4'
buglink = 'http://code.accursoft.com/mutable-branches/issues'