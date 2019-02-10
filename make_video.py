#!/usr/bin/python
# -*- coding: utf-8 -*

import sys, os, time
import pathlib
import cv2

def makeVideo( inPattern, outFile, outCodec ):
    # Get video stream dimensions from the image size
    print("MakeVideo : %s => %s (%s)"%(inPattern, outFile, outCodec))
    inPattern = pathlib.Path(inPattern)
    image = cv2.imread(str(inPattern / os.listdir(str(inPattern))[0]))
    height, width, channel = image.shape
    print("Dimension detected : %s-%s"%(width,height))
    video = cv2.VideoWriter(outFile,-1,30.0,(width,height), True)
    for file in os.listdir(str(inPattern)):
        print(str(inPattern / file))
        try:
            image = cv2.imread(str(inPattern / file))
            image = cv2.resize(image, (width,height))
            video.write(image)
        except Exception  as e:
            print(str(e))
    video.release()

if __name__== '__main__':
    if len( sys.argv )!= 4:
        print "Usage: make_video <in_file_pattern> <out_file> <format>\n\tformat= { mpeg1video | mpeg2video }"
    else:
        makeVideo( sys.argv[ 1 ], sys.argv[ 2 ], sys.argv[ 3 ] )
