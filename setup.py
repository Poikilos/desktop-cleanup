from setuptools import setup, find_packages

setup(
    name="desktop-cleanup",
    version="0.1.0",
    author="Poikilos",
    author_email="7557867+Poikilos@users.noreply.github.com",
    description="A GUI tool to scan and clean up shortcut files from user and public desktops.",
    long_description="""Desktop Cleanup is a Python-based GUI application using Tkinter and tksheet.
    It scans user and public desktop folders for shortcuts, displays them in a spreadsheet-like view,
    and allows users to clean them up by moving them to designated folders.""",
    long_description_content_type="text/plain",
    url="https://github.com/Poikilos/desktop-cleanup",
    packages=find_packages(),
    install_requires=[
        "tksheet",
        "setuptools"
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Desktop Environment",
        "Topic :: System :: Filesystems",
        "Topic :: Utilities",
    ],
    python_requires=">=3.6",
    entry_points={
        "gui_scripts": [
            "desktop-cleanup=desktopcleanup.gui_main:main"
        ]
    },
)
