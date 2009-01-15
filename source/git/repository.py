# -*- coding: utf-8 -*- ex:set ts=4 sw=4 et:

# Copyright © 2008 - Steve Frécinaux
# License: LGPL 2

import exceptions
import os

from config import Config
from gitbinary import GitBinary
from objects import Commit
from misc import issha1

class InvalidRepositoryError(exceptions.Exception):
    pass

class Repository(object):
    "A Git repository."

    def __init__(self, path, create=False):
        abspath = os.path.abspath(path)
        if not os.path.isdir(abspath):
            raise exceptions.IOError("No such directory: '%s'" % abspath)

        # Find the right path for the repository.
        if abspath.endswith('.git'):
            self._path = abspath
            self._bare = True
        else:
            self._path = os.path.join(abspath, '.git')
            self._bare = False

        # Internal git binary.
        self.run = GitBinary(abspath, bare=self._bare)

        if create:
            self.run('init', '--quiet', output=False);

        # Check if we are in a valid repository (heuristics)
        # FIXME: what if .git is a plain file?
        if not os.path.isdir(self._path) or \
           not os.path.isdir(os.path.join(self._path, 'objects')) or \
           not os.path.isdir(os.path.join(self._path, 'refs')):
            raise InvalidRepositoryError(abspath)

    def __repr__(self):
        return '<git.Repository "%s">' % self._path

    # Description property
    def _get_description(self):
        filename = os.path.join(self._path, 'description')
        return file(filename).read().strip()

    def _set_description(self, descr):
        filename = os.path.join(self._path, 'description')
        file(filename, 'w').write(descr+"\n")

    description = property(_get_description, _set_description,
                           doc="repository description")
    del _get_description
    del _set_description

    # Daemon export property
    def _get_daemon_export(self):
        return os.path.isfile(os.path.join(self._path, 'git-daemon-export-ok'))

    def _set_daemon_export(self, value):
        filename = os.path.join(self._path, 'git-daemon-export-ok')
        fileexists = os.path.exists(filename)
        if value and not fileexists:
            file(filename, 'a').close()
        elif not value and fileexists:
            os.unlink(filename)

    daemon_export = property(_get_daemon_export, _set_daemon_export,
                            doc="git-daemon export of this repository.")
    del _get_daemon_export
    del _set_daemon_export

    # Config property
    @property
    def config(self):
        "repository configuration"
        if not hasattr(self, '_config'):
            self._config = Config(self)
        return self._config

    # Head property
    @property
    def head(self):
        "repository head"
        filename = os.path.join(self._path, 'HEAD')
        symref = file(filename).read().strip()
        if symref.startswith('ref: '):
            # The HEAD is a branch tip.
            ref = symref[5:]
            commitname = self.run('rev-parse', ref, wait=True).strip()
            return Commit(self, commitname, refname=ref)
        else:
            # We are not in a branch!
            return Commit(self, symref)

    @property
    def heads(self):
        "list all the repository heads"
        format = "%(refname) %(objectname) %(objecttype)"
        heads = {}
        for line in self.run('for-each-ref', '--format=%s' % format, 'refs/heads'):
            refname, objectname, objecttype = line.strip().split()
            assert objecttype == 'commit'
            heads[refname] = Commit(self, objectname, refname=refname)
        return heads

    def object(self, name):
        if not issha1(name):
            name = self.run('rev-parse', name, wait=True).strip()
        objtype = self.run('cat-file', '-t', name, wait=True).strip()
        if objtype == 'commit':
            return Commit(self, name)
        elif objtype == 'tree':
            return Tree(self, name)
        elif objtype == 'blob':
            return Blob(self, name)
        else:
            raise Exception("Unhandled object type: '%s'" % objtype)

    def rev_list(self, since='HEAD', to=None):
        cmd = ['rev-list', '%s' % since]
        if to is not None:
            cmd.append('^%s' % to)

        for line in self.run(*cmd):
            yield Commit(self, line)

    def clone(self, path):
        "clone the repository into the provided path"
        abspath = os.path.abspath(path)

        cmd = ['clone', '--quiet']
        if path.endswith('.git'):
            cmd.append('--bare')
        cmd.append(self._path)
        cmd.append(abspath)
        self.run(output=False, *cmd)
        return Repository(abspath)
