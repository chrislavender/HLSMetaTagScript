#!/usr/bin/env python

# This is to convert time code markers from a .txt file generated from FCP.
# It is currently set up for one use case, but is evolving to be able to
# dynamically do all steps on the fly.

# Currently these assumptions are made:
# a) you have Apple's HLS command line tools installed
# b) you have created 7 id3 tags (future: dynamically determine)
# c) the tags are located in a folder called "meta_tags" (future: dynamically create id3 tags and destroy when finished)
# d) the meta_tags folder location is set correctly via the gID3TagsLocation variable (future: will be unneeded)
# e) the .txt file with the FCP markers is located in the same directory as 7 .mp4 encodings
#		generated from Compressor with this title structure: aTitle-encoding.mp4
#	1) title-64_audio.m4a
#	2) title-64_video.mp4
#	3) title-100.mp4
#	4) title-200.mp4
#	5) title-400.mp4
#	6) title-600.mp4
#	7) title-1200.mp4
# f) the markers from FCP correspond to the colors in the assignFileName function. (future: dynamically determine)

# this script should be run from inside the folder where the assets are
# you can either put this script in that folder OR add the script to your bash $PATH

#flag for proper handling of division
from __future__ import division

import sys
import subprocess
import glob
import fnmatch
import os

gID3TagsLocation = "/Users/Chris/bin/meta_tags/"
gInputFile = ""
gStreamTitle = ""
gMacrofile = "macrofile.txt"
gStartsOutputFile = ""
gAnswerAnimationTime = 1.0
# timePerFrame = 1 / ticks per second
# should be less than the video fps
gTimePerFrame = 1 / 20


def convertTimeCodeStringToFloat(tc_string):
    timeAsFloat = 0.0
    tc_elements = tc_string.split(":", 4)

    sys.stdout.write("time code = " + tc_elements[1] + " : " + tc_elements[2] + " : " + tc_elements[3] + "\n")

    i = 1

    for i in range(len(tc_elements)):
        if i == 1:
            timeAsFloat = timeAsFloat + float(tc_elements[1]) * 60
        elif i == 2:
            timeAsFloat = timeAsFloat + float(tc_elements[2])
        elif i == 3:
            timeAsFloat = timeAsFloat + float(tc_elements[3]) * gTimePerFrame

    sys.stdout.write("absolute seconds = " + str(timeAsFloat) + "\n")
    return timeAsFloat


def assignFileName(tag_name):
# FCP outputs the markers with a color associated

    if tag_name == "Red":
        fileName = "1.id3"
    elif tag_name == "Orange":
        fileName = "2.id3"
    elif tag_name == "Yellow":
        fileName = "3.id3"
    elif tag_name == "Green":
        fileName = "5.id3"
    elif tag_name == "Turquoise":
        fileName = "6.id3"
    elif tag_name == "Blue":
        fileName = "7.id3"
    else:
        fileName = "none"

    return fileName

# check for an input file argument
if (len(sys.argv) > 1):
    gInputFile = sys.argv[1]
else:
    sys.exit("ERROR: No input file")

# check for an output file argument
# if none given use the default
if (len(sys.argv) > 2):
    gStreamTitle = sys.argv[2]
    gStartsOutputFile = sys.argv[2] + "_starts"

# if none given use the default
if (len(sys.argv) > 3):
    gStartsOutputFile = sys.argv[3]

# create and open the output file
gMacrofile = gStreamTitle + "_macro.txt"
fout_markers = open(gMacrofile, "w")
fout_starts = open(gStartsOutputFile + ".txt", "w")

# next add the init tags
for num in range(1, 11):
    # print value, key
    floatString = str(num)
    fout_markers.write(floatString + " id3 " + gID3TagsLocation + "0.id3" + "\n")

fyle = open(gInputFile)

count = 0

# go through each line
for lyne in fyle:
    txt_elements = lyne.split()
    #if there are less than 5 elements it's probably a blank line (or something else is up)
    if len(txt_elements) < 5:
        continue

    time_code = txt_elements[4]
    id3_file = assignFileName(txt_elements[6])

    if id3_file == "none":
        continue

    #convert to a float
    time = convertTimeCodeStringToFloat(time_code)
    # possible answers are animated on the screen so
    # subtract animation time from the presentation time
    if id3_file == "3.id3":
        time = time - gAnswerAnimationTime

    # print to the file
    floatString = str(time)
    fout_markers.write(floatString + " id3 " + gID3TagsLocation + id3_file + "\n")

    if id3_file == "1.id3":
        count += 1
        fout_starts.write("Q" + str(count) + " " + floatString + "\n")

fout_markers.close()
fyle.close()

# organize the mov files
movGlob = glob.glob("*.mov")
if movGlob:
    if os.path.exists("_mov") is False:
        subprocess.call(["mkdir", "_mov"])
    for movFileName in movGlob:
        subprocess.call(["mv", movFileName, "_mov/"])

# create a dictionary for the mp4 files keyed by folder destination
fileNameDict = {}

# grab the .mp4 encodings
mp4Glob = glob.glob("*.mp4")
if mp4Glob:
    for mp4FileName in mp4Glob:
        # organize the ending videos
        if fnmatch.fnmatch(mp4FileName, "*_win*") or fnmatch.fnmatch(mp4FileName, "*_lose*"):
            # if os.path.exists("_endings") is False:
            #     subprocess.call(["mkdir", "_endings"])
            # subprocess.call(["mv", mp4FileName, "_endings/"])
            continue
        # if this is not an ending video then it's an encoding
        # save a dictionary of the mp4FileNames keyed by the folderName
        folderName = mp4FileName.split("-")[1].split(".")[0]
        fileNameDict[folderName] = mp4FileName
else:
    sys.exit("ERROR: No mp4 files to segment!")

# there should be a .m4a file for the audio only stream
for m4aFileName in glob.glob("*.m4a"):
    folderName = m4aFileName.split("-")[1].split(".")[0]
    fileNameDict[folderName] = m4aFileName

if os.path.exists("_streams") is False:
    subprocess.call(["mkdir", "_streams"])

# iterate through the dictonary to stream and stamp
for folderName, fileName in fileNameDict.iteritems():
    sys.stdout.write(folderName + " " + fileName + "\n")
    subprocess.call(["mkdir", "_streams/" + folderName])

    if fnmatch.fnmatch(folderName, "*_audio"):
        subprocess.call(["mediafilesegmenter", "-t", "5", "-audio-only", "-I", "-B", gStreamTitle + "_", "-f", "_streams/" + folderName, "-M", gMacrofile, fileName])
    else:
        subprocess.call(["mediafilesegmenter", "-t", "5", "-I", "-B", gStreamTitle + "_", "-f", "_streams/" + folderName, "-M", gMacrofile, fileName])

# create a dictionary for the plist files keyed by folder destination
plistFileNameDict = {}

# grab the .mp4 encodings
for plistFileName in glob.glob("*.plist"):
    folderName = plistFileName.split("-")[1].split(".")[0]
    plistFileNameDict[folderName] = plistFileName

# this subprocess should be generated more dynamically
# we just need to consider which stream is first in the
# all.m3u8 file since that will be the first stream to load
subprocess.call(["variantplaylistcreator", "-o", "_streams/standard.m3u8", "400/prog_index.m3u8", plistFileNameDict['400'], "64_audio/prog_index.m3u8", plistFileNameDict["64_audio"], "64_video/prog_index.m3u8", plistFileNameDict["64_video"], "100/prog_index.m3u8", plistFileNameDict["100"], "200/prog_index.m3u8", plistFileNameDict["200"], "600/prog_index.m3u8", plistFileNameDict["600"]])
subprocess.call(["variantplaylistcreator", "-o", "_streams/premium.m3u8", "400/prog_index.m3u8", plistFileNameDict['400'], "64_audio/prog_index.m3u8", plistFileNameDict["64_audio"], "64_video/prog_index.m3u8", plistFileNameDict["64_video"], "100/prog_index.m3u8", plistFileNameDict["100"], "200/prog_index.m3u8", plistFileNameDict["200"], "600/prog_index.m3u8", plistFileNameDict["600"], "1200/prog_index.m3u8", plistFileNameDict["1200"]])
subprocess.call(["variantplaylistcreator", "-o", "_streams/phone.m3u8", "200/prog_index.m3u8", plistFileNameDict["200"], "64_audio/prog_index.m3u8", plistFileNameDict["64_audio"], "64_video/prog_index.m3u8", plistFileNameDict["64_video"], "100/prog_index.m3u8", plistFileNameDict["100"], "400/prog_index.m3u8", plistFileNameDict['400']])

# clean up
for plistFileName in glob.glob("*.plist"):
    subprocess.call(["rm", plistFileName])
