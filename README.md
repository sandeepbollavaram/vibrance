# 🖼 Advanced Image Editor Pro

A desktop image editing application developed using Python, PyQt5 and OpenCV.

This document explains ALL steps required to install, run, build EXE, and create installer.

------------------------------------------------------------
📌 SYSTEM REQUIREMENTS
------------------------------------------------------------
- Windows 10 or above
- Python 3.10+
- Minimum 4GB RAM

------------------------------------------------------------
STEP 1: INSTALL PYTHON
------------------------------------------------------------

Download Python from:
https://www.python.org/downloads/

During installation:
✔ Select "Add Python to PATH"

Verify installation:

python --version

Explanation:
This command checks if Python is installed properly.

------------------------------------------------------------
STEP 2: OPEN PROJECT FOLDER
------------------------------------------------------------

Open terminal inside project folder:

cd ImageCompareSoftware

Explanation:
cd = change directory
Moves terminal into your project folder.

------------------------------------------------------------
STEP 3: CREATE VIRTUAL ENVIRONMENT (RECOMMENDED)
------------------------------------------------------------

Create virtual environment:

python -m venv venv

Explanation:
- -m venv creates isolated Python environment
- venv is the environment folder name

Activate virtual environment:

venv\Scripts\activate

If PowerShell blocks activation:

Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

Then activate again:

venv\Scripts\activate

After activation, you should see:

(venv)

This means virtual environment is active.

------------------------------------------------------------
STEP 4: INSTALL REQUIRED LIBRARIES
------------------------------------------------------------

Install dependencies:

pip install -r requirements.txt

Explanation:
pip installs packages listed inside requirements.txt

Packages installed:
- PyQt5 (GUI framework)
- opencv-python (Image processing)
- numpy (Numerical operations)
- pyinstaller (For building EXE)

------------------------------------------------------------
STEP 5: RUN THE APPLICATION
------------------------------------------------------------

Run the software:

python main.py

Explanation:
python runs interpreter
main.py is main application file

GUI window will open.

------------------------------------------------------------
HOW TO USE SOFTWARE
------------------------------------------------------------

1. Click Browse Folder
2. Select folder containing images
3. Enter extension (example: jpg or png)
4. Click Load Files
5. Select one or multiple images
6. Adjust sliders (Brightness, Contrast, Exposure, etc.)
7. Click APPLY EDITS
8. Use mouse wheel to Zoom
9. Click Compare Before / After
10. Use Crop tool if required

------------------------------------------------------------
LOGGING SYSTEM
------------------------------------------------------------

- All actions are saved in logs.txt
- Logs remain even after closing application
- Logs include date, time, and operation details

------------------------------------------------------------
BUILD PROFESSIONAL EXE FILE
------------------------------------------------------------

Activate virtual environment:

venv\Scripts\activate

Build executable:

python -m PyInstaller --noconsole --onefile --clean --name ImageEditorPro main.py

Explanation of flags:

--noconsole   → hides terminal window
--onefile     → creates single EXE
--clean       → removes temporary build files
--name        → sets output EXE name

After build, EXE will be located in:

dist\ImageEditorPro.exe

------------------------------------------------------------
CREATE INSTALLER (SETUP FILE)
------------------------------------------------------------

1. Install Inno Setup:
https://jrsoftware.org/isinfo.php

2. Create installer script (.iss file)

3. Compile installer script

After compilation, you will get:

ImageEditorPro_Setup.exe

This setup file will:
✔ Install program in Program Files
✔ Create Desktop shortcut
✔ Create Start Menu entry
✔ Provide Uninstaller
✔ Show Install → Finish wizard

------------------------------------------------------------
PROJECT STRUCTURE
------------------------------------------------------------

ImageCompareSoftware/
│
├── main.py
├── requirements.txt
├── README.md
├── logs.txt
├── dist/
└── venv/

------------------------------------------------------------
EDUCATIONAL OBJECTIVES
------------------------------------------------------------

This project demonstrates:

- GUI development using PyQt5
- Image processing using OpenCV
- Event-driven programming
- File handling & logging
- Multi-image editing
- Software packaging & deployment

------------------------------------------------------------
AUTHOR DETAILS
------------------------------------------------------------

Name: Sandeep Kumar Bollavaram
Course: B.Tech CSE
Year: 2nd Year

------------------------------------------------------------
END OF DOCUMENT
------------------------------------------------------------
