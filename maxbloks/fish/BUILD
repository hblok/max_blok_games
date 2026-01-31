# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

load("@rules_python//python:packaging.bzl", "py_wheel", "py_package")

py_library(
    name = "fish",
    srcs = glob(["*.py"]),
    data = ["Fish_small.png", "Fish.sh"]
)

py_package(
    name = "fish_package",
    packages = ["maxbloks"],
    deps = [
      ":fish",
    ]
)

py_wheel(
    name = "fish_wheel",
    distribution = "fish",
    version = "0.1.8",
   deps = [
        ":fish_package",
    ],
)
