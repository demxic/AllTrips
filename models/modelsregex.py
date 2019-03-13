"""This module contains all needed regular expressions need in the time_classes files"""
# *******************************************************************

import re
from typing import Pattern

duration_fmt: Pattern[str] = re.compile(r"""
    (?P<fill_align>.?[<>])?            #4 digits for FLIGHT number
    (?P<size>\d)?     #3 letter destination IATA airport code             v.gr MEX, SCL, JFK
    (?P<colon>:)?             #4 digit begin time                                 v.gr.   0300, 1825
    (?P<hide_if_zero>H)?               #4 digit end time
    """, re.VERBOSE)

