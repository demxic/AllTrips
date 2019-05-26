# *******************************************************************
# THIS REGEX ARE USED WHEN READING ROSTER FILES
#
# *******************************************************************
import re

roster_data_RE = re.compile(r'''
    (?P<month>\w{3,10})\s+         #Any month from enero to diciembre (or january to december) 
    (?P<year>\d{4})\s+             #4 digit year, v.gr. 2018 
    (?P<header>.+)
    DH:\s+                         #Header ends when DH:  v.gr 3:45 is found
    (?P<DH>\d{1,2}:\d{1,2}).+      
    DAY.+?DH\s+
    (?P<body>.*)                   #What comes next is the body
    ''', re.VERBOSE | re.DOTALL | re.IGNORECASE)

# RegEx que se debe utilizar cuando el rol no contiene Crew Type
crewstats_no_type = re.compile(r"""
    (?P<crew_member_id>\d{6})\s+    #6 digits at start followed by one or more spaces        v.gr. 102711
    (?P<name>(\w{1,12}|(\w{1,11}\s\w{1,11})))\s+           #One or twelve alphanumeric crew member line name        v.gr. XICOTENCATL
    (?P<pos>[A-Z]{3})\s+            #Three letter postion id                                 v.gr. SOB
    (?P<crew_group>\w{4})\s+             #Group for member                                        v.gr. S001
    (?P<base>[A-Z]{3})\s+           #Three letter code for homebase airport                  v.gr. MEX
    (?:\d)\s+                       #Line number, whatever that means                        v.gr. 0
    (?P<seniority>\d{1,4})\s+       #Crewmember's line number                                v.gr. 694
    (Time\sZone:)
    (?P<timeZone>\w).*              #TimeZone for all events                                v.gr. Time
    """, re.VERBOSE | re.IGNORECASE)

carryInRE = re.compile(r'''
    (?P<day>\d{2})                 #2 digits at start followed by a - or a whitespace
    (?:\s|-)
    (?P<endDay>\w{2})\s+           #The day when the sequence ends (if any)        v.gr. 07-08
    ''', re.VERBOSE)

non_trip_RE = re.compile(r'''
    (?P<day>\d{2})                 #2 digits at start followed by a - 
    -
    (?P<end_day>\d{2})\s+          #The day when the sequence ends (if any)        v.gr. 07-08
    (?P<name>[A-Z]{1,2}|[A-Z]\d)\s+#One or two letters or a letter and a digit
    ''', re.VERBOSE | re.DOTALL)

roster_trip_RE = re.compile(r'''
    (?P<day>\d{2})\s+
    (?P<end_day>[A-Z]{2})\s+
    (?P<name>\d{4})\s+
    (?P<flights>(\w{4,6}\s+\w{3}\s+\d{4}\s+\w{3}\s+\d{4}\s+)+)
    ''', re.VERBOSE | re.DOTALL | re.IGNORECASE)

airItineraryRE = re.compile(r"""
    (?P<name>\w{4,6})\s          #An opt 2char airlinecode + 4 digit number + " "    v.gr   AM0001, DH0403, 0170
    (?P<origin>[A-Z]{3})\s         #3 letter origin IATA airport code                  v.gr MEX, SCL, JFK
    (?P<begin>\d{4})\s             #4 digit begin time                                 v.gr.   0300, 1825
    (?P<destination>[A-Z]{3})\s    #3 letter destination IATA airport code             v.gr MEX, SCL, JFK
    (?P<end>\d{4})                 #4 digit end time
    """, re.VERBOSE)
