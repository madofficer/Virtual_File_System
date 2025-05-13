import argparse
from argparse import ArgumentParser


def cli():
    parser = ArgumentParser(description="get VFS command")

    subparser = parser.add_subparsers(dest="command", help="show available commands")

    ls_parser = subparser.add_parser("ls", help="list current dir")

    mount_parser = subparser.add_parser("mount", help="mount existing dir")

    cd_parser = subparser.add_parser("cd", help="change dir")
    cd_parser.add_argument("route", metavar='string')
    return parser


if __name__ == "__main__":
    parser = cli()
    args = parser.parse_args()
    print(args.route)
