# -*- coding: utf-8 -*- ex:set ts=4 sw=4 et:

# Copyright © 2008 - Steve Frécinaux
# License: LGPL 2

class Object(object):
    "An object, following Git's definition."

    def __init__(self, repo, objectname):
        self._repo = repo
        self._name = objectname

    def __str__(self):
        return self._name or ''

    def __repr__(self):
        return '<git.%s "%s">' % (self.__class__.__name__, self._name)

    def __eq__(self, other):
        # Objects with no name are never equal to any other object.
        return self._name is not None and self._name == other._name

    def _dirty(self):
        """
        Mark an object as dirty. As a result, all its parent objects are
        marked as dirty too.
        """
        # We are already dirty, so our parents should be too.
        if self._name is None:
            return

        self._name = None
        if hasattr(self, 'parent') and self.parent is not None:
            self.parent._dirty()

    @property
    def name(self):
        return self._name

    @property
    def shortname(self):
        if self._name is None:
            return None
        return self.name[:8]

class Commit(Object):
    def __init__(self, repo, objectname=None, refname=None):
        Object.__init__(self, repo, objectname)
        if objectname is None:
            self._loaded = True
            self._tree = Tree(repo, parent=self)
            self._message = ''
        else:
            self._loaded = False
            self._tree = None
        self._parents = []
        self._refname = refname

    def _load(self):
        if self._loaded: return
        self._message = '';
        if self._name is None:
            return
        is_header = True
        for line in self._repo.run('cat-file', 'commit', self._name):
            if is_header:
                line = line.strip()
                if line == '':
                    is_header = False
                    continue
                key, value = line.split(' ', 1)
                if key == 'tree':
                    self._tree = Tree(self._repo, value, parent=self)
                    continue
                if key == 'parent':
                    self._parents.append(value)
                    continue
                if key == 'author':
                    author, timestamp, offset = value.rsplit(' ', 2)
                    self._author = author
                    self._author_timestamp = timestamp
                    self._author_offset = offset
                    continue
                if key == 'committer':
                    author, timestamp, offset = value.rsplit(' ', 2)
                    self._committer = author
                    self._committer_timestamp = timestamp
                    self._committer_offset = offset
                    continue
                continue
            self._message += line

    def _dirty(self):
        old_name = self._name
        if old_name is not None:
            Object._dirty(self)
            self._parents = [old_name]

    @property
    def parents(self):
        self._load()
        return [Commit(self._repo, c) for c in self._parents]

    @property
    def tree(self):
        self._load()
        return self._tree

    @property
    def author(self):
        self._load()
        return self._author

    @property
    def comitter(self):
        self._load()
        return self._committer

    @property
    def message(self):
        self._load()
        return self._message

    @property
    def refname(self):
        return self._refname

    def write(self):
        if self._name is not None:
            return self._name

        tree_name = self.tree.write()

        cmd = ['commit-tree', tree_name]
        for p in self._parents:
            cmd.extend(['-p', p])

        self._name = self._repo.run(input=self.message, wait=True, *cmd).strip()
        return self._name

    def commit(self):
        self.write()
        if self.refname is not None:
            self._repo.run('update-ref', self.refname, self._name, output=False)

class Tree(Object):
    def __init__(self, repo, objectname=None, mode='040000', parent=None):
        Object.__init__(self, repo, objectname)
        self._parent = parent
        self.mode = mode
        if objectname is None:
            self._loaded = True
            self._contents = {}
        else:
            self._loaded = False

    def _load(self):
        if self._loaded:
            return
        self._contents = {}
        if self._name is None:
            return
        for line in self._repo.run('cat-file', '-p', self._name):
            mode, objtype, objname, filename = line.split(None, 3)
            if objtype == 'tree':
                self._contents[filename] = Tree(self._repo, objname, mode=mode, parent=self)
            elif objtype == 'blob':
                self._contents[filename] = Blob(self._repo, objname, mode=mode, parent=self)
            else:
                raise Exception("Unknown object type: '%s'" % objtype)

    def __getitem__(self, filename):
        self._load()
        return self._contents[filename]

    def __setitem__(self, filename, obj):
        if not isinstance(filename, str):
            raise ValueError("filename must be a string.")
        if '/' in filename:
            raise ValueError("filename cannot contain the '/' symbol.")
        if not isinstance(obj, Blob) and not isinstance(obj, Tree):
            raise ValueError("value must be a Blob or Tree object.")

        self._load()
        self._contents[filename] = obj
        obj._parent = self
        self._dirty()

    def __iter__(self):
        self._load()
        return iter(self._contents)

    def keys(self):
        self._load()
        return self._contents.keys()

    @property
    def parent(self):
        "parent of this object"
        return self._parent

    @property
    def root(self):
        "root tree of this object"
        if isinstance(self._parent, Commit):
            return self
        else:
            return self._parent.root

    def write(self):
        if self._name is not None:
            return self._name

        data = []
        for path in self._contents:
            obj = self._contents[path]
            obj.write()
            objtype = isinstance(obj, Tree) and 'tree' or 'blob'
            data.append("%s %s %s\t%s" % (obj.mode, objtype, obj.name, path))

        self._name = self._repo.run('mktree', '-z', input='\0'.join(data), wait=True).strip()
        return self._name

class Blob(Object):
    def __init__(self, repo, objectname=None, mode='100644', parent=None):
        Object.__init__(self, repo, objectname)
        self._parent = parent
        if objectname is None:
            self._contents = ''
            self._loaded = True
        else:
            self._loaded = False
        self.mode = mode

    def _load(self):
        if self._loaded: return
        self._contents = self._repo.run('cat-file', 'blob', self._name, wait=True)

    # Contents property
    def _get_contents(self):
        self._load()
        return self._contents

    def _set_contents(self, contents):
        self._loaded = True # No need to actually load the data here.
        self._contents = contents
        self._dirty()

    contents = property(_get_contents, _set_contents)
    del _get_contents
    del _set_contents

    @property
    def parent(self):
        "parent of this object"
        return self._parent

    @property
    def root(self):
        "root tree of this object"
        return self._parent.root

    def write(self):
        if self._name is None:
            self._name = self._repo.run('hash-object', '-w', '--stdin', input=self.contents, wait=True).strip()
        return self._name
