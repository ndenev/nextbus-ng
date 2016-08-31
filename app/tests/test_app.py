import sys, os
import pytest

sys.path.insert(0, os.path.realpath(os.path.dirname(__file__)+"/.."))

def test_import():
    import nextbus

