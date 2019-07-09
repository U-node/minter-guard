import setuptools
import codecs

with codecs.open("README.md", "r", 'utf_8_sig') as fh:
    long_description = fh.read()

setuptools.setup(
    name="minterguard",
    version="1.0.3",
    author="U-node Team",
    author_email="rymka1989@gmail.com",
    description=u"Python Guard for Minter Nodes",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/U-node/minter-guard",
    packages=setuptools.find_packages(include=['minterguard']),
    include_package_data=True,
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    )
)
