# Nikke Assistant
A python desktop app that helps with chores of a commander in Nikke: Godness of Victory

## Disclaimer

The software Nikke Assistant does not engage in any game file, memory or network traffic interference. It uses only image processing and input simulation to complete tasks that does not involve in either competing with another player or gaining unfair advantage over another player. Everything that can be done with the assistant can be done with a player manually. 

Although it is unlikely that you will get banned for using the assistant based on SU's history, the assistant is not responsible for any potential actions that could be taken by the game company due to your usage. 

<b>Please use at your own risk</b>.


## Running packaged exe on windows
- download the zipped release package
- unzip to your desired location
- open Nikke: Godness of Victory game application
- run the nikke-assistant.exe

## Common Issues
- <b>The assistant says "game window not found", simply does not start any task, or stops randomly at tasks</b>

Make sure to use the reload game function and check that your game window is resized to 591x1061. Most cases the assitant should work by then.

If the game window is still not found or if the window does not resize, it is likely that the assistant is not recognizing the name of the game window due to your client version. Use the select game window function to cycle through the list of applications and find your actual game window and then click on reload game again.

- <b>How do I use the Repeat Event Level function to repeat the events I'm currently in?</b>

Although the assistant will be updated every new event, it's only updated based on my preference in the level to repeat and may not suit your need.

It is very easy to adjust the files to your own levels to repeat ahead of time. Simply screenshot all the images you would click from the Events page all the way to the level you want to repeat. Store all those screenshots in `images/nikke/home/event/<your event name>/` and name them in order as `step_1.png`, `step_2.png` etc. You can check out the screenshot examples from previous events in the same directory if you need. In the end, don't forget to change in the settings the event to repeat to <your event name> that you've just created. Now when you click on repeat event levels, it should repeat exactly what you needed.

- <b>My issue is not included in the above and I have no idea what's going on</b>

First, remember that only the Simplified Chinese version of the game is officially supported. If you are using any other locale, there's no guarantee that all of the functions would work! If you really want to use it for your own locale, you can always submit a PR with the mirror assets in your own locale (such as the images and the advise answers).

If you have any other questions, feel free to go to the [discussion section](https://github.com/KIvoy/nikke-assistant/discussions "Nikke Assistant Discussion") and submit your topic with detailed description, screenshots, app_log and app_error files if raising a bug.


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
    - feel free to create the assets in your language to support the corresponding client.

## Releases
- you can download the latest release in the corresponding release tag

## Collaboration
- Highly Welcome! Any contribution is welcome including but exclusive to:
    - localizations (UI or game client language)
    - improvement of existing features
    - reasonable refactoring (god forbid!)
    - anything that'll make the experience better in general
