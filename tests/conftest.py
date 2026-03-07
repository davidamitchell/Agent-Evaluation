"""
Shared pytest fixtures and path configuration.

Setup (pip install, CLI installation) lives in the CI workflow, not here.
"""
import os
import sys

# Make the scripts package importable without installing it.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
