import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="py-emmet",
    version="1.1.9",
    author="Sergey Chikuyonok",
    author_email="serge.che@gmail.com",
    description="Emmet is a web-developer’s toolkit for boosting HTML & CSS code writing.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/emmetio/py-emmet",
    include_package_data=True,
    packages=setuptools.find_packages(exclude=('tests', 'tests.*',)),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.3',
)
