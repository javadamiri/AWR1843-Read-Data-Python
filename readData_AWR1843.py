import time

from awr1843_serial import AWR1843Serial
import config_params as cfgs
from gui import GUI

# Function to parse the data inside the configuration file
def parseConfigFile(configFileName):
    configParameters = {} # Initialize an empty dictionary to store the configuration parameters
    
    # Read the configuration file and send it to the board
    config = [line.rstrip('\r\n') for line in open(configFileName)]
    for i in config:
        # Split the line
        splitWords = i.split(" ")

        # Hard code the number of antennas, change if other configuration is used
        numRxAnt = 4
        numTxAnt = 3
        
        # Get the information about the profile configuration
        if "profileCfg" in splitWords[0]:
            startFreq = int(float(splitWords[2]))
            idleTime = int(splitWords[3])
            rampEndTime = float(splitWords[5])
            freqSlopeConst = float(splitWords[8])
            numAdcSamples = int(splitWords[10])
            numAdcSamplesRoundTo2 = 1;
            
            while numAdcSamples > numAdcSamplesRoundTo2:
                numAdcSamplesRoundTo2 = numAdcSamplesRoundTo2 * 2;
                
            digOutSampleRate = int(splitWords[11]);
            
        # Get the information about the frame configuration    
        elif "frameCfg" in splitWords[0]:
            chirpStartIdx = int(splitWords[1]);
            chirpEndIdx = int(splitWords[2]);
            numLoops = int(splitWords[3]);
            numFrames = int(splitWords[4]);
            framePeriodicity = float(splitWords[5]);

    # Combine the read data to obtain the configuration parameters           
    numChirpsPerFrame = (chirpEndIdx - chirpStartIdx + 1) * numLoops
    configParameters["numDopplerBins"] = numChirpsPerFrame / numTxAnt
    configParameters["numRangeBins"] = numAdcSamplesRoundTo2
    configParameters["rangeResolutionMeters"] = (3e8 * digOutSampleRate * 1e3) / (2 * freqSlopeConst * 1e12 * numAdcSamples)
    configParameters["rangeIdxToMeters"] = (3e8 * digOutSampleRate * 1e3) / (2 * freqSlopeConst * 1e12 * configParameters["numRangeBins"])
    configParameters["dopplerResolutionMps"] = 3e8 / (2 * startFreq * 1e9 * (idleTime + rampEndTime) * 1e-6 * configParameters["numDopplerBins"] * numTxAnt)
    configParameters["maxRange"] = (300 * 0.9 * digOutSampleRate)/(2 * freqSlopeConst * 1e3)
    configParameters["maxVelocity"] = 3e8 / (4 * startFreq * 1e9 * (idleTime + rampEndTime) * 1e-6 * numTxAnt)
    
    return configParameters

# Function to update the data and display in the plot
def update(radar_serials: AWR1843Serial, vis_gui: GUI):
    dataOk = 0
    global detObj
    x = []
    y = []
      
    # Read and parse the received data
    dataOk, frameNumber, detObj = radar_serials.readAndParseData()
    
    if dataOk and len(detObj["x"])>0:
        #print(detObj)
        x = -detObj["x"]
        y = detObj["y"]
        
        vis_gui.setData(x, y)
    
    return dataOk


# -------------------------    MAIN   -----------------------------------------  
def main():
    # Configure the serial ports
    radar_serials = AWR1843Serial(cfgs.CLI_PORT, cfgs.CLI_BR, cfgs.DATA_PORT, cfgs.DATA_BR)
    radar_serials.sendConfigFile(cfgs.configFileName)

    # Get the configuration parameters from the configuration file
    configParameters = parseConfigFile(cfgs.configFileName)

    vis_gui = GUI()
    vis_gui.show()

    # Main loop
    detObj = {}
    frameData = {}
    currentIndex = 0
    while True:
        try:
            # Update the data and check if the data is okay
            dataOk = update(radar_serials, vis_gui)

            if dataOk:
                # Store the current frame into frameData
                frameData[currentIndex] = detObj
                currentIndex += 1

            time.sleep(0.05)  # Sampling frequency of 30 Hz

        # Stop the program and close everything if Ctrl + c is pressed
        except KeyboardInterrupt:
            radar_serials.close()
            vis_gui.close()
            print("Program stopped by user.")
            break

if __name__ == "__main__":
    main()





