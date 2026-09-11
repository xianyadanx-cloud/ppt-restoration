"""Image-to-PPT runtime. The CLI and SceneSpec v2 are the public interfaces."""


def main(argv=None):
    from .cli import main as run

    return run(argv)
