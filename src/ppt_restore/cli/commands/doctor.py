"""Unified ``pptrestore`` command line interface.

Commands intentionally compose small core APIs.  Platform-specific rendering
and optimization modules are imported only for the command that needs them.
"""

from __future__ import annotations

from ppt_restore.platform.doctor import doctor


def run(args):
    print(doctor().to_json(indent=2))
    return 0
