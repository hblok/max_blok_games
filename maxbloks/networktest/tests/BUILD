# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

load("@rules_python//python:defs.bzl", "py_test")

py_test(
    name = "test_constants",
    srcs = ["test_constants.py"],
    deps = ["//maxbloks/networktest", "@games_pip_deps//pygame_ce"],
)

py_test(
    name = "test_connection_manager",
    srcs = ["test_connection_manager.py"],
    deps = ["//maxbloks/networktest", "@games_pip_deps//pygame_ce"],
)

py_test(
    name = "test_network_discovery",
    srcs = ["test_network_discovery.py"],
    deps = ["//maxbloks/networktest", "@games_pip_deps//pygame_ce"],
)
