# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

load("@rules_python//python:packaging.bzl", "py_wheel", "py_package")
load("//tools:py_package_wheel.bzl", "py_package_wheel")

py_library(
    name = "dogrider",
    srcs = glob(["*.py"]),
    data = ["Dogrider.png", "Dogrider.sh", "game.json"],
    deps = [
        "@games_pip_deps//pygame_ce",
    ],
    visibility = [":__subpackages__"],
)

py_package_wheel(
    name = "dogrider",
    deps = [":dogrider"]
)
