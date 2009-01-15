# -*- coding: utf-8 -*- ex:set ts=4 sw=4 et:

# Copyright © 2008 - Steve Frécinaux
# License: LGPL 2

class Config(dict):
    def __init__(self, repo):
        dict.__init__(self)
        self._repo = repo
        self._load()

    def _load(self):
        self._data = {}
        for line in self._repo.run('config', '--list'):
            key, value = line.strip().split('=', 1)
            dict.__setitem__(self, key, value.decode('utf-8'))

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        # update the repo config
        self._repo.run.run_noio(['config', 'key', str(value)])

if __name__ == '__main__':
    conf = Config()
