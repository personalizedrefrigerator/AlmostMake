import setuptools
from almost_make.version import VERSION_STRING

readmeFile = open("README.md", "r")
longDescription = readmeFile.read()
readmeFile.close()

setuptools.setup(
    name="almost_make",
    version=VERSION_STRING,
    author="Henry Heino",
    author_email="personalizedrefrigerator@gmail.com",
    description="A pure-Python implementation of make.",
    long_description=longDescription,
    long_description_content_type="text/markdown",
    url="https://github.com/personalizedrefrigerator/AlmostMake",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Development Status :: 3 - Alpha",

        "Operating System :: OS Independent",

        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",

        "Environment :: Console"
    ],
    keywords=['make', 'almake', 'bsdmake', 'gnumake', 'Makefile', 'cli'],
    entry_points={
        "console_scripts": [
            "almake = almost_make.cli:main",
            "almake_shell = almost_make.utils.shellUtil.interactiveShell:main"
        ]
    },
    python_requires=">=3.6.8"
)
