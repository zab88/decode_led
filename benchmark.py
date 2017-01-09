import os
import cv2
import numpy as np
import Led as ll
import time

test_images = [
    ('01.jpg', [1,1,1,0,1,1,0,0,1,1,1,0,1,1,0,0,1,1,1,0,1,1,0,0,1,1,1,0,1,1,0,0,1,1,1,0,1,1,0,0]),
    ('02.jpg', [1,1,1,0,1,1,0,0]), # is tail 0,0 or 0,0,1?
    ('03.jpg', [0,1,1,1,0,1,1]),
    ('04.jpg', [1,1,0,1,1,0,0,1])
]

start_time = time.time()
print 'Slow algorithm'
for test_image in test_images:
    image_original = cv2.imread('img_in'+os.sep+test_image[0])
    led = ll.Led(image_original)
    counted_array = led.getCode()
    if cmp(counted_array, test_image[1]) != 0:
        print 'Error in decoding {}:'.format(test_image[0])
        print 'correct:', test_image[1]
        print 'counted:', counted_array
    else:
        print test_image[0] + ' is correct!'
print("--- %s seconds ---" % (time.time() - start_time))


# test fast method
start_time = time.time()
print '\nFast algorithm'
for test_image in test_images:
    img_gray = cv2.imread('img_in'+os.sep+test_image[0], 0)
    counted_array = ll.Led.getCodeFast(img_gray)
    if cmp(counted_array, test_image[1]) != 0:
        print 'Error in decoding {}:'.format(test_image[0])
        print 'correct:', test_image[1]
        print 'counted:', counted_array
    else:
        print test_image[0] + ' is correct!'
print("--- %s seconds ---" % (time.time() - start_time))
