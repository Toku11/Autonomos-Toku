#!/usr/bin/env python
from __future__ import print_function
import roslib
roslib.load_manifest('cmt_test_python')
import sys
import rospy
import cv2
from std_msgs.msg import String
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
import argparse

from numpy import empty, nan
import os
import time
import CMT
import numpy as np
import util


CMT = CMT.CMT()

CMT.estimate_scale = 'estimate_scale'
CMT.estimate_rotation ='estimate_rotation'

pause_time = 10

frame=0
started =0
#cv_image= np.array([0,0])

class image_converter:

  def __init__(self):
    self.image_pub = rospy.Publisher("image_topic_2",Image)

    self.bridge = CvBridge()
    self.image_sub = rospy.Subscriber("/depth/image_raw",Image,self.callback)
    cv2.destroyAllWindows()
  def callback(self,data):
    global frame
    global started
    #global cv_image
    try:
        cv_image = self.bridge.imgmsg_to_cv2(data, "bgr8")
	print(self.bridge.imgmsg_to_cv2(data, "bgr8"))
    except CvBridgeError as e:
        print(e)

    # Clean up
    
    
    preview = 'preview'
            # If no input path was specified, open camera device
    #cap = cv2.VideoCapture(0)
    if preview is None:
        preview = True
    
        # Check if videocapture is working
    #if not cap.isOpened():
    #    print("Unable to open video input.")
    #    sys.exit(1)
    
    #while preview:
        #status, im = cap.read()
    status=True
        
    im=cv_image
    
    if started== 0:
        cv2.imshow('Preview', im)
        #cv2.imshow('Preview', cv_image)
        k = cv2.waitKey(10)
        if not k == -1:
            #break
            im0 = cv_image
            im_gray0 = cv2.cvtColor(im0, cv2.COLOR_BGR2GRAY)
	    #im_gray0 = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            im_draw = np.copy(cv_image)
            
            (tl, br) = util.get_rect(im_draw)
            print("using", tl, br, "as init bb")
            CMT.initialise(im_gray0, tl, br)
            frame = 1
            started=1
            cv2.destroyAllWindows()
    
    

        # Read first frame
    #status, im0 = cap.read()
    
    if started==1:
            # Read image
        #status, im = cap.read()
        #im=cv_image
        if not status:
            cv2.destroyAllWindows()
            sys.exit(1)
        im_gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
	#im_gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        im_draw = np.copy(im)
	#im_draw = np.copy(cv_image)
    
        tic = time.time()
        CMT.process_frame(im_gray)
        toc = time.time()
    
        # Display results
    
        # Draw updated estimate
        if CMT.has_result:
    
            cv2.line(im_draw, CMT.tl, CMT.tr, (255, 0, 0), 4)
            cv2.line(im_draw, CMT.tr, CMT.br, (255, 0, 0), 4)
            cv2.line(im_draw, CMT.br, CMT.bl, (255, 0, 0), 4)
            cv2.line(im_draw, CMT.bl, CMT.tl, (255, 0, 0), 4)
    
        util.draw_keypoints(CMT.tracked_keypoints, im_draw, (255, 255, 255))
            # this is from simplescale
        util.draw_keypoints(CMT.votes[:, :2], im_draw)  # blue
        util.draw_keypoints(CMT.outliers[:, :2], im_draw, (0, 0, 255))
        cv2.imshow('main', im_draw)
        #cv2.imshow('main', im_draw)
    
                # Check key input
        k = cv2.waitKey(pause_time)
        key = chr(k & 255)
        if key == 'q':
            #cap.release()        
            cv2.destroyAllWindows()
            rospy.signal_shutdown("ROSPy Shutdown")
            #break
            sys.exit(1)
        if key == 'd':
            import ipdb; ipdb.set_trace()
    
        # Remember image
        im_prev = im_gray
    
        # Advance frame number
        frame += 1
    
        print("{5:04d}: center: {0:.2f},{1:.2f} scale: {2:.2f}, active: {3:03d}, {4:04.0f}ms".format(CMT.center[0], CMT.center[1], CMT.scale_estimate, CMT.active_keypoints.shape[0], 1000 * (toc - tic), frame))
    


    #(rows,cols,channels) = cv_image.shape
    #if cols > 60 and rows > 60 :
    #  cv2.circle(cv_image, (50,50), 10, 255)

    cv2.imshow("Image window", cv_image)
    cv2.waitKey(3)

    try:
      self.image_pub.publish(self.bridge.cv2_to_imgmsg(cv_image, "bgr8"))
    except CvBridgeError as e:
      print(e)

def main(args):
  ic = image_converter()
  rospy.init_node('image_converter', anonymous=True)
  try:
    rospy.spin()
  except KeyboardInterrupt:
    print("Shutting down")
  cv2.destroyAllWindows()

if __name__ == '__main__':
    main(sys.argv)
