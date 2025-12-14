from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='caldera-orchestrator',
    version='1.0.0',
    description='Global orchestration pattern for MITRE Caldera',
    author='Triskele Labs',
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'caldera-orchestrator=orchestrator.cli.main:main',
        ],
    },
    python_requires='>=3.8',
    include_package_data=True,
    package_data={
        'orchestrator.schemas': ['*.json', '*.yml'],
        'orchestrator.agents.templates': ['*.j2'],
    },
)
