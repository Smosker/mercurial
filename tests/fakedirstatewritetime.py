# extension to emulate invoking 'dirstate.write()' at the time
# specified by '[fakedirstatewritetime] fakenow', only when
# 'dirstate.write()' is invoked via functions below:
#
#   - 'workingctx._poststatusfixup()' (= 'repo.status()')
#   - 'committablectx.markcommitted()'

from __future__ import absolute_import

from mercurial import (
    context,
    dirstate,
    extensions,
    policy,
    registrar,
)
from mercurial.utils import dateutil

configtable = {}
configitem = registrar.configitem(configtable)

configitem(b'fakedirstatewritetime', b'fakenow',
    default=None,
)

parsers = policy.importmod(r'parsers')

def pack_dirstate(fakenow, orig, dmap, copymap, pl, now):
    # execute what original parsers.pack_dirstate should do actually
    # for consistency
    actualnow = int(now)
    for f, e in dmap.items():
        if e[0] == 'n' and e[3] == actualnow:
            e = parsers.dirstatetuple(e[0], e[1], e[2], -1)
            dmap[f] = e

    return orig(dmap, copymap, pl, fakenow)

def fakewrite(ui, func):
    # fake "now" of 'pack_dirstate' only if it is invoked while 'func'

    fakenow = ui.config(b'fakedirstatewritetime', b'fakenow')
    if not fakenow:
        # Execute original one, if fakenow isn't configured. This is
        # useful to prevent subrepos from executing replaced one,
        # because replacing 'parsers.pack_dirstate' is also effective
        # in subrepos.
        return func()

    # parsing 'fakenow' in YYYYmmddHHMM format makes comparison between
    # 'fakenow' value and 'touch -t YYYYmmddHHMM' argument easy
    fakenow = dateutil.parsedate(fakenow, [b'%Y%m%d%H%M'])[0]

    orig_pack_dirstate = parsers.pack_dirstate
    orig_dirstate_getfsnow = dirstate._getfsnow
    wrapper = lambda *args: pack_dirstate(fakenow, orig_pack_dirstate, *args)

    parsers.pack_dirstate = wrapper
    dirstate._getfsnow = lambda *args: fakenow
    try:
        return func()
    finally:
        parsers.pack_dirstate = orig_pack_dirstate
        dirstate._getfsnow = orig_dirstate_getfsnow

def _poststatusfixup(orig, workingctx, status, fixup):
    ui = workingctx.repo().ui
    return fakewrite(ui, lambda : orig(workingctx, status, fixup))

def markcommitted(orig, committablectx, node):
    ui = committablectx.repo().ui
    return fakewrite(ui, lambda : orig(committablectx, node))

def extsetup(ui):
    extensions.wrapfunction(context.workingctx, '_poststatusfixup',
                            _poststatusfixup)
    extensions.wrapfunction(context.committablectx, 'markcommitted',
                            markcommitted)
