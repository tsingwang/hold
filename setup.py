from setuptools import setup, find_packages


setup(
    name="hold",
    version="0.1.0",
    author="Tsing Wang",
    author_email="tsing.nix@outlook.com",
    description="A simple trading statistics tool",
    long_description=open('README.md', 'r').read(),
    long_description_content_type='text/markdown',
    url="https://github.com/tsingwang/hold",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "hold = hold.cli:cli",
        ],
    },
    install_requires=[
        "click",
        "pandas",
        "rich",
        "SQLAlchemy",
    ],
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
)
