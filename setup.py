from setuptools import setup
from chime.main import version

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="chime-discord",
    version=version,
    description="A scalable, intuitive and easy-to-use music bot for Discord.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="realmayus",
    url="https://github.com/realmayus/chime",
    author_email="realmayus@gmail.com",
    license="GPLv3",
    packages=["chime", "chime.cogs", "chime.misc"],
    install_requires=["discord"],
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Telecommunications Industry",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
        "Topic :: Communications",
        "Topic :: Communications :: Conferencing",
        "Topic :: Multimedia :: Sound/Audio :: Players"
    ],
    entry_points={
        "console_scripts": [
            "chime=chime.main:start"
        ]
    }
)
