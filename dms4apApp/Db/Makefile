TOP=../..
include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE

#----------------------------------------------------
#  Optimization of db files using dbst (DEFAULT: NO)
#DB_OPT = YES

#----------------------------------------------------
# Create and install (or just install)
# databases, templates, substitutions like this

# DB for beta function measurement
DB += betafunc.db
DB += idlocalbump.db

ifneq ($(DEVIOCSTATS),)
DB_INSTALLS += $(DEVIOCSTATS)/db/iocAdminSoft.db
endif

ifneq ($(AUTOSAVE),)
DB_INSTALLS += $(firstword $(wildcard $(AUTOSAVE)/asApp/Db/save_restoreStatus.db $(AUTOSAVE)/db/save_restoreStatus.db))
endif

#----------------------------------------------------
# If <anyname>.db template is not named <anyname>*.template add
# <anyname>_TEMPLATE = <templatename>

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE

