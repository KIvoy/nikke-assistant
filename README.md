# nikke-assistant
A python desktop app that helps with chores of Nikke: Godness of Victory

## Running on Windows
- have requirments installed from `requirements.txt`
- have python installed
- run `py nikke_interface.py`
- a windows application should start
- (optional) you might need to give it admin permission for some of the functions to work

## Packing to .exe on Windows
- create virtual environment if have not done so `py -m venv venv`
- start the virtual environment `& ./venv/Scripts/Activate.ps1`
- install the requirements `pip install -r requirements.txt`
- run the packaging command `bash package.sh`
- collect the packaged folder from the default `output` directory
