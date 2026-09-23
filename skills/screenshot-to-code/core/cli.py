"""
Screenshot-to-Code (stc) CLI Entrypoint
======================================
Trampoline forwarding to stc_core.cli.
"""

from stc_core.cli import cli

if __name__ == "__main__":
    cli()
