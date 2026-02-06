"""
Setup configuration for fusion-combustibles-lector package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="fusion-combustibles-lector",
    version="0.1.0",
    author="Kernel Informatica",
    description="Python bridge para leer despachos de combustibles de controladores Wayne Fusion",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kernelinformatica/fusion-combustibles-lector",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: Microsoft :: Windows",
    ],
    python_requires=">=3.6",
    install_requires=requirements,
    keywords="wayne fusion fuel dispenser combustibles surtidores",
)
