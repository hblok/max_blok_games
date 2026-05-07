# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

load("@rules_python//python:packaging.bzl", "py_wheel", "py_package")
load("//tools:py_package_wheel.bzl", "py_package_wheel")

py_library(
    name = "tanks",
    srcs = glob(["*.py"]),
    data = ["Tanks.sh", "game.json", "Tanks.png"],
    deps = [
        "//maxbloks/common",
        "@games_pip_deps//pygame_ce",
    ],
    visibility = [":__subpackages__"],
)

py_package_wheel(
    name = "tanks",
    deps = [":tanks"]
)
