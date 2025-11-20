from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="duck",
    version="1.0.0",
    author="Your Name",  # Replace with your name
    author_email="your.email@example.com",  # Replace with your email
    description="A short description of duck",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kaustubhbhal/duck",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        # Add your dependencies here, e.g.:
        # "requests>=2.25.0",
    ],
    entry_points={
        "console_scripts": [
            "duck=duck.cli:main",
        ],
    },
)
