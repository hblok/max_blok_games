"""Custom py_wheel that reads version from version.json."""

load("@rules_python//python:packaging.bzl", "py_wheel", "py_package")

def py_package_wheel(name, deps, **kwargs):
    """
    Create a py_wheel with version read from version.json.
    
    Args:
        name: Name of the wheel target
        deps: Dependencies (typically a py_library)
        **kwargs: Additional arguments passed to py_wheel
    """
    package_name = name + "_package"
    
    # Create py_package
    py_package(
        name = package_name,
        packages = ["maxbloks"],
        deps = deps,
    )
    
    py_wheel(
        name = "wheel",
        distribution = name,
        version = "$(%s-version)" % name,
        deps = [":" + package_name],
        **kwargs
    )
