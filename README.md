# ***Butcher x NDI workflow setup guide***

___compatibility & GUI update___
	- added __requirements.txt__
	- added __NDlib.py__ ctype wrapper that refrences ND SDK
	- added __install_and_check.sh__ shell script to verify SDK and dependencies are downloaded and accessible
	- updated readme.md

## **NDi Transmitter setup:**
1. Open a touch designer project and press tab to add a MovieFileInTOP and an NDIoutTop

2. Connect the Movie FileInTOP output to the NDIoutTOP input

3. Open the NDIoutTOP parameters and type in a source name.

5. Ensure that the TOP is set to active


## **NDI Receiver Setup (Meatop):**
1. On Meat top, install and extract the NDI SDK, execute teh script, then relocate SDk to library by running the following:

- wget https://downloads.ndi.tv/SDK/NDI_SDK_Linux/Install_NDI_SDK_v6_Linux.tar.gz
- tar xf Install_NDI_SDK_v6_Linux.tar.gz
- cd "NDI SDK for Linux"
- chmod +x Install_NDI_SDK_v6_Linux.sh
- ./Install_NDI_SDK_v6_Linux.sh

[**note:** when executing the script you will be met with a user license agreement. press Y then Enter to continue the installation.]
- sudo cp -P lib/x86_64-linux-gnu/* /usr/local/lib/
- sudo ldconfig


2. To ensure each python library is installed and ready to use, install the following:
- pip install numpy
- pip install opencv-python
- pip install ndi-python

3. To ensure the receiving laptop is seeing all incoming NDI data streams, make sure these ports are open by running the following:
- sudo ufw allow 5353/udp
- sudo ufw allow 5960:5970/tcp
- sudo ufw allow 5960:5970/udp

4. Install avahi to amenable device discovery
- sudo apt update
- sudo apt install avahi-daemon avahi-utils libnss-mdns

5. CD to file location then run the following**
- ./install_and_check.sh to ensure everythign is downloaded and accessible
- Python3 -u NDI2.py to run
- Press escape to exit program

## Tkinter (GUI) notes

The source selector UI uses `tkinter`. This is provided by the system Python build (not installable via pip).
If you plan to use the GUI on Linux, install the system package for `tkinter`:

- Debian / Ubuntu:
	```bash
	sudo apt-get install python3-tk
	```
- Fedora:
	```bash
	sudo dnf install python3-tkinter
	```
- Arch Linux:
	```bash
	sudo pacman -S tk
	```
- macOS (Homebrew):
	```bash
	brew install tcl-tk
	# ensure your Python is built/linked with that Tk or use the python.org installer
	```
- Windows: `tkinter` is included with the standard CPython installer.

The project will still run without `tkinter` (it falls back to auto-detecting the first NDI source), but the GUI source selector requires it.
