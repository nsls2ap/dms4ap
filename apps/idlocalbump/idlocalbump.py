__author__ = 'shengb'

import argparse
import code
import time
import numpy as np

import traceback

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
        self._updatelocalbump()

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
            print traceback.print_exc()
            print "Cannot clean devices for local bump"

    def _monitororbit(self, bpms):
        """"""
        orbx = [0.0] * (len(bpms) - 1)
        orby = [0.0] * (len(bpms) - 1)
        while self.continuelocalbumporbitthread:
            #@TODO: a bug to be fixed.
            # ValueError: setting an array element with a sequence.
            for i in range(len(bpms)):
                if i < self.bpmcounts / 2:
                    x = bpms[i].x
                    if isinstance(x, ca.ca_nothing):
                        orbx[i] = 0.0
                    else:
                        orbx[i] = x
                    y = bpms[i].y
                    if isinstance(y, ca.ca_nothing):
                        orby[i] = 0.0
                    else:
                        orby[i] = y
                elif i > self.bpmcounts / 2 + 1:
                    x = bpms[i].x
                    if isinstance(x, ca.ca_nothing):
                        orbx[i-1] = 0.0
                    else:
                        orbx[i-1] = x
                    y = bpms[i].y
                    if isinstance(y, ca.ca_nothing):
                        orby[i-1] = 0.0
                    else:
                        orby[i-1] = y

            try:
                ca.caput([self.pvmapping.__bpmorbitx__, self.pvmapping.__bpmorbity__],
                         [orbx, orby])
            except ca.ca_nothing:
                print orbx, orby
                print traceback.print_exc()
            cothread.Sleep(1.0)

    def _updatelocalbump(self):
        #print "start local bump computing for %s" % self.selecteddevice
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
                # try:
                #     ca.caput(value.name, 0)
                # except ca.ca_nothing:
                #     print "Cannot reset calc pvs after finished."
                return
            except TypeError:
                print "Get a type error in monitor device selection"

        # try:
        #     ca.caput(value.name, 0)
        # except ca.ca_nothing:
        #     print "Cannot reset verifying pvs after finished."

    # def monitorverify(self):
    #     """Monitor the PV to trig local bump computing."""
    #     return ca.camonitor(self.pvmapping.__calc__, self.verifycallback)

    def _aplocalbumpcreation(self, plane, ename, source, bumpsettings):
        """
        plane: 0: X plane, 1: Y plane;
        ename: selected insertion device element name;
        source: s position at source position
        bumpsettings: local bump settings: [x shift, y shift, x angle, y angle]

        return: delta correctors [H, V]
        """
        if plane == 0:
            delta = ap.setIdBump(ename, bumpsettings[0], bumpsettings[2], plane="x")
        elif plane == 1:
            delta = ap.setIdBump(ename, bumpsettings[1], bumpsettings[3], plane="y")

    def applycallback(self, value):
        """Apply computed results"""
        if value == 1:
            delta = self._aplocalbumpcreation(self.plane, self.selecteddevice.lower(), self.source, self.bumpsettings)
            try:
                if self.plane == 0:
                    # show settings for x plane
                    ca.caput(self.pvmapping.__hcorrectordiff__, delta, wait=True)
                elif self.plane == 1:
                    # show settings for y plane
                    ca.caput(self.pvmapping.__vcorrectordiff__, delta, wait=True)
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
        if self.idlocalbumpthread is not None and self.continuelocalbumporbitthread:
            print "Abort cothread spawn sub-thread."
            self.continuelocalbumporbitthread = False
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
    # idlocalbump.monitorverify()
    idlocalbump.monitorapply()

    idlocalbump.startshell()
    idlocalbump.stopmonitor()
