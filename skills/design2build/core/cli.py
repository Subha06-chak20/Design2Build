"""
Design2Build (d2b) CLI Entrypoint
=================================
Trampoline forwarding to d2b_core.cli.
"""

from d2b_core.cli import cli

if __name__ == "__main__":
    cli()
