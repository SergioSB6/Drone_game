# DronQuest PX
DroneQuest PX is a multiplayer videogame developed to interact and pilot drones, offering an educational and engaging experience for users. The platform supports both simulation mode (using SITL and Mission Planner) and production mode (real drones), with control via joystick or RC transmitter.

## Features

-Real-time telemetry visualization

-Joystick and RC transmitter control

-Customizable maps (map editor)

-Fixed security fences at maps (geofence)

-Obstacle avoidance

-Collect checkpoints

-Different difficulty levels (easy, medium, hard)

-Emergency landing safety controls

DroneQuest PX is designed to facilitate active learning, spark technological curiosity, and promote drone safety and operation skills.

## Installation Guide
### Requirements
Windows 10 or newer (not compatible with Windows 7 or older)

Python 3.11.5 [Download Python](https://www.python.org/downloads/windows/)

PyCharm IDE [Download PyCharm](https://www.jetbrains.com/pycharm/download/?section=windows)

Mission Planner (stable) [Download Mission Planner](https://firmware.ardupilot.org/Tools/MissionPlanner/)

### Step-by-step Installation
1. Clone the repository in your computer or download in .zip.
2. Unzip Mission Planner into the project folder and rename it to Mission Planner2.
3. Run MissionPlanner.exe — this will open the main screen of Mission Planner.
4. Go to: Simulation → Multirotor → stable. This will install the SITL software in the following directory: C:\Users\your_username\Documents\Mission Planner\sitl
5. Close Mission Planner and go to: C:\Users\your_username\Documents
6. Rename the folder Mission Planner to Mission Planner1. Then, copy that folder and paste it into the project directory.
7. Move the previously unzipped folder (Mission Planner2) inside the newly pasted one.
8. open the project in PyCharm, and select the version of Python we installed earlier as the interpreter.
A prompt will appear to install the required libraries — click Install (this may take a few minutes).

##Demos
-Simulation mode demo: https://youtu.be/7ZYXPeF8E4g
-Production mode (real drones) demo: https://youtu.be/PpO4J4XdDqk
