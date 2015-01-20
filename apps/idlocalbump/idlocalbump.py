__author__ = 'shengb'

import argparse
import code
import time
import numpy as np

import traceback

import cothread
from cothread.dbr import DBR_CHAR_STR
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

        # local bump settings: shift, angle
        self.bumpsettings = [0.0, 0.0]

        self.idlocalbumpthread = None

        self.localbumporbitthread = None
        # flag to stop local bump orbit monitor thread
        # False means thread is stopped already
        self.continuelocalbumporbitthread = False

        self.cors = None
        self.bpms = None
        self.idobj = None

        self.previoush = None
        self.previousv = None

        self.sourceposition = 0.0

        self._getwfsize()

    def _getwfsize(self):
        self.bpmcounts = int(ca.caget(self.pvmapping.__bpmposition__+".NELM"))
        self.corscount = int(ca.caget(self.pvmapping.__correctorposition__+".NELM"))

    def _updatelocalbump(self):
        # print "start local bump computing for %s" % self.selecteddevice
        if self.selecteddevice == "NULL":
            self._cleanlocalbump()
            self.bpms = None
            self.cors = None
            self.idobj = None
            try:
                ca.caput([self.pvmapping.__srcposition__, self.pvmapping.__srcposition__ + ".DRVH"],
                         [0.0, 0.0])
            except ca.ca_nothing:
                print traceback.print_exc()
            try:
                ca.caput(self.pvmapping.__status__, "No device selected",
                         datatype=DBR_CHAR_STR)
            except ca.ca_nothing:
                print "Could not set status pv."
                return
        else:
            try:
                self.idobj = ap.getElements(self.selecteddevice.lower())[0]
                allbpms = ap.getGroupMembers(["BPM", "UBPM"], op="union")
                leftbpms = [b for b in allbpms if b.se < self.idobj.sb]
                rightbpms = [b for b in allbpms if b.sb > self.idobj.se]
                bpms = leftbpms[-self.bpmcounts / 2:] + rightbpms[:self.bpmcounts / 2]
                #bpms = ap.getNeighbors(self.selecteddevice.lower(), "BPM", self.bpmcounts / 2)
                cors = ap.getNeighbors(self.selecteddevice.lower(), "COR", self.corscount / 2)

                try:
                    #assert len(bpms) == self.bpmcounts + 1
                    assert len(bpms) == self.bpmcounts
                    assert len(cors) == self.corscount + 1
                except AssertionError:
                    print "wrong devices"
                    return

                orbx = []
                orby = []
                bpm_s = []
                # delete the element in the middle, which is the insertion device itself
                #bpms.pop(self.bpmcounts / 2)
                self.bpms = bpms[:]

                for bpm in self.bpms:
                    bpm_s.append(bpm.se)
                    orbx.append(bpm.x)
                    orby.append(bpm.y)

                hcor = []
                vcor = []
                cor_s = []
                # delete the element in the middle, which is the insertion device itself
                cors.pop(self.corscount / 2)
                self.cors = cors[:]
                for cor in self.cors:
                    hcor.append(cor.get("x", unitsys=None, handle="setpoint"))
                    vcor.append(cor.get("y", unitsys=None, handle="setpoint"))
                    cor_s.append(cor.se)

                ca.caput([self.pvmapping.__srcposition__, self.pvmapping.__srcposition__+".DRVH",
                          self.pvmapping.__idposinfo__, self.pvmapping.__bpmposition__,
                          self.pvmapping.__bpmorbitx__, self.pvmapping.__bpmorbity__,
                          self.pvmapping.__correctorposition__,
                          self.pvmapping.__hcorrectorcurrent__, self.pvmapping.__vcorrectorcurrent__],
                         [(self.idobj.se - self.idobj.sb)/2.0, (self.idobj.se - self.idobj.sb),
                          [self.idobj.sb, (self.idobj.sb+self.idobj.se)/2.0, self.idobj.se],
                          bpm_s, orbx, orby, cor_s, hcor, vcor])

                # Stop previous existing thread.
                if self.continuelocalbumporbitthread:
                    self.continuelocalbumporbitthread = False
                    if self.localbumporbitthread is not None:
                        self.localbumporbitthread.Wait()

                self.continuelocalbumporbitthread = True
                self.localbumporbitthread = cothread.Spawn(self._monitororbit)
            except AttributeError:
                print traceback.format_exc()
                print "AttributeError"
                return
            except TypeError:
                print traceback.format_exc()
                print "Get a type error in monitor device selection"

    def deviceselectioncallback(self, value, index):
        """Set selected device name when it is changed."""
        if index == 0:
            self.selecteddevice = value
            self._updatelocalbump()
        else:
            self.sourceposition = value

    def monitordeviceselection(self):
        """Start a process to monitor device selection."""
        return ca.camonitor([self.pvmapping.__deviceselected__,
                             self.pvmapping.__srcposition__],
                            self.deviceselectioncallback)

    def sourcecallback(self, value):
        """Set source s position when it is changed."""
        self.source = value

    def monitorsource(self):
        """Start a process to monitor source s position."""
        return ca.camonitor(self.pvmapping.__deviceselected__, self.sourcecallback)

    def planecallback(self, value):
        """Set source plane when it is changed."""
        self.plane = value
        cothread.Sleep(2.0)
        if self.selecteddevice != "NULL":
            try:
                ca.caput(self.pvmapping.__shift__, ca.caget(self.pvmapping.__positionrb__))
                ca.caput(self.pvmapping.__angle__, ca.caget(self.pvmapping.__anglerb__))
            except ca.ca_nothing:
                # do not do anything for this exception.
                pass
        else:
            try:
                ca.caput(self.pvmapping.__shift__, 0.0)
                ca.caput(self.pvmapping.__angle__, 0.0)
            except ca.ca_nothing:
                # do not do anything for this exception.
                pass

    def monitorplane(self):
        """Start a process to monitor source plane."""
        return ca.camonitor(self.pvmapping.__plane__, self.planecallback)

    def bumpsettingscallback(self, value, index):
        """Update local bump settings: [shift, angle]"""
        self.bumpsettings[index] = value

    def monitorbumpsettings(self):
        """Monitor local bump settings"""
        return ca.camonitor([self.pvmapping.__shift__,
                             self.pvmapping.__angle__],
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

    def _getliveangleandpos(self, bpm0, bpm1):
        """
        """
        if self.plane == 0:
            p0 = bpm0.x
            p1 = bpm1.x
            p0bba = bpm0.x0
            p1bba = bpm1.x0
        elif self.plane == 1:
            p0 = bpm0.y
            p1 = bpm1.y
            p0bba = bpm0.y0
            p1bba = bpm1.y0
        angle = (p1 - p0)/(bpm1.se - bpm0.se)
        position = angle * (self.idobj.sb+self.sourceposition-bpm0.se) + p0
        angle_bba = (p1bba - p0bba)/(bpm1.se - bpm0.se)
        position_bba = angle_bba * (self.idobj.sb+self.sourceposition-bpm0.se) + p0bba
        return angle, position, angle_bba, position_bba

    def _monitororbit(self):
        """
        """
        orbx0 = [0.0] * self.bpmcounts
        orby0 = [0.0] * self.bpmcounts
        orbx = [0.0] * self.bpmcounts
        orby = [0.0] * self.bpmcounts
        hcor = [0.0] * self.corscount
        vcor = [0.0] * self.corscount

        msg = "Local bump for %s"%self.selecteddevice
        if self.bpms is None or self.cors is None or self.idobj is None:
            msg = "No Device selected."
        try:
            ca.caput(self.pvmapping.__status__, msg,
                     datatype=DBR_CHAR_STR)
        except ca.ca_nothing:
            print "Cound not set status pv."
            return
        while self.continuelocalbumporbitthread:
            # ValueError: setting an array element with a sequence.
            if self.bpms is None or self.cors is None or self.idobj is None:
                return
                
            for i, bpm in enumerate(self.bpms):
                x = bpm.x
                x0 = bpm.x0
                if isinstance(x, ca.ca_nothing):
                    orbx[i] = 0.0
                else:
                    orbx[i] = x
                if isinstance(x0, ca.ca_nothing):
                    orbx0[i] = 0.0
                else:
                    orbx0[i] = x0
                y = bpm.y
                y0 = bpm.y0
                if isinstance(y, ca.ca_nothing):
                    orby[i] = 0.0
                else:
                    orby[i] = y
                if isinstance(y0, ca.ca_nothing):
                    orby0[i] = 0.0
                else:
                    orby0[i] = y0
            for i, cor in enumerate(self.cors):
                h = cor.get("x", unitsys=None, handle="setpoint")
                if isinstance(h, ca.ca_nothing):
                    hcor[i] = 0.0
                else:
                    hcor[i] = h
                v = cor.get("y", unitsys=None, handle="setpoint")
                if isinstance(v, ca.ca_nothing):
                    vcor[i] = 0.0
                else:
                    vcor[i] = v
            angle, position, angle_bba, position_bba = self._getliveangleandpos(self.bpms[self.bpmcounts/2-1], self.bpms[self.bpmcounts/2])
            try:
                ca.caput([self.pvmapping.__anglerb__, self.pvmapping.__positionrb__,
                          self.pvmapping.__anglerb0__, self.pvmapping.__positionrb0__,
                          self.pvmapping.__bpmorbitx__, self.pvmapping.__bpmorbity__,
                          self.pvmapping.__bpmorbitx0__, self.pvmapping.__bpmorbity0__,
                          self.pvmapping.__hcorrectorcurrent__, self.pvmapping.__vcorrectorcurrent__],
                         [angle, position, angle_bba, position_bba,
                          orbx, orby, orbx0, orby0, hcor, vcor])
            except ca.ca_nothing:
                print traceback.print_exc()
            cothread.Sleep(1.0)

    def undocallback(self, value):
        """
        """
        if value == 1:
            try:
                if self.plane == 0:
                    if self.previoush is None:
                        ca.caput(self.pvmapping.__status__, "There is nothing to undo for horizontal plane",
                                 datatype=DBR_CHAR_STR)
                    else:
                        for i, cor in enumerate(self.cors):
                             cor.set("x", self.previoush[i], unitsys=None)
                        self.previoush = None
                elif self.plane == 1:
                    if self.previousv is None:
                        ca.caput(self.pvmapping.__status__, "There is nothing to undo for vertical plane",
                                 datatype=DBR_CHAR_STR)
                    else:
                        for i, cor in enumerate(self.cors):
                            cor.set("y", self.previousv[i], unitsys=None)
                        self.previousv = None
                ca.caput(value.name, 0)
            except ca.ca_nothing:
                try:
                    ca.caput(self.pvmapping.__status__, "Failed to undo action.", datatype=DBR_CHAR_STR)
                except ca.ca_nothing:
                    print "Cannot set status pv"

    def monitorundo(self):
        """Monitor the PV to trig local bump computing."""
        return ca.camonitor(self.pvmapping.__undo__, self.undocallback)

    def _aplocalbumpcreation(self, plane, ename, source, bumpsettings):
        """
        plane: 0: X plane, 1: Y plane;
        ename: selected insertion device element name;
        source: s position at source position
        bumpsettings: local bump settings: [shift, angle]

        return: delta correctors [H, V]
        """

        if plane == 0:
            fld = 'x'
            #xc = ((self.idobj.se - self.idobj.sb) / 2.0 - self.sourceposition) * \
            #    bumpsettings[1] + bumpsettings[0]
            #thetac = bumpsettings[1]
        elif plane == 1:
            fld = 'y'
        xc = ((self.idobj.se - self.idobj.sb) / 2.0 - self.sourceposition) * \
            bumpsettings[1] + bumpsettings[0]
        thetac = bumpsettings[1]

        if self.previoush is None:
            self.previoush = [0.0] * self.corscount
        for i, cor in enumerate(self.cors):
            self.previoush[i] = cor.get(fld, unitsys=None, handle="setpoint")

        niter = 10
        for i in range(niter):
            cothread.Yield(0.10)
            norm0, norm1, norm2, corvals = \
                ap.setIdBump(ename, xc, thetac, plane=fld)
            angle, position, _, _ = self._getliveangleandpos(self.bpms[self.bpmcounts/2-1], self.bpms[self.bpmcounts/2])
            # if the achieved angle and offset are very close to desired values, break
            # can not distinguish 10urad and 5um.
            if np.abs(angle - thetac) < 1e-2 and np.abs(xc - position) < 5e-3:
                break
            if corvals is None:
                msg = "{0}/{1} Minimum chi^2 achieved: {2} (predicted: {3})".format(i,niter,norm0, norm1)
            else:
                msg = "{0}/{1} chi^2 decreased {2} from {3} (predicted: {4})".format(
                    i, niter, norm2-norm0, norm0, norm1)
            ca.caput(self.pvmapping.__status__, msg[:255], datatype=DBR_CHAR_STR)

        delta = ap.fget(self.cors, fld, unitsys=None, handle="setpoint") - np.array(self.previoush, 'd')
        return delta

    def applycallback(self, value):
        """Apply computed results"""
        if value == 1:
            try:
                delta = self._aplocalbumpcreation(self.plane, self.selecteddevice.lower(),
                                                  self.source, self.bumpsettings)
            except Exception as e:
                try:
                    ca.caput(value.name, 0)
                    ca.caput(self.pvmapping.__status__, e.message[:255], datatype=DBR_CHAR_STR)
                except ca.ca_nothing:
                    print "Cannot access status pv."
                return

            try:
                if self.plane == 0:
                    # show settings for x plane
                    ca.caput(self.pvmapping.__hcorrectordiff__, delta, wait=True)
                elif self.plane == 1:
                    # show settings for y plane
                    ca.caput(self.pvmapping.__vcorrectordiff__, delta, wait=True)
                ca.caput(value.name, 0)
                ca.caput(self.pvmapping.__status__, time.strftime("%a, %d %b %Y, %H:%M:%S %Z"), datatype=DBR_CHAR_STR)
            except ca.ca_nothing:
                print "Cannot reset applying pvs after finished."
            # to stop local bump orbit thread monitor thread
            #self.continuelocalbumporbitthread = False
            #self.localbumporbitthread.Wait()

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
    idlocalbump.monitorundo()
    idlocalbump.monitorapply()
    idlocalbump.monitorbumpsettings()

    idlocalbump.startshell()
    idlocalbump.stopmonitor()
