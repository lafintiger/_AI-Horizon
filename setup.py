from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="aih-pipeline",
    version="0.1.0",
    author="AI-Horizon Research Team",
    author_email="research@csusb.edu",
    description="AI-Horizon: Cybersecurity Workforce Evolution Forecasting Pipeline",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/csusb/ai-horizon",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Researchers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "aih=aih.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "aih": ["*.yaml", "*.json", "data/*"],
    },
) 