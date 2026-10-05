"""Supervisor is the entry point; it launches A Core, which launches its body bridge."""

import sys

from supervisor.supervisor import cli

def run(argv=None):
    arguments = list(sys.argv[1:] if argv is None else argv)
    if not arguments:
        from launcher import show_launcher
        try:
            selection = show_launcher()
        except RuntimeError as error:
            print(str(error), file=sys.stderr)
            return 1
        if selection is None:
            return 0
        arguments = selection.arguments()
    original = sys.argv
    try:
        sys.argv = [original[0], *arguments]
        return cli()
    finally:
        sys.argv = original


if __name__ == '__main__':
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='backslashreplace', line_buffering=True)
    raise SystemExit(run())
