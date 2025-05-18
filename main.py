import json
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
        self.parent: Directory | None = parent
        self.children = {}
        self.mounted = False

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

    def repr(self):
        return self.name


class VFS:
    def __init__(self):
        self.root = Directory("root/", parent=None)
        self.current_dir = self.root
        self.current_path = "/"
        self.mount_points = {}

    def run(self) -> None:
        print("Virtual File System. Type '--help' for commands")
        try:
            while True:
                parser = cli()
                prompt = input(self.upd_prompt()).strip()
                if not prompt:
                    continue

                try:
                    args = parser.parse_args(prompt.split())
                except SystemExit:
                    continue

                match args.command:
                    case "cd":
                        self.cd(args.path)
                    case "mkdir":
                        self.mkdir(args.dir_name)
                    case "mount":
                        self.mount(args.source, args.target)
                    case "unmount":
                        self.unmount(args.mounted_path)
                    case "dir" | "ls":
                        self.dir()
                    case "touch":
                        self.touch(args.file_name, args.content)
                    case "save":
                        self.save_to_file(args.file_name)
                    case "load":
                        self.load_from_file(args.file_name)

        except KeyboardInterrupt:
            print("vfs killed")
        except Exception as err:
            print(f"Exception raised [{err}]")

    def _resolve_path(self, path):
        path = path.replace("\\", "/").strip()
        if not path.startswith("/"):
            path = os.path.join(self.current_path, path)
        return path + "/"

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

    def cd(self, path) -> bool:
        if not path:
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

        if current == self.root:
            self.current_path = "/"
            return

        while current is not None and current != self.root:
            path_parts.append(current.name)
            current = current.parent

        self.current_path = "/" + "/".join(reversed(path_parts)) + "/"
        print(self.current_path)

    def mkdir(self, dir_name: str) -> bool:
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

                print(os.listdir(real_full_path))
        items = []
        for name, child in self.current_dir.children.items():
            if isinstance(child, Directory):
                items.append(f"{name}/")
            else:
                items.append(name)

        for mount_path in self.mount_points:
            mount_dir = os.path.dirname(mount_path)
            if mount_dir == self.current_path.rstrip("/"):
                items.append(f"{os.path.basename(mount_path)}/ [mounted]")

        print(*items)

    def mount(self, source: str, target: str) -> bool:
        if not os.path.isdir(source):
            print(f"source is not a directory: {source}")
            return False

        original_path = self.current_path
        original_dir = self.current_dir

        try:
            if not self.cd(target):
                print('target dir doesnt exists')
                return False

            if self.current_dir.mounted:
                print("Cant mount into already mounted dir")
                return False
            mount_point = self.current_dir
            self.current_dir.mounted = True

            for root, dirs, files in os.walk(source):
                rel_path = os.path.relpath(root, source)
                if rel_path == '.':
                    rel_path = ''

                self.current_dir = mount_point
                if rel_path:
                    for part in rel_path.split(os.sep):
                        if not self.cd(part):
                            if not self.mkdir(part):
                                print(f"Failed to create directory: {part}")
                                return False
                            self.cd(part)

                for file_name in files:
                    if file_name not in self.current_dir.children:
                        file_path = os.path.join(root, file_name)
                        try:
                            with open(file_path, 'r') as f:
                                content = f.read()
                            self.touch(file_name, f"[Mounted] {content[:100]}...")
                        except Exception as e:
                            self.touch(file_name, f"[Mounted file: {file_path}]")

            self.mount_points[self._resolve_path(target)] = source
            return True

        finally:
            self.current_path = original_path
            self.current_dir = original_dir

    def unmount(self, path):
        target_path = self._resolve_path(path)

        if target_path in self.mount_points:
            del self.mount_points[target_path]
            print(f"unmounted: {target_path}")
            return True
        else:
            print(f"no mount point at: {target_path}")
            return False

    def save_to_file(self, file_name):
        data = {
            "root": self.root.to_dict(),
            "current_path": self.current_path,
            "mount_points": self.mount_points
        }

        try:
            with open(file_name, "w") as f:
                json.dump(data, f, indent=2)
            print(f"vfs saved to {file_name}")
            return True
        except Exception as err:
            print(f"Error saving vfs {err}")

    def load_from_file(self, file_name):
        if not os.path.exists(file_name):
            print(f"file not found: {file_name}")
            return False

        try:
            with open(file_name, "r") as file:
                data = json.load(file)

            self.root = Directory.from_dict(data["root"])
            self.current_path = data["current_path"]
            self.mount_points = data.get("mount_points", {})

            self.current_dir = self._find_dir(self.current_path)
            if not self.current_dir:
                print(f"Warning: Current path not found after load, resetting to root")
                self.current_dir = self.root
                self.current_path = "/"

            print(f"vfs loaded from {file_name}")
            return True
        except Exception as err:
            print(f"error loading vfs {err}")
            return False

    def upd_prompt(self) -> str:
        return f"VFS:{self.current_path}>"


if __name__ == "__main__":
    vfs = VFS()
    vfs.run()
