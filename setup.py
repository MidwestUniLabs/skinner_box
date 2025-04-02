import re
from setuptools import setup, find_packages

# Extract the version from __init__.py
def get_version():
    with open("skinnerbox_source/__init__.py", "r") as init_file:
        for line in init_file:
            match = re.match(r"^__version__ = ['\"]([^'\"]+)['\"]", line)
            if match:
                return match.group(1)
    raise RuntimeError("Version not found in __init__.py")

setup(
    name="Skinnerbox-Source",
    version=get_version(),  # Dynamically set the version
    description="Source Code for the Skinner Box by Midwest UniLabs",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="JDykman",
    author_email="jake@midwestunilabs.com",
    url="https://github.com/JDykman/skinner_box",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "blinker==1.9.0",
        "certifi==2025.1.31",
        "cffi==1.17.1",
        "charset-normalizer==3.4.1",
        "click==8.1.8",
        "colorama==0.4.6",
        "colorzero==2.0",
        "cryptography==44.0.2",
        "DateTime==5.5",
        "Deprecated==1.2.18",
        "dotenv==0.9.9",
        "et_xmlfile==2.0.0",
        "Flask==3.1.0",
        "Flask-Limiter==3.10.1",
        "gpiozero==2.0.1",
        "idna==3.10",
        "itsdangerous==2.2.0",
        "Jinja2==3.1.5",
        "limits==4.0.1",
        "markdown-it-py==3.0.0",
        "MarkupSafe==3.0.2",
        "mdurl==0.1.2",
        "Nuitka==2.6.6",
        "openpyxl==3.1.5",
        "ordered-set==4.1.0",
        "packaging==24.2",
        "pycparser==2.22",
        "Pygments==2.19.1",
        "python-dotenv==1.0.1",
        "pytz==2025.1",
        "requests==2.32.3",
        "rich==13.9.4",
        "setuptools==75.8.0",
        "typing_extensions==4.12.2",
        "urllib3==2.3.0",
        "Werkzeug==3.1.3",
        "wrapt==1.17.2",
        "zope.interface==7.2",
        "zstandard==0.23.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)