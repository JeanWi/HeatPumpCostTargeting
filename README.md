[//]: # ([![Documentation Status]&#40;https://readthedocs.org/projects/xxxxxx/badge/?version=latest&#41;]&#40;https://xxxxxx.readthedocs.io/en/latest/?badge=latest&#41;)

[//]: # (![Testing]&#40;https://github.com/xxxxxx/actions/workflows/00deploy.yml/badge.svg?branch=develop&#41;)

[//]: # ([![codecov]&#40;https://codecov.io/gh/xxxxxx/graph/badge.svg?token=RVR402OGG0&#41;]&#40;https://codecov.io/gh/xxxxxx&#41;)

[//]: # ([![Code style: black]&#40;https://img.shields.io/badge/code%20style-black-000000.svg&#41;]&#40;https://github.com/psf/black&#41;)

[//]: # ([![PyPI version]&#40;https://badge.fury.io/py/xxxxxx.svg&#41;]&#40;https://pypi.org/project/xxxxxx/&#41;)


# Python-Template
This python template includes:
- Testing including code coverage with github CI
- Possibility to have a readthedocs page
- CI workflow to publish the package on PyPI

Please adapt the branch protection rules after creating a repository from this template. It's easiest to 
export the rules from this repository and import them again to the new repository.

## Testing
### In github CI
Adapt .github/workflows/testing.yml with Python version, other packages,...

### Codecov
Get a codecov account and connect the repository. You need to add a codecov token to the repository

## Readthedocs/Sphinx
- Make sure sphinx is installed in your virtual environment
- Navigate to the docs directory in the terminal
- Run sphinx-quickstart from the terminal and enter all required details
- Get a readthedocs account and connect the repository to readthedocs

## Status Badges in readme file
To show the status badges, comment in the first lines in this file and change the URLs respectively.

## Publishing on PyPI
The repository needs to be connected to a PyPI account and a token needs to be added to the repository. Refer to other
recources on how this works. Test the release first with TestPyPI. The workflow to publish on PyPI is triggered by
generating a new release on GitHub

## Workflow
- The main branch is protected and holds the most recent released version
- The develop branches hold the latest developments for the next version. Naming convention: develop_vMAJOR.MINOR.BUGFIX
- A feature branch is created and merged on the most recent develop branch via a PR
- Any PR on a develop branch is tested and can only be merged after tests have passed
- Merging a develop branch into main tests again
- Releases to PyPI are triggered by making a new release
