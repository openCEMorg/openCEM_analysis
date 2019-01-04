"""simple test to ensure example_config.ini reflects actual config.ini used"""
import os
import configparser
import pytest
from cemo_outputs import CONFIG, MODULE_DIR

TEST_CONFIG = configparser.RawConfigParser()
TEST_CONFIG.read(os.path.join(MODULE_DIR, 'example_config.ini'))

def test_config_sections():
    """checks config sections are the same"""
    assert CONFIG.sections() == TEST_CONFIG.sections()

@pytest.mark.parametrize("section", CONFIG.sections())
def test_section_keys(section):
    """checks keys in each sections are the same"""
    assert TEST_CONFIG[section].keys() == CONFIG[section].keys()
