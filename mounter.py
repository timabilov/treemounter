import os
import shutil
from contextlib import contextmanager
from datetime import datetime
from time import sleep
from types import coroutine

from typing import Union


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class PathMixin:

    @coroutine
    def ancestors(self):
        obj = self
        while True:
            if obj._parent:
                obj = obj._parent
                yield obj
            else:
                break

    def path(self):

        return "/".join(map(str, self.ancestors())) + "/" + self.name

    def realpath(self, mount_path):
        """
        Mounted path of the node
        :return:
        """
        ancestors = list(reversed(list(self.ancestors())))
        # root, *others = ancestors

        if not mount_path:
            # no mount
            return

        head = ("/".join(map(str, ancestors)) + "/") if ancestors else ""
        return mount_path + head + self.name

    def _mount(self, mount_path):#, element: Union['File', 'Folder']):

        # path = self.path()
        if isinstance(self, Dir):
            if not os.path.exists(self.realpath(mount_path)):
                os.makedirs(self.realpath(mount_path))

        elif isinstance(self, File):
            with open(self.realpath(mount_path), 'w') as fd:
                if self.data:
                    fd.write(self.data)

    def delete(self):
        if not hasattr(self, 'mount_path'):
            raise Exception(f"`mount_path` is not specified for {self.path()}."
                            f" Check that specified resource is folder.")
        shutil.rmtree((self.realpath(self.mount_path)))
        self.mount_path = None

    def __repr__(self):
        return self.name

    def render(self):
        return self.name


class File(PathMixin):
    """
    In-memory plain file implementation
    """
    def __init__(self, name, data=None):
        self.name = name
        self.data = data
        self._parent = None  # when adding file to some folder
        self.time = datetime.now()
        self.real_path = None

    def render(self):
        return bcolors.OKBLUE + super().render() + bcolors.ENDC


class FolderNotFoundException(Exception):

    pass


class Folder(PathMixin):

    def __init__(self, name, folder=None, parent=None, mount: str = None):
        self.name = name
        self.folder = folder
        self.folders = []
        self.files = []
        self.time = datetime.now()
        self._parent = parent
        self.mount_path = mount  # structure mount point, only for root
        self.real_path = mount  # real path of this folder

    def add(self, obj: Union['File', 'Folder']):
        if getattr(obj, 'mount_path', False):
            raise Exception(f'Mounted node({obj.name}) should be root "{self.name}->{obj.name}"')

        if isinstance(obj, Folder):
            self.folders += [obj]
            obj._parent = self
        elif isinstance(obj, File):
            self.files += [obj]
            obj._parent = self

        if self.is_mounted():
            self.sync()

    def is_mounted(self):
        any(element.mounted for element in self.ancestors())

    def elements(self):

        return self.folders + self.files

    def list(self):

        ls = self.elements()
        for i in ls:
            print(i.render())

    def cd(self, name):
        for i in self.folders:
            if i.name == name:
                return i
        raise FolderNotFoundException(
            f'{self.name} has no -> {name} . Existing folders: {self.folders}'
        )

    def _removefile(self, filenmae):
        for i, file in enumerate(self.files, start=0):
            if file.name == filenmae:
                self.files.pop(i)

    def _removefolder(self, foldername):
        for i, folder in enumerate(self.folders, start=0):
            if folder.name == foldername:
                self.folders.pop(i)

    def rm(self, name):
        for i in self.folders + self.files:
            if i.name == name:
                if isinstance(i, File):
                    self._removefile(name)
                    break
                else:
                    self._removefolder(name)
                    break

    def __call__(self, *args: Union['File', 'Folder'], **kwargs):
        for element in args:
            self.add(element)
        return self

    ####### TREE OPERATIONS ########

    def tree(self, level=0):
        list(
            map(
                lambda el: print((el[1] * 3 * ' ') + el[0].render()),
                self.traverse()
            )
        )

    @coroutine
    def search(self, keyword):
        for element in self.traverse():
            if keyword in str(element):
                yield element

    def traverse(self, level=0):
        """
        Returns element and level of depth
        :param level:
        :return:
        """
        l = []
        for i in self.files:

            l.append((i, level))

        for i in self.folders:
            l.append((i, level))
            # traverse always returns two values. (i, level)
            l.extend(i.traverse(level + 1))
        return l

    def mount(self, mount_path):
        """
        In-place mounting of current structure
        :return:
        """
        self.mount_path = mount_path
        self._mount(mount_path)
        for element, _ in self.traverse():
            element._mount(self.mount_path)
        return self

    def render(self):
        return bcolors.WARNING + super().render() + bcolors.ENDC

    def __getitem__(self, item: str):
        if not isinstance(item, str):
            raise TypeError(f'Dir indices must be str, not {type(item)}')

        for node in self.elements():
            if item == node.name:
                return node

    def __truediv__(self, path: str):
        if not isinstance(path, str):
            raise TypeError(f'Dir indices must be str, not {type(path)}')
        folder: Folder = self
        for fd in path.split('/'):
            folder = folder.cd(fd)
        return folder


class Dir(Folder):

    """
    Only shortcut use for nested creation
    """
    pass


@contextmanager
def tmpmount(node: Union['Folder', 'File'], mount='./'):
    node.mount(mount)

    try:
        yield node
    finally:
        node.delete()
