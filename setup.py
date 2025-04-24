from setuptools import setup, find_packages

setup(
    name="xml-patcher",
    version="1.0.0",
    description="A tool for patching and modifying XML files with YAML configuration",
    author="Franck L.",
    author_email="fcl@aubonrepas.com",
    packages=find_packages(include=['xml_patcher', 'xml_patcher.*']),
    # package_dir={'': 'src'},  <-- Removed this line
    package_data={
        'xml_patcher': ['templates/*', 'config/*'],
    },
    install_requires=[
        "pyyaml>=6.0",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "xml-patcher=xml_patcher.patcher:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
) 
