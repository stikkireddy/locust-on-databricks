from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    install_requires = fh.read().splitlines()


setup(
    name="locust-on-databricks",
    author="Sri Tikkireddy",
    author_email="sri.tikkireddy@databricks.com",
    description="Run locust on single node or distributed on Databricks.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/stikkireddy/locust-on-databricks",
    packages=find_packages(),
    install_requires=install_requires,
    extras_require={
            'dev': [
                'pytest',
                'pytest-pep8',
                'pytest-cov',
                'pyspark==3.4.1',
                'twine'
            ]
        },
    setup_requires=["setuptools_scm"],
    use_scm_version=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache 2.0 License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
)
