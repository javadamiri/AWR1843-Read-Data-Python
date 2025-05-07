import os

CLI_PORT = 'COM4' if os.name == 'nt' else '/dev/ttyACM1'
CLI_BR = 115200
DATA_PORT = 'COM3' if os.name == 'nt' else '/dev/ttyACM0'
DATA_BR = 921600
configFileName = 'AWR1843config.cfg'