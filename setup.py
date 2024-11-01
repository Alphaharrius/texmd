from setuptools import setup, find_packages

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="texmd",
    version="0.0.2",
    description="A simple library that translates LaTeX to Markdown.",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Alphaharrius/texmd",
    author="Alphaharrius",
    author_email="me@alphaharrius.cc",
    license="Apache-2.0",
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "pydantic",
        "pylatexenc",
        "pybtex",
    ],
    extras_require={
        "dev": [
            "pytest",
            "twine"
        ]
    },
    python_requires=">=3.9",
)
