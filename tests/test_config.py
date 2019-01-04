import pytest
import os
import configparser
from opennem import config, module_dir

test_config = configparser.RawConfigParser()
test_config.read(os.path.join(module_dir,'sample_config.ini'))

def test_config_sections():
    assert config.sections() == test_config.sections()

@pytest.mark.parametrize("section", config.sections())
def test_section_keys(section):
    assert test_config[section].keys() == config[section].keys()
