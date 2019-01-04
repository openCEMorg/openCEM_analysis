import pytest
import os
import configparser
from cemo_outputs import CONFIG, MODULE_DIR

test_config = configparser.RawConfigParser()
test_config.read(os.path.join(MODULE_DIR,'example_config.ini'))

def test_config_sections():
    assert CONFIG.sections() == test_config.sections()

@pytest.mark.parametrize("section", CONFIG.sections())
def test_section_keys(section):
    assert test_config[section].keys() == CONFIG[section].keys()
