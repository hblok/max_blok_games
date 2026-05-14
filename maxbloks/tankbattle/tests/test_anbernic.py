# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

import platform
import unittest
from unittest import mock

from maxbloks.tankbattle import anbernic


class TestIsAnbernicDevice(unittest.TestCase):

    def test_returns_bool(self):
        self.assertIsInstance(anbernic.is_anbernic_device(), bool)

    def test_false_on_non_linux(self):
        with mock.patch("platform.system", return_value="Darwin"):
            self.assertFalse(anbernic.is_anbernic_device())

    def test_false_on_windows(self):
        with mock.patch("platform.system", return_value="Windows"):
            self.assertFalse(anbernic.is_anbernic_device())

    def test_true_when_hostname_contains_anbernic(self):
        with mock.patch("platform.system", return_value="Linux"), \
             mock.patch("socket.gethostname", return_value="ANBERNIC"):
            self.assertTrue(anbernic.is_anbernic_device())

    def test_true_when_hostname_lowercase_anbernic(self):
        with mock.patch("platform.system", return_value="Linux"), \
             mock.patch("socket.gethostname", return_value="anbernic-rg35xx"):
            self.assertTrue(anbernic.is_anbernic_device())

    def test_false_when_linux_no_anbernic_hostname_no_dt(self):
        with mock.patch("platform.system", return_value="Linux"), \
             mock.patch("socket.gethostname", return_value="mypc"), \
             mock.patch("os.path.exists", return_value=False):
            self.assertFalse(anbernic.is_anbernic_device())

    def test_hostname_exception_falls_through(self):
        with mock.patch("platform.system", return_value="Linux"), \
             mock.patch("socket.gethostname", side_effect=OSError("no socket")), \
             mock.patch("os.path.exists", return_value=False):
            self.assertFalse(anbernic.is_anbernic_device())

    def test_true_on_h616arm_device_tree(self):
        dt_content = "allwinner,h616arm"
        with mock.patch("platform.system", return_value="Linux"), \
             mock.patch("socket.gethostname", return_value="trimui"), \
             mock.patch("os.path.exists", return_value=True), \
             mock.patch("builtins.open", mock.mock_open(read_data=dt_content)):
            self.assertTrue(anbernic.is_anbernic_device())

    def test_true_on_sun50iw9_device_tree(self):
        dt_content = "allwinner,sun50iw9p1"
        with mock.patch("platform.system", return_value="Linux"), \
             mock.patch("socket.gethostname", return_value="rg35xx"), \
             mock.patch("os.path.exists", return_value=True), \
             mock.patch("builtins.open", mock.mock_open(read_data=dt_content)):
            self.assertTrue(anbernic.is_anbernic_device())

    def test_false_on_linux_unknown_device_tree(self):
        dt_content = "raspberry,pi4b"
        with mock.patch("platform.system", return_value="Linux"), \
             mock.patch("socket.gethostname", return_value="raspberrypi"), \
             mock.patch("os.path.exists", return_value=True), \
             mock.patch("builtins.open", mock.mock_open(read_data=dt_content)):
            self.assertFalse(anbernic.is_anbernic_device())
