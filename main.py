import os
from datetime import datetime
from typing import List

from cli import cli


class File:
    def __init__(self, name: str, content=""):
        self.name = name
        self.content = content
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.size = len(content)

    def to_dict(self):
        return {
            "type": "file",
            "name": self.name,
            "content": self.content,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "size": self.size
        }

    @classmethod
    def from_dict(cls, data):
        file = cls(data['name'], data['content'])
        file.created_at = data['created_at']
        file.updated_at = data['updated_at']
        file.size = data['size']
        return file


class Directory:
    def __init__(self, name, parent=None):
        self.name = name
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.parent = parent
        self.children = {}

    def to_dict(self):
        return {
            'type': 'directory',
            'name': self.name,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'children': {name: child.to_dict() for name, child in self.children.items()}
        }

    @classmethod
    def from_dict(cls, data):
        dir_obj = cls(data['name'])
        dir_obj.created_at = data['created_at']
        dir_obj.updated_at = data['updated_at']

        for name, child_data in data["children"].items():
            if child_data["type"] == 'file':
                dir_obj.children[name] = File.from_dict(child_data)
            else:
                dir_obj.children[name] = Directory.from_dict(child_data)

        return dir_obj

    def add_child(self, child) -> None:
        child.parent = self
        self.children[child.name] = child
        self.updated_at = datetime.now().isoformat()

    def remove_child(self, name) -> bool:
        if name in self.children:
            del self.children[name]
            self.updated_at = datetime.now().isoformat()
            return True
        else:
            return False

    def get_child(self, name):
        return self.children.get(name)

    def list_children(self) -> List[str]:
        return list(self.children.keys())


class VFS:
    def __init__(self):
        self.root = Directory("root/", parent=None)
        self.current_dir = self.root
        self.current_path = "/"
        self.mount_points = {}

    def run(self, args) -> None:
        print(args.command)
        match args.command:
            case "cd":
                self.cd(args.route)
        # TODO write all cases

    def _resolve_path(self, path):
        path = path.replace("\\", "/")
        if not path.startswith("/"):
            path = os.path.join(self.current_path, path)
        return os.path.normpath(path) + "/"

    def _find_dir(self, path):
        path = self._resolve_path(path)
        if path == "/":
            return self.root

        components = [c for c in path.split("/") if c]
        current = self.root

        for component in components:
            if component == "..":
                if current.parent is not None:
                    current = current.parent
                else:
                    child = current.get_child(component)
                    if isinstance(child, Directory):
                        current = child
                    else:
                        return None
        return current

    def cd(self, path):
        if not path:
            return False
        full_path = self._resolve_path(path)
        for mount_path in self.mount_points:
            if full_path.startswith(mount_path):
                print("cant cd to mounted dir")
                return False
        target_dir = self._find_dir(path)
        if target_dir:
            self.current_dir = target_dir
            self._update_current_path()
            return True
        else:
            print(f"dir not found {path}")
            return False

    def _update_current_path(self):
        path_parts = []
        current = self.current_dir

        while current is not None and current != self.root:
            path_parts.append(current.name)

        self.current_path = "/" + "/".join(reversed(path_parts)) + "/"

    def mkdir(self, dir_name):
        if not dir_name:
            return False

        if dir_name in self.current_dir.children:
            print(f"dir already exists: {dir_name}")
            return False

        new_dir = Directory(dir_name, self.current_dir)
        self.current_dir.add_child(new_dir)
        return True

    def touch(self, file_name, content=""):
        if not file_name:
            return False

        if file_name in self.current_dir.children:
            print("file already exists")
            return False

        new_file = File(file_name, content)
        self.current_dir.add_child(new_file)
        return True

    def dir(self):

        for mount_path, real_path in self.mount_points.items():
            if self.current_path.startswith(mount_path):
                rel_path = os.path.relpath(self.current_path, mount_path)
                real_full_path = os.path.join(real_path, rel_path)

                if not os.path.exists(real_full_path):
                    print("mounted path no longer exists")
                    return False

                if not os.path.isdir(real_full_path):
                    print("mounted path is not a dir")
                    return False

                return os.listdir(real_full_path)
        items = []
        for name, child in self.current_dir.children.items():
            if isinstance(child, Directory):
                items.append(f"{name}/")
            else:
                items.append(name)

        for mount_path in self.mount_points:
            mount_dir = os.path.dirname(mount_path)
            if mount_dir == self.current_path.rstrip("/")
                items.append(f"{os.path.basename(mount_path)}/ [mounted]")

        return items

    def mount(self, source, target):
        if not os.path.exists(source):
            print(f"source path is not exist: {source}")
            return False
        source = os.path.abspath(source)
        target_path = self._resolve_path(target)

        for mount_path in self.mount_points:
            if target.startswith(mount_path):
                print(f"cant mount inside already mounted vfs: {mount_path}")
                return False

        components = [c for c in target_path.split("/") if c]
        current = self.root

        for component in components[:-1]:
            child = current.get_child(component)
            if not isinstance(child, Directory):






if __name__ == "__main__":
    vfs = VFS()
    print("Virtual File System Initialized")
    while True:
        parser = cli()
        args = parser.parse_args()
        vfs.run(args)
