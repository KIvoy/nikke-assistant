#!/bin/bash
pyinstaller --noconfirm --onedir --windowed --icon "D:/Development/nikke-assistant/images/nikke_icon.ico" --uac-admin --add-data "C:/Program Files/Tesseract-OCR;Tesseract-OCR/" --add-data "D:/Development/nikke-assistant/admin.py;." --add-data "D:/Development/nikke-assistant/game_interaction_io.py;." --add-data "D:/Development/nikke-assistant/location_box.py;." --add-data "D:/Development/nikke-assistant/nikke_agent.py;." --add-data "D:/Development/nikke-assistant/nikke_interface.conf;." --add-data "D:/Development/nikke-assistant/images;images/" --add-data "D:/Development/nikke-assistant/agent;agent/" --paths "C:/Windows/System32/downlevel"  "D:/Development/nikke-assistant/nikke_interface.py"