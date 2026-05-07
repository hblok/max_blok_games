# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

load("@rules_python//python:defs.bzl", "py_library")

py_library(
    name = "networktest",
    srcs = glob(["*.py"]),
    data = ["Network.sh", "game.json"],
    deps = [
        "//maxbloks/common",
        "@games_pip_deps//pygame_ce",
    ],
    visibility = [":__subpackages__"],
)
