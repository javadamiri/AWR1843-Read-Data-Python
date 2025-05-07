import numpy as np
import serial
import time

class AWR1843Serial:
    def __init__(self, cli_port: str, cli_baudrate:int, data_port: str, data_baudrate:int):
        print(f"INFO: Initializing AWR1843Serial with CLI port: {cli_port}, CLI baudrate: {cli_baudrate}, "
              f"Data port: {data_port}, Data baudrate: {data_baudrate}")
        self._cli = serial.Serial(cli_port, cli_baudrate)
        self._data = serial.Serial(data_port, data_baudrate)
        self._byteBuffer = np.zeros(2**15,dtype = 'uint8')
        self._byteBufferLength = 0

    def sendConfigFile(self, configFileName):
        # Read the configuration file and send it to the board
        config = [line.rstrip('\r\n') for line in open(configFileName)]
        for i in config:
            self._cli.write((i+'\n').encode())
            print(i)
            time.sleep(0.01)

    def close(self):
        # Close the serial ports
        self._cli.write(('sensorStop\n').encode())
        self._cli.close()
        self._data.close()

    def readAndParseData(self):
        # Constants
        MMWDEMO_UART_MSG_DETECTED_POINTS = 1;
        
        maxBufferSize = 2**15;
        
        magicWord = [2, 1, 4, 3, 6, 5, 8, 7]
        
        # Initialize variables
        magicOK = 0 # Checks if magic number has been read
        dataOK = 0 # Checks if the data has been read correctly
        frameNumber = 0
        detObj = {}
        
        print(f'INFO: Reading {self._data.in_waiting} bytes from the serial port')
        readBuffer = self._data.read(self._data.in_waiting)
        byteVec = np.frombuffer(readBuffer, dtype = 'uint8')
        byteCount = len(byteVec)
        
        # Check that the buffer is not full, and then append the data to the buffer
        if (self._byteBufferLength + byteCount) < maxBufferSize:
            self._byteBuffer[self._byteBufferLength:self._byteBufferLength + byteCount] = byteVec[:byteCount]
            self._byteBufferLength = self._byteBufferLength + byteCount
        else:
            # for now just show a warning message
            print('WARNING: Buffer overflow, data not added to the buffer!')
            # # If the buffer is full, then remove the data that is not needed
            # self._byteBuffer[:maxBufferSize - byteCount] = self._byteBuffer[byteCount:maxBufferSize]
            # self._byteBuffer[maxBufferSize - byteCount:] = np.zeros(len(self._byteBuffer[maxBufferSize - byteCount:]),dtype = 'uint8')
            # self._byteBufferLength = maxBufferSize - byteCount

        # Check that the buffer has some data
        if self._byteBufferLength > 16:
            # Check for all possible locations of the magic word
            possibleLocs = np.where(self._byteBuffer == magicWord[0])[0]

            # Confirm that is the beginning of the magic word and store the index in startIdx
            startIdx = []
            for loc in possibleLocs:
                check = self._byteBuffer[loc:loc+8]
                if np.all(check == magicWord):
                    startIdx.append(loc)
                
            # Check that startIdx is not empty
            if startIdx:
                
                # Remove the data before the first start index
                if startIdx[0] > 0 and startIdx[0] < self._byteBufferLength:
                    self._byteBuffer[:self._byteBufferLength-startIdx[0]] = self._self._byteBuffer[startIdx[0]:self._byteBufferLength]
                    self._byteBuffer[self._byteBufferLength-startIdx[0]:] = np.zeros(len(self._byteBuffer[self._byteBufferLength-startIdx[0]:]),dtype = 'uint8')
                    self._byteBufferLength = self._byteBufferLength - startIdx[0]
                    
                # Check that there have no errors with the byte buffer length
                if self._byteBufferLength < 0:
                    self._byteBufferLength = 0
                    
                # word array to convert 4 bytes to a 32 bit number
                word = [1, 2**8, 2**16, 2**24]
                
                # Read the total packet length
                totalPacketLen = np.matmul(self._byteBuffer[12:12+4],word)
                
                # Check that all the packet has been read
                if (self._byteBufferLength >= totalPacketLen) and (self._byteBufferLength != 0):
                    magicOK = 1
        else:
            print('INFO: Not enough data in the buffer!')
        
        # If magicOK is equal to 1 then process the message
        if magicOK:
            # word array to convert 4 bytes to a 32 bit number
            word = [1, 2**8, 2**16, 2**24]
            
            # Initialize the pointer index
            idX = 0
            
            # Read the header
            magicNumber = self._byteBuffer[idX:idX+8]
            idX += 8
            version = format(np.matmul(self._byteBuffer[idX:idX+4],word),'x')
            idX += 4
            totalPacketLen = np.matmul(self._byteBuffer[idX:idX+4],word)
            idX += 4
            platform = format(np.matmul(self._byteBuffer[idX:idX+4],word),'x')
            idX += 4
            frameNumber = np.matmul(self._byteBuffer[idX:idX+4],word)
            idX += 4
            timeCpuCycles = np.matmul(self._byteBuffer[idX:idX+4],word)
            idX += 4
            numDetectedObj = np.matmul(self._byteBuffer[idX:idX+4],word)
            idX += 4
            numTLVs = np.matmul(self._byteBuffer[idX:idX+4],word)
            idX += 4
            subFrameNumber = np.matmul(self._byteBuffer[idX:idX+4],word)
            idX += 4

            # Read the TLV messages
            for tlvIdx in range(numTLVs):
                # word array to convert 4 bytes to a 32 bit number
                word = [1, 2**8, 2**16, 2**24]

                # Check the header of the TLV message
                tlv_type = np.matmul(self._byteBuffer[idX:idX+4],word)
                idX += 4
                tlv_length = np.matmul(self._byteBuffer[idX:idX+4],word)
                idX += 4

                # Read the data depending on the TLV message
                if tlv_type == MMWDEMO_UART_MSG_DETECTED_POINTS:
                    # Initialize the arrays
                    x = np.zeros(numDetectedObj,dtype=np.float32)
                    y = np.zeros(numDetectedObj,dtype=np.float32)
                    z = np.zeros(numDetectedObj,dtype=np.float32)
                    velocity = np.zeros(numDetectedObj,dtype=np.float32)
                    
                    for objectNum in range(numDetectedObj):
                        # Read the data for each object
                        x[objectNum] = self._byteBuffer[idX:idX + 4].view(dtype=np.float32)
                        idX += 4
                        y[objectNum] = self._byteBuffer[idX:idX + 4].view(dtype=np.float32)
                        idX += 4
                        z[objectNum] = self._byteBuffer[idX:idX + 4].view(dtype=np.float32)
                        idX += 4
                        velocity[objectNum] = self._byteBuffer[idX:idX + 4].view(dtype=np.float32)
                        idX += 4
                    
                    # Store the data in the detObj dictionary
                    detObj = {"numObj": numDetectedObj, "x": x, "y": y, "z": z, "velocity":velocity}
                    dataOK = 1

            # Remove already processed data
            if idX > 0 and self._byteBufferLength>idX:
                shiftSize = totalPacketLen
                
                    
                self._byteBuffer[:self._byteBufferLength - shiftSize] = self._byteBuffer[shiftSize:self._byteBufferLength]
                self._byteBuffer[self._byteBufferLength - shiftSize:] = np.zeros(len(self._byteBuffer[self._byteBufferLength - shiftSize:]),dtype = 'uint8')
                self._byteBufferLength = self._byteBufferLength - shiftSize
                
                # Check that there are no errors with the buffer length
                if self._byteBufferLength < 0:
                    self._byteBufferLength = 0
        else:
            print('INFO: Magic number not found!')

        return dataOK, frameNumber, detObj

