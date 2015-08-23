"""
Take streaming data with this file
"""

import u6 # The driver library for the LabJack
import time # allows naming of files with the date and time
from datetime import datetime # another time library. (convert to time library eventually)
import Queue
import threading
import sys
import copy

# Streaming pre-sets.
stream_time1 = int(raw_input('seconds to stream? '))
print "streaming for %s seconds." % stream_time1
MAX_REQUESTS = stream_time1 # * 25

# open the LabJack (U6) 
#d = None
d = u6.U6()

#set up the LabJack
d.getCalibrationData()

d.streamConfig(NumChannels = 2, 
               ResolutionIndex = 1, 
               SettlingFactor = 1, 
               ChannelNumbers = [ 0, 1 ], 
               ChannelOptions = [ 0, 0 ], 
               #SampleFrequency = 25000 
               SamplesPerPacket = 10,
               InternalStreamClockFrequency = 0, 
               DivideClockBy256 = False, 
               ScanInterval = 4000) 
               
# Make a new data file.
f = open( time.strftime("%Y%m%d-%H%M%S") + '.txt', 'w')

class StreamDataReader(object):
    def __init__(self, device):
        self.device = device
        self.data = Queue.Queue()
        self.dataCount = 0
        self.missed = 0
        self.running = False
        
    def readStreamData(self):
        self.running = True
        
        start = datetime.now()
        self.device.streamStart()
        while self.running:
            # Calling with convert = False, because we are going to convert in
            # the main thread.
            returnDict = self.device.streamData(convert = False).next()
            
            self.data.put_nowait(copy.deepcopy(returnDict))
            
            self.dataCount += 1
            if self.dataCount > MAX_REQUESTS:
                self.running = False
                
        print "Stream stopped."
        self.device.streamStop()
        stop = datetime.now()
        
        total = self.dataCount * self.device.packetsPerRequest * self.device.streamSamplesPerPacket
        print "%s requests with %s packets per request with %s samples per packet = %s samples total." % ( self.dataCount, d.packetsPerRequest, d.streamSamplesPerPacket, total )
        
        print "%s samples were lost due to errors." % self.missed
        total -= self.missed
        print "Adjusted number of samples = %s" % total
        
        runTime = (stop-start).seconds + float((stop-start).microseconds)/1000000
        print "The experiment took %s seconds." % runTime
        print "%s samples / %s seconds = %s Hz" % ( total, runTime, float(total)/runTime )
        d.close()

sdr = StreamDataReader(d)

sdrThread = threading.Thread(target = sdr.readStreamData)

# Start the stream and begin loading the result into a Queue
# this is the function to call when we get a request to stream.
sdrThread.start()

errors = 0
missed = 0

while True:
    try:
        # Check if the thread is still running
        if not sdr.running:
            break
        
        # Pull results out of the Queue in a blocking manner
        result = sdr.data.get(True, 1)
        
        # If there were errors, print them
        if result['errors'] != 0:
            errors += result['errors']
            missed += result['missed']
            print "+++++ Total Errors: %s, Total Missed: %s" % (errors, missed)
        
        # Convert the raw bytes (result['result']), to voltage data.
        r = d.processStreamData(result['result'])
        
        ch0 = r['AIN0']
        ch1 = r['AIN1']
        #ch2 = r['AIN2']
        for i in range(0, len(ch0)):
            f.write( '{0:.6f}\t'.format(ch0[i]) )
            f.write( '{0:.6f}\t'.format(ch1[i]) )
         #   f.write( '{0:.6f}\n'.format(ch2[i]) )

    except Queue.Empty:
        print "Queue is empty. Stopping..."
        sdr.running = False
        break
    except KeyboardInterrupt:
        sdr.running = False
    except Exception:
        e = sys.exc_info()[1]
        print type(e), e
        sdr.running = False
        break

f.close()


