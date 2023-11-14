# -*- coding: utf-8 -*-

from bisect import bisect_left

#https://stackoverflow.com/a/12141511

def take_closest(myList, myNumber, returnIndex=False):
    """
    Assumes myList is sorted. Returns closest value to myNumber.
    If two numbers are equally close, return the smallest number.
    Returns the first occurence of the closest number if there are multiple entries
    """
    
    #bisect_left might be called again later to make sure we have the first entry
    pos = bisect_left(myList, myNumber) 
    
    if pos == 0:
        if returnIndex is False:
            return myList[0]
        else:
            return 0
    
    if pos == len(myList):
        pos = bisect_left(myList, myList[pos-1])
        if pos == len(myList):
            if returnIndex is False:
                return myList[-1]
            else:
                return pos-1
        else:
            if returnIndex is False:
                return myList[pos]
            else:
                return pos

    if myList[pos] - myNumber < myNumber - myList[pos - 1]:
        pos = bisect_left(myList, myList[pos])
        if returnIndex is False:
            return myList[pos]
        else:
            return pos
    else:
        pos = bisect_left(myList, myList[pos-1])
        if returnIndex is False:
            return myList[pos]
        else:
            return pos