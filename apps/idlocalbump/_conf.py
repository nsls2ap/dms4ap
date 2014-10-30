class PvMapping(object):
    def __init__(self):
        """Configuration for PVs used by creating a local bump nearby insertion device.
        """
        self.__deviceselected__ = "SR-DMS4AP{LOCALBUMP}DEV:Sel-SP"
        self.__source__ = "SR-DMS4AP{LOCALBUMP}S-SP"
        self.__plane__ = "SR-DMS4AP{LOCALBUMP}PLANE-SP"
        #self.__xshift__ = "SR-DMS4AP{LOCALBUMP}SHIFT:X-SP"
        #self.__yshift__ = "SR-DMS4AP{LOCALBUMP}SHIFT:Y-SP"
        #self.__xangle__ = "SR-DMS4AP{LOCALBUMP}ANGLE:X-SP"
        #self.__yangle__ = "SR-DMS4AP{LOCALBUMP}ANGLE:Y-SP"
        self.__shift__ = "SR-DMS4AP{LOCALBUMP}SHIFT-SP"
        self.__angle__ = "SR-DMS4AP{LOCALBUMP}ANGLE-SP"
        self.__anglerb__ = "SR-DMS4AP{LOCALBUMP}ANGLE-I"
        self.__positionrb__ = "SR-DMS4AP{LOCALBUMP}POS-I"

        self.__bpmposition__ = "SR-DMS4AP{LOCALBUMP:BPM}Pos-I"
        self.__bpmorbitx__ = "SR-DMS4AP{LOCALBUMP:BPM}ORB:X-I"
        self.__bpmorbity__ = "SR-DMS4AP{LOCALBUMP:BPM}ORB:Y-I"
        self.__bpmorbitx0__ = "SR-DMS4AP{LOCALBUMP:BPM}ORB:X0-I"
        self.__bpmorbity0__ = "SR-DMS4AP{LOCALBUMP:BPM}ORB:Y0-I"

        self.__correctorposition__ = "SR-DMS4AP{LOCALBUMP:COR}Pos-I"
        self.__hcorrectorcurrent__ = "SR-DMS4AP{LOCALBUMP:HCOR}PS-SP"
        self.__hcorrectordiff__ = "SR-DMS4AP{LOCALBUMP:HCOR}PS:Delta-SP"
        self.__vcorrectorcurrent__ = "SR-DMS4AP{LOCALBUMP:VCOR}PS-SP"
        self.__vcorrectordiff__ = "SR-DMS4AP{LOCALBUMP:VCOR}PS:Delta-SP"

        self.__undo__ = "SR-DMS4AP{LOCALBUMP}Enbl:Undo-Cmd"
        self.__apply__ = "SR-DMS4AP{LOCALBUMP}Enbl-Cmd"
        self.__status__ = "SR-DMS4AP{LOCALBUMP}TS-I"
        self.__idposinfo__ = "SR-DMS4AP{LOCALBUMP}S-I"
        self.__srcposition__ = "SR-DMS4AP{LOCALBUMP}SRC-SP"
