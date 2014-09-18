__author__ = 'shengb'

import code

import cothread
import cothread.catools as ca

import aphla as ap

from _conf import PvMapping


class IdLocalBump():
    def __init__(self, pvmapping):
        """Application to create a local bump around an insertion device.
        This application is built on top of aphla, which has been developing at NSLS II project.
        """
        self.pvmapping = pvmapping

    def applycallback(self):
        """"""

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
    idlocalbump = IdLocalBump(PvMapping())

    idlocalbump.startshell()
    idlocalbump.stopmonitor()
