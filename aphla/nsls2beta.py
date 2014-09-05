
# Initialization

# import numpy as np
# import aphla as ap
# ap.machines.load("nsls2", "SR")

tw = ap.getTwiss('p*c*', ['s', 'betax', 'betay', 'etax', 'phix', 'phiy'])

# trig=0 is internal, trig=1 is external
names, x0, y0, Isum0, timestamp, offset = ap.nsls2.getSrBpmData(waveform="Tbt",trig=1, count=2000, output=False)

# adjust the offset, align to the original zero
nbpm, nturns = np.shape(Isum0)
nturns = nturns + np.max(offset)
x = np.zeros((nbpm, nturns), 'd')
y = np.zeros((nbpm, nturns), 'd')
Isum = np.zeros((nbpm, nturns), 'd')
# convert nm to mm
for i in range(nbpm):
    x[i,offset[i]:offset[i]+nturns] =  x0[i,:]*1e-6
    y[i,offset[i]:offset[i]+nturns] =  y0[i,:]*1e-6
    Isum[i,offset[i]:offset[i]+nturns] = Isum0[i,:]

btx = ap.calcBetaAu(x[:,3:1800], ref=tw[:,1])
bty = ap.calcBetaAu(y[:,3:1800], ref=tw[:,2])

