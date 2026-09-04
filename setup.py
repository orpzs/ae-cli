from setuptools import setup, find_packages

setup(
    name="ae-cli",
    version="0.1.0",
    packages=find_packages(),
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
