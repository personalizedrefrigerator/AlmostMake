import setuptools

readmeFile = open("README.md", "r")
longDescription = readmeFile.read()
readmeFile.close()

setuptools.setup(
    name="almost_make",
    version="0.0.11",
    author="Henry Heino",
    author_email="personalizedrefrigerator@gmail.com",
    description="A makefile parser",
    long_description=longDescription,
    long_description_content_type="text/markdown",
    url="https://github.com/personalizedrefrigerator/AlmostMake",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Development Status :: 2 - Pre-Alpha"
    ],
    entry_points={
        "console_scripts": [
            "almake = almost_make.cli:main"
        ]
    },
    python_requires=">=3.7"
)
