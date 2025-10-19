from setuptools import setup, find_packages

setup(
    name="colorchangerPDF",
    version="1.0.0",
    author="emir alakus",
    author_email="emirabdullah2007@gmail.com",
    description="Convert PDFs to dark mode safely, locally using Python",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Abdullah-js/colorchangerPDF",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "pymupdf",
        "pillow",
        "numpy",
        "tqdm"
    ],
    entry_points={
        "console_scripts": [
        "colorchangerPDF=colorchangerPDF.script:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)