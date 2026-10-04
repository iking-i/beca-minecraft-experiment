"""Supervisor is the entry point; it launches A Core, which launches its body bridge."""

import sys

from supervisor.supervisor import cli

if __name__ == '__main__':
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='backslashreplace', line_buffering=True)
    raise SystemExit(cli())
