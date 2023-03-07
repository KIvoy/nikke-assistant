# nikke-assistant
A python desktop app that helps with chores of a commander in Nikke: Godness of Victory

## Running packaged exe on windows
- download the zipped release package
- unzip to your desired location
- open Nikke: Godness of Victory game application
- run the NikkeAssistant.exe

## Running Source Code on Windows
- have requirments installed from `requirements.txt`
- have python installed
- have tesseract installed and pointed to the right directory
- run `py nikke_interface.py`
- to generate locale files you might want to run `py setup.py compile_catalog --domain nikke-assistant --directory ./locale --locale zh`, replace the locale with corresponding locale.
- a windows application should start
- (optional) you might need to give it admin permission for some of the functions to work

## Packing to .exe on Windows
- create virtual environment if have not done so `py -m venv venv`
- start the virtual environment `& ./venv/Scripts/Activate.ps1`
- install the requirements `pip install -r requirements.txt`
- run the packaging command `bash package.sh`, make sure to change the directories
    - or alternatively use auto-py-to-exe to package everything
- collect the packaged folder from either `dist` or `output` directory depending on which method you used, or your custom directory

## Language Support
- you can change the game language and the ui language in `NIKKE_ASSISTANT.INI`
    - so far `en` for English and `zh` for Simplified Chinese
    - support for English client is not yet implemented, you might run into some errors
    - feel free to create the assets in your language to support the corrensponding client.

## Releases
- you can download the latest release in the corresponding release tag

