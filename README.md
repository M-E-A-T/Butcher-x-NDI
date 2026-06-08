# ***Butcher x NDI workflow setup guide***

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


3. To ensure each python library is installed and ready to use, install the following:
- pip install numpy
- pip install opencv-python
- pip install ndi-python

6. To ensure the receiving laptop is seeing all incoming NDI data streams, make sure these ports are open by running the following:
- sudo ufw allow 5353/udp
- sudo ufw allow 5960:5970/tcp
- sudo ufw allow 5960:5970/udp

8. Install avahi to amenable device discovery
- sudo apt update
- sudo apt install avahi-daemon avahi-utils libnss-mdns

10. CD to file location then run the following**
- Python3 -u NDI2.py
- Press escape to exit program
