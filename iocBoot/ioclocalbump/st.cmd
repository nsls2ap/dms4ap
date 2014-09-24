#!../../bin/darwin-x86/dms4ap

## You may have to change betafunc to something else
## everywhere it appears in this file

< envPaths

cd ${TOP}

## Register all support components
dbLoadDatabase "dbd/dms4ap.dbd"
dms4ap_registerRecordDeviceDriver pdbbase

## Load record instances
dbLoadRecords "db/idlocalbump.db"
dbLoadRecords "iocsim/bpm_cor.db"

cd ${TOP}/iocBoot/${IOC}
iocInit

cd "../../iocsim/"
system("python initpvs.py")
cd ${TOP}/iocBoot/${IOC}
