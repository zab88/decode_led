import cv2
import numpy as np

class Led:
    def __init__(self, img_bgr):
        self.img_origin = img_bgr.copy()
        self.img_gray = cv2.cvtColor(self.img_origin, cv2.COLOR_BGR2GRAY)
        self.img_canny = cv2.Canny(self.img_gray, 60, 150)
        grad_x = cv2.Sobel(self.img_gray, cv2.CV_16S, 1, 0, ksize=1, scale=1, delta=0, borderType=cv2.BORDER_DEFAULT)
        self.img_sobel_x = cv2.convertScaleAbs(grad_x)
        self.img_thres_127 = cv2.threshold(self.img_gray, 127, 255, cv2.THRESH_BINARY)[1]

    def getCode(self):
        # projection canny edges on x axis
        rows_sum = self.img_canny.sum(axis=0)

        # left and right border of eclipse
        start_x = next(k for k, v in enumerate(rows_sum) if v > 0)
        end_x = len(rows_sum) - next(k for k, v in enumerate(rows_sum[::-1]) if v > 0)

        # width will approximated by the most representative lines (from center)
        max_strip_length = max(rows_sum)
        widths, widths_all, stripes_x = [], [], []
        cur_sum, cur_sum2 = 0, 0
        for x, i in enumerate(rows_sum):
            cur_sum += 1
            cur_sum2 += 1
            if i > max_strip_length / 2:
                widths.append(cur_sum)
                cur_sum = 0
            if i > 255 * 20 or (x in [start_x, end_x]):
                widths_all.append(cur_sum2)
                stripes_x.append(x)
                cur_sum2 = 0
        widths, widths_all = widths[1:], widths_all[1:]

        # get 3 greatest values
        widths_copy = widths[:]
        max_123 = []
        for i in xrange(0, 3):
            max_123.append(max(widths_copy))
            del widths_copy[widths_copy.index(max_123[-1])]
        # this 3 greatest values are etalon for regular strip width (not separator)
        wide_strip_len = int(sum(max_123) / len(max_123))
        min_wide = int(wide_strip_len * 0.65)

        # making final array
        res = []
        for k, i in enumerate(widths_all):
            if i >= min_wide:
                # get color
                non_zero = cv2.countNonZero(self.img_thres_127[:, stripes_x[k] + 1:stripes_x[k + 1] - 1])
                if non_zero > 100:
                    res.append(1)
                else:
                    res.append(0)
        return res