"""Rename named branches.

To start renaming branches, create a file called .hgbranches in the root of the working directory.
Each line in .hgbranches consists of a space-delimited pair such as oldBranch newBranch.
If the branch name contains spaces, it should be quoted.
Only the most recently checked in version of .hgbranches is used.
"""

from mercurial import dispatch, extensions, commands

def uisetup(ui):
    extensions.wrapcommand(commands.table, 'branch', branch_wrapper)

def branch_wrapper(orig, ui, *args, **kwargs):
    ui.pushbuffer()
    ret = orig(ui, *args, **kwargs)
    out = ui.popbuffer()
    lines = out.splitlines(True)
    if lines[-1].startswith("(branches are permanent and global"): lines.pop()
    ui.write(''.join(lines))
    return ret

testedwith = '2.3 2.4'
buglink = 'http://code.accursoft.com/mutable-branches/issues'