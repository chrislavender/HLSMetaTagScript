#!/usr/bin/env python

# This is to convert time code markers from a .txt file generated from FCP.
# It is currently set up for one use case, but is evolving to be able to
# dynamically do all steps on the fly

# Currently these assumptions are made:
# a) you have Apple's HLS command line tools installed
# b) the app requires 6 id3 tags (future: dynamically determine)
# c) the .txt file with the FCP markers is located in the same
#		directory as 7 .mp4 encodings generated from Compressor
# d) the markers from FCP correspond to the colors in the assignFileName
#       function. (future: dynamically determine)

# this script should be run from inside the directory where the assets are located
# you can either put this script in that directory OR
#                   add the script to your bash $PATH


############################################################################
## FORMAT FOR RUNNING
#
## hls_script.py <path to markers.txt file> <optional prefix for .ts files>
#############################################################################

#flag for proper handling of division
from __future__ import division

import sys
import subprocess
import glob
import fnmatch
import os
import re

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

    sys.stdout.write("time code = "
                     + tc_elements[1] + " : "
                     + tc_elements[2] + " : "
                     + tc_elements[3] + "\n")

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
# these are Braindex specific
# FCP outputs the markers with a color associated

    if tag_name == "Red":
        fileName = "1.id3"
    elif tag_name == "Orange":
        fileName = "2.id3"
    elif tag_name == "Yellow":
        fileName = "3.id3"
    elif tag_name == "Green":
        fileName = "4.id3"
    elif tag_name == "Turquoise":
        fileName = "5.id3"
    elif tag_name == "Blue":
        fileName = "6.id3"
    else:
        fileName = "none"

    return fileName


def metaTagText(fileName):
# these are Braindex specific

    if fileName == "1.id3":
        tagText = "setup"
    elif fileName == "2.id3":
        tagText = "question"
    elif fileName == "3.id3":
        tagText = "possible_answers"
    elif fileName == "4.id3":
        tagText = "contestant_answer"
    elif fileName == "5.id3":
        tagText = "correct_answer"
    elif fileName == "6.id3":
        tagText = "reset"
    else:
        tagText = "error too many tags"

    return tagText


def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    # '''
    # alist.sort(key=natural_keys) sorts in human order
    # http://nedbatchelder.com/blog/200712/human_sorting.html
    # (See Toothy's implementation in the comments)
    # '''
    return [atoi(c) for c in re.split('(\d+)', text)]


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
subprocess.call(["id3taggenerator", "-o", "0.id3", "-text", "init"])
for num in range(1, 11):
    # print value, key
    floatString = str(num)
    fout_markers.write(floatString + " id3 " + "0.id3" + "\n")

fyle = open(gInputFile)

count = 0

# go through each line
for lyne in fyle:
    txt_elements = lyne.split()
    # if there are less than 5 elements it's probably
    # a blank line (or something else is up)
    # a rudimentary validation but works for now
    if len(txt_elements) < 5:
        continue

    time_code = txt_elements[-3]
    id3_fileName = assignFileName(txt_elements[-1])

    if id3_fileName == "none":
        continue

    tag_text = metaTagText(id3_fileName)

    subprocess.call(["id3taggenerator", "-o", id3_fileName, "-text", tag_text])

    #convert to a float
    time = convertTimeCodeStringToFloat(time_code)
    # possible answers are animated on the screen so
    # subtract animation time from the presentation time
    if id3_fileName == "3.id3":
        time = time - gAnswerAnimationTime

    # print to the file
    floatString = str(time)
    fout_markers.write(floatString + " id3 " + id3_fileName + "\n")

    if id3_fileName == "1.id3":
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
        if fnmatch.fnmatch(mp4FileName,
                           "*_win*") or fnmatch.fnmatch(mp4FileName,
                                                        "*_lose*"):
            # if os.path.exists("_endings") is False:
            #     subprocess.call(["mkdir", "_endings"])
            # subprocess.call(["mv", mp4FileName, "_endings/"])
            continue

        # currently we are not processing the highest bit rate stream
        # this should be an optional argument or something
        elif not fnmatch.fnmatch(mp4FileName, "*1200*"):
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

if os.path.exists("_streams") is True:
    subprocess.call(["rm", "-r", "_streams"])
    
subprocess.call(["mkdir", "_streams"])

# iterate through the dictonary to stream and stamp
for folderName, fileName in fileNameDict.iteritems():
    sys.stdout.write(folderName + " " + fileName + "\n")
    subprocess.call(["mkdir", "_streams/" + folderName])

    if fnmatch.fnmatch(folderName, "*_audio"):
        subprocess.call(["mediafilesegmenter",
                        "-t", "5",
                        "-audio-only",
                        "-I", "-B", gStreamTitle + "_",
                        "-f", "_streams/" + folderName,
                        "-M", gMacrofile,
                        fileName])
    # currently we are not processing the highest bit rate stream
    # this should be an optional argument or something
    elif not fnmatch.fnmatch(folderName, "*1200*"):
        subprocess.call(["mediafilesegmenter",
                        "-t", "5",
                        "-I", "-B", gStreamTitle + "_",
                        "-f", "_streams/" + folderName,
                        "-M", gMacrofile,
                        fileName])

# create a dictionary for the plist files keyed by folder destination
plistFileNameDict = {}

# grab the .mp4 encodings
for plistFileName in glob.glob("*.plist"):
    folderName = plistFileName.split("-")[1].split(".")[0]
    plistFileNameDict[folderName] = plistFileName

# grab the file names
fileNameList = list(fileNameDict.keys())

# perform a "human sort"
# http://stackoverflow.com/questions/5967500/how-to-correctly-sort-string-with-number-inside
sortedFileNameList = sorted(fileNameList, key=natural_keys)

# we need to consider which stream is first in the
# top level .m3u8 file since that will be the first stream to load
# fix the order of the variant play list

## Standard Stream
standardVariantListOrder = [4, 0, 1, 2, 3, 5]
variantCommandStringList = ["variantplaylistcreator", "-o", "_streams/standard.m3u8"]
for item in [sortedFileNameList[i] for i in standardVariantListOrder]:
    variantCommandStringList.append(item + "/prog_index.m3u8")
    variantCommandStringList.append(plistFileNameDict[item])
subprocess.call(variantCommandStringList)

## Phone Stream
phoneVariantListOrder = [3, 0, 1, 2, 4, 5]
variantCommandStringList = ["variantplaylistcreator", "-o", "_streams/phone.m3u8"]
for item in [sortedFileNameList[i] for i in phoneVariantListOrder]:
    variantCommandStringList.append(item + "/prog_index.m3u8")
    variantCommandStringList.append(plistFileNameDict[item])
subprocess.call(variantCommandStringList)

## Premium Stream
# premiumVariantListOrder = [4, 0, 1, 2, 3, 5, 6]
# variantCommandStringList = ["variantplaylistcreator", "-o", "_streams/premium.m3u8"]
# for item in [sortedFileNameList[i] for i in premiumVariantListOrder]:
#     variantCommandStringList.append(item + "/prog_index.m3u8")
#     variantCommandStringList.append(plistFileNameDict[item])
# subprocess.call(variantCommandStringList)

# clean up
for plistFileName in glob.glob("*.plist"):
    subprocess.call(["rm", plistFileName])

for id3FileList in glob.glob("*.id3"):
    subprocess.call(["rm", id3FileList])
