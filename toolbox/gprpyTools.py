import numpy as np
import numpy.matlib as matlib
import scipy.interpolate as interp
# For progress bar
import time
from tqdm import tqdm


def timeZeroAdjust(data):
        
    maxlen = data.shape[0]
    newdata = np.asmatrix(np.zeros(data.shape))
    
    # Go through all traces to find maximum spike
    maxind = np.zeros(data.shape[1], dtype=int)
    for tr in range(0,data.shape[1]):
        maxind[tr] = int(np.argmax(np.abs(data[:,tr])))

    # Find the mean spike point
    meanind = int(np.round(np.mean(maxind)))

    # Shift all traces. If max index is smaller than
    # mean index, then prepend zeros, otherwise append
    for tr in range(0,data.shape[1]):
        if meanind > maxind[tr]:
            differ = int(meanind - maxind[tr])
            newdata[:,tr] = np.vstack([np.zeros((differ,1)), data[0:(maxlen-differ),tr]])
        elif meanind < maxind[tr]:
            differ = maxind[tr] - meanind
            newdata[:,tr] = np.vstack([data[differ:maxlen,tr], np.zeros((differ,1))])
        else:
            newdata[:,tr] = data[:,tr]

    return newdata




def dewow(data,window):
    newdata = np.asmatrix(np.zeros(data.shape))
    
    # If the window is larger or equal to the number of samples,
    # then we can do a much faster dewow
    if (window >= data.shape[0]):
        for tr in tqdm(range(0,data.shape[1])):
            newdata[:,tr]=data[:,tr]-np.mean(data[:,tr])*np.ones((data.shape[0],1))
    else:
        # For each trace
        for tr in tqdm(range(0,data.shape[1])):
            trace = data[:,tr]
            averages = np.zeros(trace.shape)
            # Calculate and subtract running mean
            for i in range(0,data.shape[0]):
                winstart = int(i - np.floor(window/2.0))
                winend = int(i + np.floor(window/2.0))
                # If running mean window goes outside of range,
                # set range to "beginning until length"
                if winstart < 0:
                    winstart = 0
                    winend = window
                # Or to "end-length to end"
                if winend > len(trace):
                    winstart = len(trace) - window
                    winend = len(trace)     
                newdata[i,tr] = trace[i] - np.mean(trace[winstart:winend])
    print('done with dewow')
    return newdata


def remMeanTrace(data,ntraces):
    newdata = np.asmatrix(np.zeros(data.shape))
    tottraces = data.shape[1]

    # For each trace
    for tr in tqdm(range(0,data.shape[1])):
        winstart = int(tr - np.floor(ntraces/2.0))
        winend = int(tr + np.floor(ntraces/2.0))
        if (winstart < 0):
            winstart = 0
            winend = min(ntraces,tottraces)
        elif (winend > tottraces):
            winstart = max(tottraces - ntraces,0)
            winend = tottraces
           
        avgtr = np.zeros(data[:,tr].shape)
        for i in range(winstart,winend):
            avgtr = avgtr + data[:,i]
            
        avgtr = avgtr/float(winend-winstart)
            
        newdata[:,tr] = data[:,tr] - avgtr
            
    return newdata

def tpowGain(data,twtt,power):
    factor = np.reshape(twtt**(float(power)),(len(twtt),1))
    factmat = matlib.repmat(factor,1,data.shape[1])
    
    return np.multiply(data,factmat)


def agcGain(data,window):
    eps=1e-8
    newdata = np.asmatrix(np.zeros(data.shape))
    # For each trace
    for tr in tqdm(range(0,data.shape[1])):
        trace = data[:,tr]
        energy = np.zeros(trace.shape)
        for i in range(0,len(trace)):
            winstart = int(i - np.floor(window/2.0))
            winend = int(i + np.floor(window/2.0))
            # If running mean window goes outside of range,
            # set range to "beginning until length"
            if winstart < 0:
                winstart = 0
                winend = window
            # Or to "end-length to end"
            if winend > len(trace):
                winstart = len(trace) - window
                winend = len(trace)     
            energy[i] = np.max([np.linalg.norm(trace[winstart:winend]) ,eps])
        newdata[:,tr] = np.divide(data[:,tr],energy)
    return newdata


def prepTopo(topofile,position=None):
    # Read topofile, see if it is two columns or three columns.
    # Here I'm using numpy's loadtxt. There are more advanced readers around
    # but this one should do for this simple situation
    delimiter = ','
    topotable = np.loadtxt(topofile,delimiter=delimiter)
    topomat = np.asmatrix(topotable)
    # Depending if the table has two or three columns,
    # need to treat it differently
    if topomat.shape[1] is 3:
        # Turn the three-dimensional positions into along-profile
        # distances
        topoVal=topomat[:,2]
        npos = topomat.shape[0]
        steplen = np.sqrt(
            np.power( topomat[1:npos,0]-topomat[0:npos-1,0] ,2.0) + 
            np.power( topomat[1:npos,1]-topomat[0:npos-1,1] ,2.0)
        )
        alongdist = np.cumsum(steplen)
        topoPos = np.append(0,alongdist)
    elif topomat.shape[1] is 2:
        topoPos=topomat[:,0]
        topoVal=topomat[:,1]
        
    return topoPos, topoVal

def correctTopo(data, velocity, profilePos, topoPos, topoVal, timeStep):
    # The variable "topoPos" provides the along-profile coordinates
    # for which the topography is given. 
    # We allow several possibilities to provide topoPos:
    # If None is given, then we assume that they are regularly
    # spaced along the profile
    if topoPos is None:
        topoPos = np.linspace(np.min(profilePos),np.max(profilePos),
                              np.size(topoVal))
    # If it's an integer or a float, then it gives the evenly spaced
    # intervals
    elif type(topoPos) is int:
        topoPos = np.arange(np.min(profilePos),np.max(profilePos),
                            float(topoPos))
    elif type(topoPos) is float:
        topoPos = np.arange(np.min(profilePos),np.max(profilePos),
                            topoPos)
    # Or it could be a file giving the actual along-profile positions    
    elif type(topoPos) is str:
        delimiter = ','
        topopostable = np.loadtxt(topoPos,delimiter=delimiter)

    # Next we need to interpolate the topography
    elev = interp.pchip_interpolate(topoPos,topoVal,profilePos)

    elevdiff = elev-np.min(elev)
    # Turn each elevation point into a two way travel-time shift.
    # It's two-way travel time
    etime = 2*elevdiff/velocity

    # Calculate the time shift for each trace
    tshift = (np.round(etime/timeStep)).astype(int)

    print("Not yet finished. Continue as in GPR-O elevCorrect")

    return data

    
    

    
