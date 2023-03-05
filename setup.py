from babel.messages.frontend import extract_messages
from babel.messages.frontend import compile_catalog

from setuptools import setup, find_packages

setup(
    name='nikke-assistant',
    version='0.1.0',
    packages=find_packages(include=['nikke-assistant', 'nikke-assistant.*'])
)

[extract_messages]
input_dir = 'nikke-assistant'
output_file = 'nikke-assistant/locale/nikke-assistant.pot'


[compile_catalog]
domain = "./"
directory = "./locale"