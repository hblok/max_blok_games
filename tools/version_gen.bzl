def _gen_version_impl(ctx):
    """Generate version.py """
    
    # Get version from workspace status
    version = ctx.var.get("SBCMAN_VERSION", "0.0.0-dev")
    
    output = ctx.actions.declare_file("version.py")
    ctx.actions.write(
        output = output,
        content = 'VERSION = "{}"\n'.format(version),
    )
    
    # Return PyInfo so it can be used in py_library deps
    return [
        DefaultInfo(files = depset([output])),
        PyInfo(
            transitive_sources = depset([output]),
            imports = depset([]),
        ),
    ]

gen_version = rule(
    implementation = _gen_version_impl,
    attrs = {},
)
