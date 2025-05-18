import argparse
from argparse import ArgumentParser


def cli():
    parser = ArgumentParser(description="get VFS command")

    subparser = parser.add_subparsers(dest="command", help="show available commands")

    dir_parser = subparser.add_parser("dir", help="list current dir")
    ls_parser = subparser.add_parser("ls", help="list current dir")

    mount_parser = subparser.add_parser("mount", help="mount existing dir")
    mount_parser.add_argument("source", help="real path")
    mount_parser.add_argument("target", help="virtual path")

    unmount_parser = subparser.add_parser("unmount", help="unmount [mounted] dir")
    unmount_parser.add_argument("mounted_path", help="path to [mounted] dir in vfs")

    cd_parser = subparser.add_parser("cd", help="change dir")
    cd_parser.add_argument("path", metavar='string')

    mkdir_parser = subparser.add_parser("mkdir", help="make dir")
    mkdir_parser.add_argument("dir_name", metavar="string")

    rm_parser = subparser.add_parser("rm", help="remove dir")
    rm_parser.add_argument("dir_name", metavar="string")

    touch_parser = subparser.add_parser("touch", help="create file")
    touch_parser.add_argument("file_name", help="file name")
    touch_parser.add_argument("content", default="", help="file content")

    save_parser = subparser.add_parser("save", help="save current vfs state")
    save_parser.add_argument("file_name", default="vfs_state.json", help="state name")

    load_parser = subparser.add_parser("load", help="load existing vfs state")
    load_parser.add_argument("file_name", default="vfs_state.json", help="existing state name")

    return parser


if __name__ == "__main__":
    parser = cli()
    args = parser.parse_args()
    print(args.route)
