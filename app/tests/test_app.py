import sys, os
import pytest

sys.path.insert(0, os.path.realpath(os.path.dirname(__file__)+"/.."))


def test_import_and_create_app():
    from nextbus import create_app
    assert(create_app())
