# Copyright (C) 2026 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

load("//tools:py_package_wheel.bzl", "py_package_wheel")

py_library(
    name = "tankbattle",
    srcs = glob(["*.py"]),
    data = [
        "Tankbattle.sh",
        "game.json",
        "version.json",
    ],
    deps = [
        "//maxbloks/common",
        "@games_pip_deps//pygame_ce",
    ],
    visibility = [":__subpackages__"],
)

py_package_wheel(
    name = "tankbattle",
    deps = [":tankbattle"],
)
