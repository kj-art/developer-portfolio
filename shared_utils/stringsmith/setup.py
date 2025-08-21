"""
Setup script for StringSmith package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="stringsmith",
    version="0.1.0",
    author="StringSmith Developer",
    description="Advanced template formatting with conditional sections and inline formatting",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing",
    ],
    python_requires=">=3.7",
    install_requires=[
        # No required dependencies for basic functionality
    ],
    extras_require={
        "colors": ["rich>=10.0.0"],
        "dev": ["pytest>=6.0.0", "pytest-cov>=2.0.0", "black>=21.0.0", "flake8>=3.8.0"],
    },
    keywords="template formatting string conditional sections ansi colors",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/stringsmith/issues",
        "Source": "https://github.com/yourusername/stringsmith",
    },
)