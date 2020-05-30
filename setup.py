from setuptools import setup

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="chime",
    version="1.0.0",
    description="A scalable, intuitive and easy-to-use music bot for Discord.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="realmayus",
    author_email="realmayus@gmail.com",
    packages=["chime"],
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
    ]
)