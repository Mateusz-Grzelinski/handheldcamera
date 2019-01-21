**Development has been stopped. In the end, project failed to capture position, rotation worked quite well**

Tested against Blender 2.79. No plans for porting

## Handheld camera Blender addon (client)
This addon allows you to capture yours accelerometer and gyroscope movement data and use it to animate object in your scene  in semi real time.

## Gyroscope and accelometer data (server)

EW tried to use Arduino + MPU 6050+ ESP8266 
https://github.com/mblasiak/GyroController

Maybe it is possible to get data from your phone.

## Installation
Download as zip, install as any other addon from user settings.

## Usage:
This blender addon is a client, that connects to a server and gets movement data. You need to fill in hostname/ip address and port number. 
Shortcut:
  - `ECS` to abort
  - `y` to start setting keyframes

## Development

Run fake server to provide random data for addon (localhost, port 5000)
```bash
python handheld_server.py
```

Start Blender and connect to pycharm debugger automatically:
```bash
./run_blender.sh
```

# Warning:

- calculating accelormeter data to position didn't work in the end, see conclusion in https://github.com/mblasiak/GyroController
- animation will override existing keyframes
- only one object is supported (I do not plan any mocap setup)
