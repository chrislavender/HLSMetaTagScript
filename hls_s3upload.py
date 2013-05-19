#!/usr/bin/env python

# This script is to upload HLS assets to an S3 bucket
# It's required to ensure that the headers for the
# .m3u8 and .ts files are set correctly.

# Currently these assumptions are made:
# a) you have command line access to your s3 bucket
# b) you have s3cmd installed
# c) you're running this from inside the episode's directory
#   above a directory called _streams in which the .ts and
#   .m3u8 files are located
#
# SAMPLE DIRECTORY STRUCTURE
#
# |-EpisodeNum
#   <run from this level>
#    |---_streams
#    |-----100
#    |-----200
#    |-----400
#    |-----600
#    |-----64_audio
#    |-----64_video
#
# you can either put this script in that folder OR
#                   add the script to your bash $PATH

import subprocess
import glob
import sys
import os

gS3BaseUrl = "s3://touchframetesting/"
gStreamsDir = "_streams"


def get_immediate_subdirectories(dir):
    return [name for name in os.listdir(dir)
            if os.path.isdir(os.path.join(dir, name))]


parentFilePath = os.path.abspath(os.path.join(" ", os.pardir))
parentFilePathList = parentFilePath.split("/")

# grab the .m3u8 files
m3u8Glob = glob.glob(gStreamsDir + "/*.m3u8")
if not m3u8Glob:
        sys.exit("ERROR: No .m3u8 files located in" + gStreamsDir + "!")

variantM3u8CommandString = "s3cmd -m audio/x-mpegurl put" + " " + \
    gStreamsDir + "/*.m3u8" + " " + \
    gS3BaseUrl + parentFilePathList[-1] + "/"

print "Uploading:" + " " + variantM3u8CommandString
subprocess.call(variantM3u8CommandString, shell=True)

streamSubDirList = get_immediate_subdirectories(gStreamsDir)

for subDir in streamSubDirList:
    subDirPath = gStreamsDir + "/" + subDir
    m3u8Glob = glob.glob(subDirPath + "/*.m3u8")

    if not m3u8Glob:
        sys.exit("ERROR: m3u8 file is missing for the stream in " + subDirPath + "!")

    m3u8CommandString = "s3cmd -m audio/x-mpegurl put " + \
        subDirPath + "/*.m3u8 " + gS3BaseUrl + parentFilePathList[-1] + "/" + subDir + "/"

    print "Uploading:" + " " + m3u8CommandString
    subprocess.call(m3u8CommandString, shell=True)

    tsGlob = glob.glob(subDirPath + "/*.ts")
    aacGlob = glob.glob(subDirPath + "/*.aac")

    if tsGlob:
        tsCommandString = "s3cmd -m video/mp2t put " + \
            subDirPath + "/*.ts " + gS3BaseUrl + parentFilePathList[-1] + "/" + subDir + "/"

        print "Uploading:" + " " + tsCommandString
        subprocess.call(tsCommandString, shell=True)

    elif aacGlob:
        aacCommandString = "s3cmd -m audio/x-aac put " + \
            subDirPath + "/*.aac " + gS3BaseUrl + parentFilePathList[-1] + "/" + subDir + "/"

        print "Uploading:" + " " + aacCommandString
        subprocess.call(aacCommandString, shell=True)

    else:
        sys.exit("ERROR: " + subDir)

aclCommandString = "s3cmd setacl " + \
    gS3BaseUrl + parentFilePathList[-1] + "/" + " " + \
    "--acl-public --recursive"

print "Making Files Public:" + " " + aclCommandString
subprocess.call(aclCommandString, shell=True)

validationCommandString = "mediastreamvalidator" + " " + \
    gS3BaseUrl + parentFilePathList[-1] + "/*.m3u8"
print "Validating:" + " " + validationCommandString
subprocess.call(validationCommandString, shell=True)
