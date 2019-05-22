import os
import sh


def parse_subvolume(line):
    components = line.split()
    parent_uid = components[8] if components[8] != '-' else None
    return {
        'id_': components[1],
        'gen': components[3],
        'top_level': components[6],
        'parent_uid': parent_uid,
        'uid': components[10],
        'name': components[12],
    }


def get_subvolumes(path):
    result = sh.btrfs.subvolume.list('-u', '-q', path)
    output = result.stdout.decode('utf-8')

    return [parse_subvolume(x) for x in output.splitlines()]


def parse_snapshot(line):
    components = line.split()
    return {
        'id_': components[1],
        'gen': components[3],
        'cgen': components[5],
        'top_level': components[8],
        'otime': components[10] + ' ' + components[11],
        'parent_uid': components[13],
        'uid': components[15],
        'name': components[17],
    }


def get_snapshots(path):
    result = sh.btrfs.subvolume.list('-u', '-q', '-s', path)
    output = result.stdout.decode('utf-8')

    return [parse_snapshot(x) for x in output.splitlines()]


class BtrfsError(Exception):
    pass


class SubvolumeCreationFailed(BtrfsError):
    pass


class NoSuchFileOrDirectory(SubvolumeCreationFailed):
    pass


class TargetPathAlreadyExists(SubvolumeCreationFailed):
    pass


class FileSystem(object):
    def __init__(self, mountpoint):
        self.mountpoint = mountpoint

    @property
    def subvolumes(self):
        return [
            Subvolume(s['uid'], s['name'], s['parent_uid'], self)
            for s in get_subvolumes(self.mountpoint)]

    @property
    def snapshots(self):
        return [
            Snapshot(s['otime'], s['uid'], s['name'], s['parent_uid'], self)
            for s in get_snapshots(self.mountpoint)]

    def find_subvolume_by_name(self, name):
        for subvolume in self.subvolumes:
            if subvolume.name == name:
                return subvolume
        return None

    def find_subvolume_by_prefix(self, prefix):
        found = []
        for subvolume in self.subvolumes:
            if subvolume.name.startswith(prefix):
                found.append(subvolume)

        return found

    def find_subvolume_by_uid(self, uid):
        for subvolume in self.subvolumes:
            if subvolume.uid == uid:
                return subvolume
        return None

    def find_snapshot_by_name(self, name):
        for snapshot in self.snapshots:
            if snapshot.name == name:
                return snapshot
        return None

    def make_subvolume(self, name):
        path = os.path.join(self.mountpoint, name)
        try:
            sh.btrfs.subvolume.create(path)
        except sh.ErrorReturnCode_1 as e:
            stderr = e.stderr.decode('utf-8')
            if stderr.startswith("ERROR: can't access"):
                raise NoSuchFileOrDirectory(stderr)
            if stderr.startswith("ERROR: '{0}' exists".format(path)):
                raise TargetPathAlreadyExists(stderr)
            raise BtrfsError(stderr)

        return self.find_subvolume_by_name(name)

    def delete_subvolume(self, name):
        path = os.path.join(self.mountpoint, name)
        try:
            sh.btrfs.subvolume.delete(path)
        except sh.ErrorReturnCode_1 as e:
            stderr = e.stderr.decode('utf-8')
            if 'No such file or directory' in stderr:
                return
            raise BtrfsError(stderr)


class Subvolume(object):
    def __init__(self, uid, name, parent_uid, fs):
        self.uid = uid
        self.name = name
        self.parent_uid = parent_uid
        self.fs = fs

    def __repr__(self):
        return f'<Subvolume({self.short_uid}, {self.path})>'

    def __iter__(self):
        yield from (
            ('uid', self.uid),
            ('short_uid', self.short_uid),
            ('parent_uid', self.parent_uid),
            ('name', self.name),
            ('path', self.path),
        )

    def __eq__(self, other):
        if type(self) != type(other):
            return False

        return dict(self) == dict(other)

    @property
    def short_uid(self):
        return self.uid.split('-')[0]

    @property
    def path(self):
        return os.path.join(self.fs.mountpoint, self.name)

    @property
    def subvolumes(self):
        return self.fs.find_subvolume_by_prefix(f"{self.name}/")

    def delete(self):
        for vol in self.subvolumes:
            vol.delete()

        try:
            sh.btrfs.subvolume.delete(self.path)
        except sh.ErrorReturnCode_1 as e:
            stderr = e.stderr.decode('utf-8')
            raise BtrfsError(stderr)

    def take_snapshot(self, name):
        path = os.path.join(self.fs.mountpoint, name)
        sh.btrfs.subvolume.snapshot(self.path, path)
        return self.fs.find_snapshot_by_name(name)


class Snapshot(Subvolume):
    def __init__(self, otime, *args, **kwargs):
        self.otime = otime
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return f'<Snapshot({self.short_uid}, {self.path})>'
