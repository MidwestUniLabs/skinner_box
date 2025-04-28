from setuptools import setup, find_packages

# Read version from version.txt
with open("version.txt", "r") as f:
    version = f.read().strip()

# Read requirements from requirements.txt
with open("requirements.txt", "r") as f:
    requirements = [line.strip() for line in f.readlines() if line.strip() and not line.startswith("#")]

setup(
    name="Skinnerbox-Source",
    version=version,
    description="Source Code for the Skinner Box by Midwest UniLabs",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="JDykman",
    author_email="jake@midwestunilabs.com",
    url="https://github.com/JDykman/skinner_box",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)