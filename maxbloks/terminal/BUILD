# Copyright (C) 2025 H. Blok
# SPDX-License-Identifier: GPL-3.0-or-later

load("@rules_python//python:packaging.bzl", "py_wheel", "py_package")

py_library(
    name = "terminal",
    srcs = [
        "main.py", "Terminal.sh",
    ],
    deps = [
        "//maxbloks/terminal/config",
        "//maxbloks/terminal/core",
        "//maxbloks/terminal/ui",
    ],
    visibility = [":__subpackages__"],
)

py_package(
    name = "terminal_package",
    packages = ["maxbloks"],
    deps = [
      ":terminal",
    ]
)

py_wheel(
    name = "wheel",
    distribution = "terminal",
    version = "$(terminal-version)",
    deps = [ 
        ":terminal_package",
    ],
)
