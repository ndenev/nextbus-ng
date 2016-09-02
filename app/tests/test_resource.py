import pytest

from nextbus.resources import Agency, Routes, RouteSchedule, RouteConfig


def test_agency():
    agency = Agency()
    agency.get()
