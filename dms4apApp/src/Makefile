TOP=../..

include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE

#=============================
# Build the IOC support library

#=============================
# Build the IOC application

PROD_IOC = dms4ap
# dms4ap.dbd will be created and installed
DBD += dms4ap.dbd

# dms4ap.dbd will be made up from these files:
dms4ap_DBD += base.dbd
dms4ap_DBD += system.dbd

# dms4ap_registerRecordDeviceDriver.cpp derives from dms4ap.dbd
dms4ap_SRCS += dms4ap_registerRecordDeviceDriver.cpp

# Build the main IOC entry point on workstation OSs.
dms4ap_SRCS_DEFAULT += dms4apMain.cpp

ifneq ($(DEVIOCSTATS),)
dms4ap_DBD += devIocStats.dbd
dms4ap_LIBS += devIocStats
endif

ifneq ($(AUTOSAVE),)
dms4ap_DBD += asSupport.dbd
dms4ap_LIBS += autosave
endif

ifneq ($(CAPUTLOG),)
dms4ap_DBD += caPutLog.dbd
dms4ap_LIBS += caPutLog
endif

# Finally link to the EPICS Base libraries
dms4ap_LIBS += $(EPICS_BASE_IOC_LIBS)

#=============================

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE

