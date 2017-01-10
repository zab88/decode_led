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

    def getLedContour(self):
        self.img_thres_200 = cv2.threshold(self.img_gray, 180, 255, cv2.THRESH_BINARY)[1]
        contours, _ = cv2.findContours(self.img_thres_200, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        left_x, right_x = self.img_thres_200.shape[1], 0
        left_y, right_y = None, None
        for cnt in contours:
            approx = cv2.approxPolyDP(cnt, 0.001 * cv2.arcLength(cnt, True), True)
            approx_area = cv2.contourArea(approx)
            # deleting too small blobs
            if approx_area < 20:
                continue
            x_cnt, y_cnt, w_cnt, h_cnt = cv2.boundingRect(cnt)
            if x_cnt < left_x:
                left_x = x_cnt
                left_y = y_cnt + h_cnt/2
            if x_cnt + w_cnt > right_x:
                right_x = x_cnt + w_cnt
                right_y = y_cnt + h_cnt/2
        cv2.line(self.img_thres_200, (left_x, left_y), (right_x, right_y), (255), 1)

        contours, _ = cv2.findContours(self.img_thres_200, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            hull = cv2.convexHull(cnt)
            approx = cv2.approxPolyDP(hull, 0.001 * cv2.arcLength(hull, True), True)
            approx_area = cv2.contourArea(approx)
            if approx_area < 400:
                continue

            self.contour_bin = np.zeros(self.img_thres_127.shape, np.uint8)
            self.contour_led = [approx]
            cv2.drawContours(self.contour_bin, [approx], 0, (255), -1)

            M = cv2.moments(approx)
            if M["m00"] == 0:
                continue
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            #cv2.circle(self.contour_bin, (cX, cY), 5, (0), -1)
        self.led_center = (cX, cY)
        self.img_origin_cleaned = np.bitwise_and(self.contour_bin, self.img_gray)

    @staticmethod
    def getCodeFast(img_gray):
        win_w = 3
        l3_thres = win_w*50

        img_thres_1 = cv2.threshold(img_gray, 40, 255, cv2.THRESH_BINARY)[1]
        img_thres_2 = cv2.threshold(img_gray, 225, 255, cv2.THRESH_BINARY)[1]
        # img_thres_127 = cv2.threshold(img_gray, 127, 255, cv2.THRESH_BINARY)[1]
        separators_bin = np.bitwise_xor(img_thres_1, img_thres_2)

        rows_sum = separators_bin.sum(axis=0)

        # ss = cv2.subtract(img_thres_1, separators_bin)
        # ss2 = cv2.subtract(255-img_thres_2, separators_bin)
        # cv2.imshow('white', ss)
        # cv2.imshow('black', ss2)
        # cv2.imshow('ser', separators_bin)
        # cv2.waitKey()
        # exit()

        # left and right border of eclipse
        start_x = next(k for k, v in enumerate(rows_sum) if v > 0)
        # end_x = len(rows_sum) - next(k for k, v in enumerate(rows_sum[::-1]) if v > 0)

        res = []
        cur_sum = 0
        zero = 0
        for x, val in enumerate(rows_sum):
            if x <= start_x:
                continue
            # num = cv2.countNonZero(img_gray[:, x:x+1])
            num = np.count_nonzero(separators_bin[:, x:x+win_w])
            # continue on separator
            if num < l3_thres:
                cur_sum = 0
                continue
            get_color = np.count_nonzero(img_thres_2[:, x:x+win_w])
            if get_color > zero and cur_sum==0:
                # white
                # print 'white', num, get_color
                res.append(1)
                cur_sum += 1
            elif get_color <= zero and cur_sum==0:
                # black
                # print 'black', num, get_color
                res.append(0)
                cur_sum += 1

        return res