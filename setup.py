from babel.messages.frontend import extract_messages
from babel.messages.frontend import compile_catalog

from setuptools import setup, find_packages

setup(
    name='nikke-assistant',
    version='1.3.2',
    packages=find_packages(include=['nikke-assistant', 'nikke-assistant.*'])
)

[extract_messages]
input_dir = './'
output_file = './locale/nikke-assistant.pot'


[compile_catalog]
domain = "nikke-assistant"
directory = "./locale"