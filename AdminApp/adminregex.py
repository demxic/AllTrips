import re

# *******************************************************************
# FOLLOWING REGEX ARE USED TO IDENTIFY OBJECTS WHEN READING PBS FILES
#
# *******************************************************************
# Used to find the total number of trips stored in the PBS file

# Used to find page numbers in a PBS_trips_file
page_number_RE = re.compile(r"""
    =+\d+=+
    """, re.VERBOSE | re.DOTALL)

trips_total_RE = re.compile(r"""
    trips:\s+       #The Total number of trips legend followed by one ore more white spaces 
    (?P<trips_total>\d{1,4})        #Up to 4 digit total number of trips in the PBS trips file
    """, re.VERBOSE | re.DOTALL)