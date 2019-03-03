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