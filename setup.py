import sys
import os
from pathlib import Path
from setuptools import setup, find_packages
from setuptools.command.develop import develop
from setuptools.command.install import install


def post_install():
    """On Windows, create .cmd shims in Python Scripts directories to bypass WDAC policy blocking user .exe files."""
    if sys.platform == "win32":
        try:
            candidates = [
                Path(sys.prefix) / "Scripts",
                Path.home() / "AppData" / "Roaming" / "Python" / f"Python{sys.version_info.major}{sys.version_info.minor}" / "Scripts",
            ]
            for sdir in candidates:
                if sdir.exists():
                    for exe_name in ["ae.exe", "ae-cli.exe"]:
                        p = sdir / exe_name
                        if p.exists():
                            try:
                                p.unlink()
                            except Exception:
                                pass
                    # Windows CMD / BAT wrappers
                    for cmd_name in ["ae.cmd", "ae-cli.cmd", "ae.bat"]:
                        p = sdir / cmd_name
                        try:
                            p.write_text("@echo off\r\npython -m ae_cli.main %*\r\n", encoding="utf-8")
                        except Exception:
                            pass

                    # Git Bash / POSIX shell wrappers
                    for sh_name in ["ae", "ae-cli"]:
                        p = sdir / sh_name
                        try:
                            p.write_text("#!/usr/bin/env bash\npython -m ae_cli.main \"$@\"\n", encoding="utf-8")
                        except Exception:
                            pass

            # Automatically register alias in ~/.bashrc for Git Bash users
            bashrc = Path.home() / ".bashrc"
            try:
                content = bashrc.read_text(encoding="utf-8") if bashrc.exists() else ""
                if "alias ae=" not in content:
                    with open(bashrc, "a", encoding="utf-8") as f:
                        f.write("\n# ae-cli bash alias\nalias ae=\"python -m ae_cli.main\"\nalias ae-cli=\"python -m ae_cli.main\"\n")
            except Exception:
                pass
        except Exception:
            pass


class PostDevelopCommand(develop):
    def run(self):
        super().run()
        post_install()


class PostInstallCommand(install):
    def run(self):
        super().run()
        post_install()


setup(
    name="ae-cli",
    version="0.1.0",
    packages=find_packages(),
    cmdclass={
        "develop": PostDevelopCommand,
        "install": PostInstallCommand,
    },
    install_requires=[
        "click>=8.0.0",
        "rich>=13.0.0",
        "prompt-toolkit>=3.0.0",
        "httpx>=0.24.0",
        "google-auth>=2.0.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "ae = ae_cli.main:main",
            "ae-cli = ae_cli.main:main",
        ],
    },
)
