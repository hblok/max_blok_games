# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

load("@rules_python//python:packaging.bzl", "py_wheel", "py_package")

py_library(
    name = "fish",
    srcs = glob(["*.py"]),
    data = ["Fish_small.png", "Fish.sh", "game.json"],
    deps = [
        "@games_pip_deps//pygame_ce",
    ],
    visibility = [":__subpackages__"],
)

py_package(
    name = "fish_package",
    packages = ["maxbloks"],
    deps = [
      ":fish",
    ]
)

py_wheel(
    name = "wheel",
    distribution = "fish",
    version = "$(fish-version)",
    deps = [ 
        ":fish_package",
    ],
)
