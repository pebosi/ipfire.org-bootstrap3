# -*- coding: utf-8 -*- ex:set ts=4 sw=4 et:

# Copyright © 2008 - Steve Frécinaux
# License: LGPL 2

import subprocess
import select
import exceptions
import os

class ExecutionError(exceptions.Exception):
    pass

class GitBinary(object):
    binary = ['/usr/bin/env', 'git']

    def __init__(self, repo_dir, bare=False):
        self.repo_args = []
        if bare:
            self.repo_args.append('--bare')
        else:
            self.repo_args.append('--work-tree=%s' % repo_dir)
            repo_dir = os.path.join(repo_dir, '.git')
        self.repo_args.append('--git-dir=%s' % repo_dir)
        self.bare = bare
        self.git_dir = repo_dir

    def _command(self, *args):
        if args[0] == 'clone':
            return self.binary + list(args)
        else:
            return self.binary + self.repo_args + list(args)

    def gen(self, p):
        while True:
            rlist = select.select([p.stdout], [], [])[0]
            if p.stdout in rlist:
                line = p.stdout.readline()
            if line:
                yield line.rstrip("\n")
            else:
                break
        p.stdout.close()

        if p.wait() != 0:
            raise ExecutionError("Subprocess exited with non-zero returncode"
                                 " of %d" % p.returncode)

    def __call__(self, *args, **kwargs):
        cmd = self._command(args)

        # The input parameter allows to feed the process's stdin
        input = kwargs.get('input', None)
        has_input = input is not None

        # The wait parameter will make the function wait for the process to
        # have completed and return the full output at once.
        wait = bool(kwargs.get('wait', False))

        # The output parameter will make the function watch for some output.
        has_output = bool(kwargs.get('output', True))

        p = subprocess.Popen(self._command(*args),
                             stdin = has_input and subprocess.PIPE or None,
                             stdout = has_output and subprocess.PIPE or None,
                             bufsize=1)
        if has_input:
            p.stdin.write(input)
            p.stdin.close()

        if has_output:
            gen = self.gen(p)
            return wait and '\n'.join(gen) or gen

        if p.wait() != 0:
            raise ExecutionError("Subprocess exited with non-zero returncode"
                                 " of %d" % p.returncode)
