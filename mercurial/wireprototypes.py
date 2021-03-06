# Copyright 2018 Gregory Szorc <gregory.szorc@gmail.com>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from __future__ import absolute_import

from .node import (
    bin,
    hex,
)
from .i18n import _
from . import (
    error,
    util,
)
from .utils import (
    interfaceutil,
)

# Names of the SSH protocol implementations.
SSHV1 = 'ssh-v1'
# These are advertised over the wire. Increment the counters at the end
# to reflect BC breakages.
SSHV2 = 'exp-ssh-v2-0001'
HTTP_WIREPROTO_V2 = 'exp-http-v2-0001'

# All available wire protocol transports.
TRANSPORTS = {
    SSHV1: {
        'transport': 'ssh',
        'version': 1,
    },
    SSHV2: {
        'transport': 'ssh',
        # TODO mark as version 2 once all commands are implemented.
        'version': 1,
    },
    'http-v1': {
        'transport': 'http',
        'version': 1,
    },
    HTTP_WIREPROTO_V2: {
        'transport': 'http',
        'version': 2,
    }
}

class bytesresponse(object):
    """A wire protocol response consisting of raw bytes."""
    def __init__(self, data):
        self.data = data

class ooberror(object):
    """wireproto reply: failure of a batch of operation

    Something failed during a batch call. The error message is stored in
    `self.message`.
    """
    def __init__(self, message):
        self.message = message

class pushres(object):
    """wireproto reply: success with simple integer return

    The call was successful and returned an integer contained in `self.res`.
    """
    def __init__(self, res, output):
        self.res = res
        self.output = output

class pusherr(object):
    """wireproto reply: failure

    The call failed. The `self.res` attribute contains the error message.
    """
    def __init__(self, res, output):
        self.res = res
        self.output = output

class streamres(object):
    """wireproto reply: binary stream

    The call was successful and the result is a stream.

    Accepts a generator containing chunks of data to be sent to the client.

    ``prefer_uncompressed`` indicates that the data is expected to be
    uncompressable and that the stream should therefore use the ``none``
    engine.
    """
    def __init__(self, gen=None, prefer_uncompressed=False):
        self.gen = gen
        self.prefer_uncompressed = prefer_uncompressed

class streamreslegacy(object):
    """wireproto reply: uncompressed binary stream

    The call was successful and the result is a stream.

    Accepts a generator containing chunks of data to be sent to the client.

    Like ``streamres``, but sends an uncompressed data for "version 1" clients
    using the application/mercurial-0.1 media type.
    """
    def __init__(self, gen=None):
        self.gen = gen

class cborresponse(object):
    """Encode the response value as CBOR."""
    def __init__(self, v):
        self.value = v

class v2errorresponse(object):
    """Represents a command error for version 2 transports."""
    def __init__(self, message, args=None):
        self.message = message
        self.args = args

class v2streamingresponse(object):
    """A response whose data is supplied by a generator.

    The generator can either consist of data structures to CBOR
    encode or a stream of already-encoded bytes.
    """
    def __init__(self, gen, compressible=True):
        self.gen = gen
        self.compressible = compressible

# list of nodes encoding / decoding
def decodelist(l, sep=' '):
    if l:
        return [bin(v) for v in  l.split(sep)]
    return []

def encodelist(l, sep=' '):
    try:
        return sep.join(map(hex, l))
    except TypeError:
        raise

# batched call argument encoding

def escapebatcharg(plain):
    return (plain
            .replace(':', ':c')
            .replace(',', ':o')
            .replace(';', ':s')
            .replace('=', ':e'))

def unescapebatcharg(escaped):
    return (escaped
            .replace(':e', '=')
            .replace(':s', ';')
            .replace(':o', ',')
            .replace(':c', ':'))

# mapping of options accepted by getbundle and their types
#
# Meant to be extended by extensions. It is extensions responsibility to ensure
# such options are properly processed in exchange.getbundle.
#
# supported types are:
#
# :nodes: list of binary nodes
# :csv:   list of comma-separated values
# :scsv:  list of comma-separated values return as set
# :plain: string with no transformation needed.
GETBUNDLE_ARGUMENTS = {
    'heads':  'nodes',
    'bookmarks': 'boolean',
    'common': 'nodes',
    'obsmarkers': 'boolean',
    'phases': 'boolean',
    'bundlecaps': 'scsv',
    'listkeys': 'csv',
    'cg': 'boolean',
    'cbattempted': 'boolean',
    'stream': 'boolean',
}

class baseprotocolhandler(interfaceutil.Interface):
    """Abstract base class for wire protocol handlers.

    A wire protocol handler serves as an interface between protocol command
    handlers and the wire protocol transport layer. Protocol handlers provide
    methods to read command arguments, redirect stdio for the duration of
    the request, handle response types, etc.
    """

    name = interfaceutil.Attribute(
        """The name of the protocol implementation.

        Used for uniquely identifying the transport type.
        """)

    def getargs(args):
        """return the value for arguments in <args>

        For version 1 transports, returns a list of values in the same
        order they appear in ``args``. For version 2 transports, returns
        a dict mapping argument name to value.
        """

    def getprotocaps():
        """Returns the list of protocol-level capabilities of client

        Returns a list of capabilities as declared by the client for
        the current request (or connection for stateful protocol handlers)."""

    def getpayload():
        """Provide a generator for the raw payload.

        The caller is responsible for ensuring that the full payload is
        processed.
        """

    def mayberedirectstdio():
        """Context manager to possibly redirect stdio.

        The context manager yields a file-object like object that receives
        stdout and stderr output when the context manager is active. Or it
        yields ``None`` if no I/O redirection occurs.

        The intent of this context manager is to capture stdio output
        so it may be sent in the response. Some transports support streaming
        stdio to the client in real time. For these transports, stdio output
        won't be captured.
        """

    def client():
        """Returns a string representation of this client (as bytes)."""

    def addcapabilities(repo, caps):
        """Adds advertised capabilities specific to this protocol.

        Receives the list of capabilities collected so far.

        Returns a list of capabilities. The passed in argument can be returned.
        """

    def checkperm(perm):
        """Validate that the client has permissions to perform a request.

        The argument is the permission required to proceed. If the client
        doesn't have that permission, the exception should raise or abort
        in a protocol specific manner.
        """

class commandentry(object):
    """Represents a declared wire protocol command."""
    def __init__(self, func, args='', transports=None,
                 permission='push'):
        self.func = func
        self.args = args
        self.transports = transports or set()
        self.permission = permission

    def _merge(self, func, args):
        """Merge this instance with an incoming 2-tuple.

        This is called when a caller using the old 2-tuple API attempts
        to replace an instance. The incoming values are merged with
        data not captured by the 2-tuple and a new instance containing
        the union of the two objects is returned.
        """
        return commandentry(func, args=args, transports=set(self.transports),
                            permission=self.permission)

    # Old code treats instances as 2-tuples. So expose that interface.
    def __iter__(self):
        yield self.func
        yield self.args

    def __getitem__(self, i):
        if i == 0:
            return self.func
        elif i == 1:
            return self.args
        else:
            raise IndexError('can only access elements 0 and 1')

class commanddict(dict):
    """Container for registered wire protocol commands.

    It behaves like a dict. But __setitem__ is overwritten to allow silent
    coercion of values from 2-tuples for API compatibility.
    """
    def __setitem__(self, k, v):
        if isinstance(v, commandentry):
            pass
        # Cast 2-tuples to commandentry instances.
        elif isinstance(v, tuple):
            if len(v) != 2:
                raise ValueError('command tuples must have exactly 2 elements')

            # It is common for extensions to wrap wire protocol commands via
            # e.g. ``wireproto.commands[x] = (newfn, args)``. Because callers
            # doing this aren't aware of the new API that uses objects to store
            # command entries, we automatically merge old state with new.
            if k in self:
                v = self[k]._merge(v[0], v[1])
            else:
                # Use default values from @wireprotocommand.
                v = commandentry(v[0], args=v[1],
                                 transports=set(TRANSPORTS),
                                 permission='push')
        else:
            raise ValueError('command entries must be commandentry instances '
                             'or 2-tuples')

        return super(commanddict, self).__setitem__(k, v)

    def commandavailable(self, command, proto):
        """Determine if a command is available for the requested protocol."""
        assert proto.name in TRANSPORTS

        entry = self.get(command)

        if not entry:
            return False

        if proto.name not in entry.transports:
            return False

        return True

def supportedcompengines(ui, role):
    """Obtain the list of supported compression engines for a request."""
    assert role in (util.CLIENTROLE, util.SERVERROLE)

    compengines = util.compengines.supportedwireengines(role)

    # Allow config to override default list and ordering.
    if role == util.SERVERROLE:
        configengines = ui.configlist('server', 'compressionengines')
        config = 'server.compressionengines'
    else:
        # This is currently implemented mainly to facilitate testing. In most
        # cases, the server should be in charge of choosing a compression engine
        # because a server has the most to lose from a sub-optimal choice. (e.g.
        # CPU DoS due to an expensive engine or a network DoS due to poor
        # compression ratio).
        configengines = ui.configlist('experimental',
                                      'clientcompressionengines')
        config = 'experimental.clientcompressionengines'

    # No explicit config. Filter out the ones that aren't supposed to be
    # advertised and return default ordering.
    if not configengines:
        attr = 'serverpriority' if role == util.SERVERROLE else 'clientpriority'
        return [e for e in compengines
                if getattr(e.wireprotosupport(), attr) > 0]

    # If compression engines are listed in the config, assume there is a good
    # reason for it (like server operators wanting to achieve specific
    # performance characteristics). So fail fast if the config references
    # unusable compression engines.
    validnames = set(e.name() for e in compengines)
    invalidnames = set(e for e in configengines if e not in validnames)
    if invalidnames:
        raise error.Abort(_('invalid compression engine defined in %s: %s') %
                          (config, ', '.join(sorted(invalidnames))))

    compengines = [e for e in compengines if e.name() in configengines]
    compengines = sorted(compengines,
                         key=lambda e: configengines.index(e.name()))

    if not compengines:
        raise error.Abort(_('%s config option does not specify any known '
                            'compression engines') % config,
                          hint=_('usable compression engines: %s') %
                          ', '.sorted(validnames))

    return compengines
