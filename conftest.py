import pytest


def pytest_configure(config):
    """
    This is run before testing starts (add properties to config

    :param config: Configuration for pytest
    """
    config.data_folder_path = ""
