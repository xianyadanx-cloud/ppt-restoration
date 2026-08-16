#!/usr/bin/env python3
"""Skill: Layout Auditor - Static Layout Constraint Assertion Engine."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from tools.layout_linter import audit_layout, main

if __name__ == "__main__":
    main()
