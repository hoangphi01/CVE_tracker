from setuptools import setup, find_packages

setup(
    name="cve-tracker",
    version="1.0.0",
    description="macOS menu bar app that tracks CVE publication status via MITRE API",
    author="Hoang Phi",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "rumps>=0.4.0",
        "pyobjc-core>=10.0",
        "pyobjc-framework-Cocoa>=10.0",
    ],
    entry_points={
        "console_scripts": [
            "cve-check=cve_tracker.cli:main",
            "cve-menubar=cve_tracker.menubar:main",
        ],
    },
)
