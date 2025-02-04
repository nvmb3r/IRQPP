import setuptools

# with open("README.md", "r") as fh:
#     long_description = fh.read()

setuptools.setup(
    name="qpputils",  # Replace with your own username
    version="0.0.1",
    scripts=['qpputils/dataparser.py', 'qpputils/functions.py'],
    author="Oleg Zendel",
    author_email="oleg.zendel@rmit.edu.au",
    description="Utility modules for QPP package",
    long_description="Utility modules for QPP development in python",
    long_description_content_type="text/markdown",
    url="https://github.com/Zendelo/IRQPP",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
