# Python Version (currently supported)
om solution swapper csvreader python\
original ahk by [panic](https://github.com/ianh)\
python port by omgitsabist

download the file and set up the metrics in any text editor

F8 goes back to the next worst solution\
F9 swaps the current solution out for the next best solution\
F10 updates the metrics overlay\
F11 repopulates past solves overlay with all non superceded solves in selection\
F12 repopulates past solves overlay with all solves in selection\
double-clicking a solution in the list will swap in that one

for multiple metrics, i recommend making multiple copies of this script\
after finishing one metric, close the script for it and open the script for the next one

all external libraries and files should automatically download and install\
but in case they don't you can find them here:

wxpython - for gui (https://wxpython.org/index.html) \
pynput - for input detection (https://pypi.org/project/pynput/) \
om.py - omsim python package (http://critelli.technology/om.py) \
libverify - opus magnum simulator (https://github.com/ianh/omsim/releases)

pynput has certain limitations on different operating systems that you can find out about here https://pynput.readthedocs.io/en/latest/limitations.html

# AHK Version
om solution swapper\
by [panic](https://github.com/ianh)\
with very bad edits by omgitsabist

dependant on [omsim](https://github.com/ianh/omsim)\
works best with files downloaded from admin pages of http://events.critelli.technology/

at start, measures the Primary(), Secondary() and Tertiary() metrics for each solution in the SOLUTIONS folder, then copies the worst one into the GAMEFILES folder

F8 goes back to the next worst solution\
F9 swaps the current solution out for the next best solution\
F10 updates the metrics overlay\
F11 repopulates past solves overlay with all non superceded solves in selection\
F12 repopulates past solves overlay with all solves in selection\
double-clicking a solution in the list will swap in that one

for multiple metrics, i recommend making multiple copies of this script --\
after finishing one metric, close the script for it and open the script for the next one

simulator version runs libverify to parse metrics\
csvreader version reads directly from a csv file
