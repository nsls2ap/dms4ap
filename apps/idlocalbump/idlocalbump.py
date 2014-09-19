__author__ = 'shengb'

import argparse
import code

import numpy as np

import cothread
import cothread.catools as ca

import aphla as ap

from _conf import PvMapping


class IdLocalBump():
    def __init__(self, pvmapping, machine="nsls2", submachine="SR"):
        """Application to create a local bump around an insertion device.
        This application is built on top of aphla, which has been developing at NSLS II project.
        """
        self.pvmapping = pvmapping
        self.selecteddevice = "NULL"
        self.source = 0.0
        self.plane = 0

        # # number of bpms on each side of selected device used for local bump
        # self.bpms4localbump = 4
        # # number of correctors on each side of selected device used for local bump
        # self.cors4localbump = 2

        # initialize hla library
        ap.machines.load(machine, submachine)

        # local bump settings: x shift, y shift, x angle, y angle
        self.bumpsettings = [0.0, 0.0, 0.0, 0.0]

        self.idlocalbumpthread = None

        self._getwfsize()

    def _getwfsize(self):
        self.bpmcounts = int(ca.caget(self.pvmapping.__bpmposition__+".NELM"))
        self.corscount = int(ca.caget(self.pvmapping.__correctorposition__+".NELM"))

    def deviceselectioncallback(self, value):
        """Set selected device name when it is changed."""
        self.selecteddevice = value

    def monitordeviceselection(self):
        """Start a process to monitor device selection."""
        return ca.camonitor(self.pvmapping.__deviceselected__, self.deviceselectioncallback)

    def sourcecallback(self, value):
        """Set source s position when it is changed."""
        self.source = value

    def monitorsource(self):
        """Start a process to monitor source s position."""
        return ca.camonitor(self.pvmapping.__deviceselected__, self.sourcecallback)

    def planecallback(self, value):
        """Set source plane when it is changed."""
        self.plane = value

    def monitorplane(self):
        """Start a process to monitor source plane."""
        return ca.camonitor(self.pvmapping.__plane__, self.planecallback)

    def bumpsettingscallback(self, value, index):
        """Update local bump settings: [x shift, y shift, x angle, y angle]"""
        self.bumpsettings[index] = value

    def monitorbumpsettings(self):
        """Monitor local bump settings"""
        return ca.camonitor([self.pvmapping.__xshift__, self.pvmapping.__yshift__,
                             self.pvmapping.__xangle__, self.pvmapping.__yangle__],
                            self.bumpsettingscallback)

    def _cleanlocalbump(self):
        """Clean local bump and set all values to zero."""
        try:
            print "clean up local bump"
            bpms = np.zeros(self.bpmcounts)
            cors = np.zeros(self.corscount)
            ca.caput([self.pvmapping.__bpmposition__, self.pvmapping.__bpmorbitx__, self.pvmapping.__bpmorbity__,
                      self.pvmapping.__correctorposition__,
                      self.pvmapping.__hcorrectorcurrent__, self.pvmapping.__hcorrectordiff__,
                      self.pvmapping.__vcorrectorcurrent__, self.pvmapping.__vcorrectordiff__],
                     [bpms, bpms, bpms, cors, cors, cors, cors, cors])

        except ca.ca_nothing:
            print "Cannot clean devices for local bump"

    def calccallback(self, value):
        """Computing a new local bump"""
        if value == 1:
            print "start local bump computing for %s" % self.selecteddevice
            if self.selecteddevice == "NULL":
                self._cleanlocalbump()
            else:
                try:
                    print self.bpmcounts/2
                    bpms = ap.getNeighbors(self.selecteddevice.lower(), "BPM", self.bpmcounts/2)
                    for i in range(len(bpms)):
                        if i != self.bpmcounts/2:
                            bpm = bpms[i]
                            print bpm.name, bpm.se, bpm.sb, bpm.x, bpm.y
                    cors = ap.getNeighbors(self.selecteddevice.lower(), "COR", self.corscount/2)
                    for i in range(len(cors)):
                        if i != self.corscount/2:
                            cor = cors[i]
                            print cor.name, cor.se, cor.sb, cor.get("x", handle="setpoint"), cor.get("y", handle="setpoint")
                except AttributeError:
                    try:
                        ca.caput(value.name, 0)
                    except ca.ca_nothing:
                        print "Cannot reset calc pvs after finished."
                    return

            try:
                ca.caput(value.name, 0)
            except ca.ca_nothing:
                print "Cannot reset calc pvs after finished."

    def monitorcalc(self):
        """Monitor the PVs of chromaticity varies."""
        return ca.camonitor(self.pvmapping.__calc__, self.calccallback)

    def applycallback(self, value):
        """"""
        if value == 1:
            print "To be implemented."

    def monitorapply(self):
        """Monitor the PVs of chromatocity varies."""
        return ca.camonitor(self.pvmapping.__apply__, self.applycallback)

    def startshell(self):
        """Give user an interactive interface to enable a proper stopping all cothread monitors later.
        """
        code.interact()

    def stopmonitor(self):
        """Stop all cothread monitors"""
        if self.idlocalbumpthread is not None:
            print "Abort cothread spawn sub-thread."
            self.idlocalbumpthread.Wait()
        cothread.Quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Specify machine and submachine to APHLA")
    parser.add_argument('machine', help='the name of primary machine')
    parser.add_argument('submachine', help='the name of sub machine')

    args = parser.parse_args()

    idlocalbump = IdLocalBump(PvMapping(), machine=args.machine, submachine=args.submachine)
    idlocalbump.monitordeviceselection()
    idlocalbump.monitorsource()
    idlocalbump.monitorplane()
    idlocalbump.monitorcalc()
    idlocalbump.monitorapply()

    idlocalbump.startshell()
    idlocalbump.stopmonitor()
