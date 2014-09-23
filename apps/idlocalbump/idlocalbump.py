__author__ = 'shengb'

import argparse
import code
import time
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

        self.localbumporbitthread = None
        # flag to stop local bump orbit monitor thread
        # False means thread is stopped already
        self.continuelocalbumporbitthread = False

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

    def _monitororbit(self, bpms):
        """"""
        while self.continuelocalbumporbitthread:
            orbx = []
            orby = []
            for i in range(len(bpms)):
                if i != self.bpmcounts / 2:
                    orbx.append(bpms[i].x)
                    orby.append(bpms[i].y)

            ca.caput([self.pvmapping.__bpmorbitx__, self.pvmapping.__bpmorbity__],
                     [orbx, orby])
            cothread.Sleep(1.0)
        else:
            print "Stop update local bump orbit."

    def verifycallback(self, value):
        """Computing a new local bump"""
        if value == 1:
            print "start local bump computing for %s" % self.selecteddevice
            if self.selecteddevice == "NULL":
                self._cleanlocalbump()
            else:
                try:
                    bpms = ap.getNeighbors(self.selecteddevice.lower(), "BPM", self.bpmcounts/2)
                    orbx = []
                    orby = []
                    bpm_s = []
                    for i in range(len(bpms)):
                        if i != self.bpmcounts / 2:
                            bpm_s.append(bpms[i].se)
                            orbx.append(bpms[i].x)
                            orby.append(bpms[i].y)
                            print bpms[i].pv(handle='readback')
                    cors = ap.getNeighbors(self.selecteddevice.lower(), "COR", self.corscount/2)
                    hcor = []
                    vcor = []
                    cor_s = []
                    for i in range(len(cors)):
                        if i != self.corscount/2:
                            hcor.append(cors[i].get("x", handle="setpoint"))
                            vcor.append(cors[i].get("y", handle="setpoint"))
                            cor_s.append(cors[i].se)
                    ca.caput([self.pvmapping.__bpmposition__,
                              self.pvmapping.__bpmorbitx__, self.pvmapping.__bpmorbity__,
                              self.pvmapping.__correctorposition__,
                              self.pvmapping.__hcorrectorcurrent__, self.pvmapping.__vcorrectorcurrent__],
                             [bpm_s, orbx, orby, cor_s, hcor, vcor])

                    # Stop previous existing thread.
                    if self.continuelocalbumporbitthread:
                        self.continuelocalbumporbitthread = False
                        if self.localbumporbitthread is not None:
                            self.localbumporbitthread.Wait()

                    self.continuelocalbumporbitthread = True
                    self.localbumporbitthread = cothread.Spawn(self._monitororbit, bpms)
                except AttributeError:
                    try:
                        ca.caput(value.name, 0)
                    except ca.ca_nothing:
                        print "Cannot reset calc pvs after finished."
                    return

            try:
                ca.caput(value.name, 0)
            except ca.ca_nothing:
                print "Cannot reset verifying pvs after finished."

    def monitorverify(self):
        """Monitor the PV to trig local bump computing."""
        return ca.camonitor(self.pvmapping.__calc__, self.verifycallback)

    def applycallback(self, value):
        """Apply computed results"""
        if value == 1:
            try:
                ca.caput(value.name, 0)
                ca.caput(self.pvmapping.__status__, time.strftime("%a, %d %b %Y, %H:%M:%S %Z"))
            except ca.ca_nothing:
                print "Cannot reset applying pvs after finished."
            # to stop local bump orbit thread monitor thread
            self.continuelocalbumporbitthread = False
            self.localbumporbitthread.Wait()

    def monitorapply(self):
        """Monitor the PV to trig setting data to IOC."""
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
    idlocalbump.monitorverify()
    idlocalbump.monitorapply()

    idlocalbump.startshell()
    idlocalbump.stopmonitor()
