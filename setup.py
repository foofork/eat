from setuptools import setup, find_packages

setup(
    name="eat-framework",
    version="0.1.0",
    description="Ephemeral Agent Toolkit - One-hop tool discovery for AI agents",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="EAT Framework Team",
    author_email="team@eat-framework.org",
    url="https://github.com/eat-framework/eat-framework",
    packages=find_packages(),
    install_requires=[
        "aiohttp>=3.8.0",
        "cryptography>=3.4.0",
        "pyjwt[crypto]>=2.0.0",
        "click>=8.0.0",
        "pydantic>=1.8.0",
        "requests>=2.25.0",
        "pyyaml>=5.4.0",
        "jsonschema>=3.2.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-asyncio>=0.18.0",
            "pytest-cov>=2.12.0",
            "black>=21.0.0",
            "flake8>=3.9.0",
            "mypy>=0.910",
        ]
    },
    entry_points={
        'console_scripts': [
            'eat-gen=eat.cli.main:generate',
            'eat-serve=eat.cli.main:serve',
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)