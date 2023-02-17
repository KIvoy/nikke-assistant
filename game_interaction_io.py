from functools import wraps
from types import GeneratorType
import numpy as np
from easyocr import Reader
import pyautogui
import time
from PIL import ImageGrab
from types import GeneratorType
import cv2
import pytesseract
pytesseract.pytesseract.tesseract_cmd=r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
import re
from location_box import LocationBox

class GameInteractionIO:
    bounce_key_delay = 0.07
    inter_key_delay = 0.1
    post_action_delay = 1
    language = ['en','ch_sim']
    reader = Reader(language)
    
    def post_action_generator(delay):
        def post_action(function):
            @wraps(function)
            def wrapper(*args, **kwargs):
                retval = function(*args, **kwargs)
                GameInteractionIO.delay(delay)
                return retval
            return wrapper
        return post_action
    
    post_action = post_action_generator(post_action_delay)
    
    def get_available_applications(verbose=False):
        app_list = [app for app in pyautogui.getAllWindows() if app.title!=""]
        if not verbose:
            app_list = [app.title for app in app_list]
        return app_list
    
    def stretch_white_space(image):
        white_space = np.array([[255]*(image.shape[1])]*2)
        p = np.concatenate((white_space, image))

        a = np.array([[255]*(p.shape[0])]).T
        prev = 0
        empty_count = 5
        count = 0
        digit = []
        for ind in range(p.shape[1]):
            if np.mean(p[:,ind]) == 255:
                a = np.concatenate((a, p[:,prev:ind+1]), axis=1)
                a = np.concatenate((a, np.array([p[:,ind]]*11).T), axis=1)
                if np.mean(p[:,prev:ind+1].flatten()) != 255:
                    digit.append(np.array(p[:,prev:ind+1], dtype=np.uint8))
                prev = ind
                count += 1
                if count > empty_count:
                    break
            else:
                count = 0
        a = a.astype(np.uint8)
        return a, digit
    
    
    def preprocess_image(image, threshold='global'):
        """
        preprocess a PIL image to make it more visible for text recognition
        """
        image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        if threshold =='global':
            ret, thresh = cv2.threshold(gray,110,255,cv2.THRESH_BINARY)
            new_image = thresh
        elif threshold == 'adaptive':
            thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 13, 2)
            erode = cv2.erode(thresh, np.array((7, 7)), iterations=1)
            new_image - erode
        return new_image
    
    
    def preprocess_image_number(image):
        """
        preprocess a PIL image to make it more visible for text recognition
        """
        image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        ret, thresh = cv2.threshold(gray,110,255,cv2.THRESH_BINARY)
        erode = cv2.erode(thresh, np.array((9, 9)), iterations=1)
        stretch_image, digit = GameInteractionIO.stretch_white_space(erode)
        return stretch_image 
    
    
    def read_text(image_name, model_name=None, detail=1, in_line=True):
        if not model_name:
            model_name = GameInteractionIO.reader

        frame = cv2.cvtColor(np.array(image_name), cv2.COLOR_RGB2BGR)
        
        # Read the data
        result = model_name.readtext(frame, detail=detail, paragraph=in_line)
        return result
    
    def _read_number(image, l=0, im_type=6):
        if l==0:
            value = pytesseract.image_to_string(image,
                        config=f'--psm {im_type} outputbase digits tessedit_char_whitelist=0123456789').strip().replace(" ", "")
        elif l==1:
            image = GameInteractionIO.preprocess_image_number(image)
            value = pytesseract.image_to_string(image,
                        config=f'--psm {im_type} outputbase digits tessedit_char_whitelist=0123456789').strip().replace(" ", "")
        
        value = re.sub('[^A-Za-z0-9]+', '\n', value)
        if not value.isdigit():
            return False
        value = int(value)
        return value
    
    def read_number(image, l=0):
        """
        image types
        #   0    Orientation and script detection (OSD) only.
        #   1    Automatic page segmentation with OSD.
        #   2    Automatic page segmentation, but no OSD, or OCR.
        #   3    Fully automatic page segmentation, but no OSD. (Default)
        #   4    Assume a single column of text of variable sizes.
        #   5    Assume a single uniform block of vertically aligned text.
        #   6    Assume a single uniform block of text.
        #   7    Treat the image as a single text line.
        #   8    Treat the image as a single word.
        #   9    Treat the image as a single word in a circle.
        #  10    Treat the image as a single character.
        #  11    Sparse text. Find as much text as possible in no particular order.
        #  12    Sparse text with OSD.
        #  13    Raw line. Treat the image as a single text line,
        #             bypassing hacks that are Tesseract-specific.
        """
        value = False
        im_type_list = [6,7,8,9,10,11,12,13]
        value_list = []
        for im_type in im_type_list:
            value = GameInteractionIO._read_number(image, l, im_type)
            if value:
                value_list.append(value)
        if not value:
            value = GameInteractionIO.read_text(image, detail=0)
            if value:
                value = value[0]
                value = re.sub('[^A-Za-z0-9]+', '\n', value)
                if value.isdigit():
                    value = int(value)
                    value_list.append(value)
        if len(value_list)>0:
            value = max(value_list)
        return value
    
    
    def repeat_press(key, hold_time):
        start_time = time.time()
        while time.time() - start_time < hold_time:
            pyautogui.press(key)

    def hold_key(key, hold_time):
        pyautogui.keyDown(key)
        print('holding %s' % key)
        time.sleep(hold_time)
        pyautogui.keyUp(key)

    def hold_key_combo(keydown, key):
        pyautogui.keyDown(keydown)
        pyautogui.keyDown(key)
        time.sleep(GameInteractionIO.inter_key_delay)
        pyautogui.keyUp(key)
        pyautogui.keyUp(keydown)

    def double_click(key):
        print('double clicking %s' % key)
        pyautogui.keyDown(key)
        time.sleep(GameInteractionIO.bounce_key_delay)
        pyautogui.keyUp(key)
        time.sleep(GameInteractionIO.inter_key_delay)
        pyautogui.keyDown(key)
        time.sleep(GameInteractionIO.bounce_key_delay)
        pyautogui.keyUp(key)

    def single_click(key):
        print('single clicking %s' % key)
        pyautogui.keyDown(key)
        time.sleep(GameInteractionIO.bounce_key_delay)
        pyautogui.keyUp(key)
    
    def scroll(distance):
        pyautogui.scroll(distance)
        time.sleep(GameInteractionIO.inter_key_delay)
        
        
    def mouse_right_click(cursor_coord=[None, None]):
        pyautogui.click(*cursor_coord, clicks=1, interval=1, button='right')

    def mouse_left_click(cursor_coord=[None, None]):
        pyautogui.click(*cursor_coord, clicks=1, interval=1, button='left')

    def mouse_right_double_click(cursor_coord):
        pyautogui.click(*cursor_coord, clicks=2, interval=0.1, button='right')

    def mouse_left_double_click(cursor_coord):
        pyautogui.click(*cursor_coord, clicks=2, interval=0.1, button='left')
    
    def mouse_multiclick(cursor_coord, clicks=2, interval=0.1, button='left'):
        pyautogui.click(*cursor_coord, clicks=clicks, interval=interval, button='left')
    
    def delay(delay_time):
        if delay_time < 0:
            delay_time = 0
        time.sleep(delay_time)
    
    def get_image_center(location):
        return np.array([location.left + location.width//2, location.top + location.height//2])

    def get_window_info(logo_path, resolution):
        window_corner_location = GameInteractionIO.locate_image(logo_path, confidence=0.9)
        if not window_corner_location:
            return None
        offset = [-3, -4, 0, 20]
        # offset = [-3, 16, 0, 0]
        x_min = window_corner_location.left + offset[0]
        width = resolution[0] + offset[2]
        y_min = window_corner_location.top + offset[1]
        height = resolution[1] + offset[3]
        window_info_array = [x_min, y_min, width, height]
        window_info_location = LocationBox(*window_info_array)
        return window_info_location

    def _rmse(measured, truth):
        rmse = np.linalg.norm(measured - truth) / np.sqrt(len(truth))
        return rmse
    
    def _remove_duplicated_location(image_location_list, threshold=0.1):
        if not image_location_list:
            return image_location_list
        il_prev = image_location_list[0]
        new_image_location_list = [il_prev]
        for il in image_location_list[1:]:
            if abs(il.top - il_prev.top) > il.height*threshold or abs(il.left - il_prev.left) > il.width*threshold:
                new_image_location_list.append(il)
                il_prev = il
        return new_image_location_list
    
    def locate_image(image_path, master_image_path=None, confidence=0.8, region=None, multi=False, multi_threshold=0.3):
        if isinstance(image_path, list):
            location_list = []
            for im in image_path:
                if master_image_path:
                    if multi:
                        image_location = pyautogui.locateAll(im, master_image_path, confidence=confidence)
                    else:
                        image_location = pyautogui.locate(im, master_image_path, confidence=confidence)
                else:
                    if multi:
                        image_location = pyautogui.locateAllOnScreen(im, confidence=confidence, region=region)
                    else:
                        image_location = pyautogui.locateOnScreen(im, confidence=confidence, region=region)
                if image_location is not None:
                    if isinstance(image_location, GeneratorType):
                        image_location = [LocationBox(*il) for il in image_location]
                        image_location = GameInteractionIO._remove_duplicated_location(image_location, threshold=multi_threshold)
                    elif image_location is not None:
                        image_location = LocationBox(*image_location)
                    location_list.append(image_location)
            return location_list
        else:
            if master_image_path:
                if multi:
                    image_location = pyautogui.locateAll(image_path, master_image_path, confidence=confidence)
                else:
                    image_location = pyautogui.locate(image_path, master_image_path, confidence=confidence)
            else:
                if multi:  
                    image_location = pyautogui.locateAllOnScreen(image_path, confidence=confidence, region=region)
                else:
                    image_location = pyautogui.locateOnScreen(image_path, confidence=confidence, region=region)
            if isinstance(image_location, GeneratorType):
                image_location = [LocationBox(*il) for il in image_location]
                image_location = GameInteractionIO._remove_duplicated_location(image_location, threshold=multi_threshold)
            elif image_location is not None:
                image_location = LocationBox(*image_location)
            return image_location if image_location else None
    
    def exist_image(image_path, master_image_path=None, confidence=0.8, region=None, loop=False, timeout=10):
        image_location = None
        if isinstance(image_path, list):
            location_list = []
            if loop is True:
                wait_time = 0
                while image_location is None and wait_time < timeout:
                    for im in image_path:
                        if master_image_path:
                            image_location = pyautogui.locate(im, master_image_path, confidence=confidence)
                        else:
                            image_location = pyautogui.locateOnScreen(im, confidence=confidence, region=region)
                        if image_location is None:
                            GameInteractionIO.delay(1)
                            wait_time += 1
                            break
                if image_location is None:
                    return False
            else:
                for im in image_path:
                    if master_image_path:
                        image_location = pyautogui.locate(im, master_image_path, confidence=confidence)
                    else:
                        image_location = pyautogui.locateOnScreen(im, confidence=confidence, region=region)
                    if image_location is None:
                        return False
        else:
            if loop is True:
                wait_time = 0
                while image_location is None and wait_time < timeout:
                    if master_image_path:
                        image_location = pyautogui.locate(image_path, master_image_path, confidence=confidence)
                    else:
                        image_location = pyautogui.locateOnScreen(image_path, confidence=confidence, region=region)
                    if image_location is None:
                        GameInteractionIO.delay(1)
                        wait_time += 1
                        break
                if image_location is None:
                    return False
            else:
                if master_image_path:
                    image_location = pyautogui.locate(image_path, master_image_path, confidence=confidence)
                else:
                    image_location = pyautogui.locateOnScreen(image_path, confidence=confidence, region=region)
                if image_location is None:
                    return False
        return True
    
    def move_to_image_location(location, alignment='center'):
        image_cord = [location.left, location.top]
        if alignment == 'center':
            image_cord[0] += location.width//2
            image_cord[1] += location.height//2
        pyautogui.moveTo(*image_cord)

    def get_direction(source_location, destination_location):
        source_center = GameInteractionIO.get_image_center(source_location)
        destination_center = GameInteractionIO.get_image_center(destination_location)
        direction = destination_center - source_center
        return direction

    def get_coord(location):
        return np.array([location.left, location.top])

    def mouse_center(window_center):
        pyautogui.moveTo(*window_center)

    def mouse_center_click(window_center):
        pyautogui.moveTo(*window_center)
        pyautogui.click(*window_center, clicks=1, interval=1, button='left')

    def locate_image_and_double_click(image_path, region_im=None, region_location=None, region=None, button='left'):
        """
        locate an image and double click it
        default using left click
        """
        image_location = GameInteractionIO.locate_image(image_path, region_im, confidence=0.8, region=region)
        if not image_location:
            return False
        image_coord = GameInteractionIO.get_image_center(image_location)
        if region_location is not None:
            image_coord += region_location.coord()
        pyautogui.click(*image_coord, clicks=2, interval=1, button=button)
        return True
    
    @post_action
    def locate_image_and_click(image_path, region_im=None, region_location=None, confidence=0.8,
                               region=None, button='left', loop=False, timeout=10, delay=1):
        """
        locate an image and double click it
        default using left click
        """
        image_location = GameInteractionIO.locate_image(image_path, region_im, confidence=confidence, region=region)
        if loop is True:
            wait_time = 0
            while not image_location and wait_time < timeout:
                GameInteractionIO.delay(delay)
                image_location = GameInteractionIO.locate_image(image_path, region_im, confidence=confidence, region=region)
                wait_time += 1
        if not image_location:
            return False
        if isinstance(image_location, list):
            image_location = image_location[0]
        image_coord = GameInteractionIO.get_image_center(image_location)
        if region_location is not None:
            image_coord += region_location.coord()
        pyautogui.click(*image_coord, clicks=1, interval=1, button=button)
        return True


    def get_region_location_first_time(region_image_path, window_info):
        """
        based on the given image path, get the relative location of the image in
        the screen w.r.t. the window's center coord 
        """
        region_abs_location = GameInteractionIO.locate_image(region_image_path, confidence=0.9, region=window_info)
        region_offset = GameInteractionIO.get_coord(region_abs_location) - GameInteractionIO.get_image_center(window_info)
        region_offset_location = LocationBox(
            *region_offset,
            *region_abs_location.size())
        return region_offset_location

    def get_region_location(region_location_offset, window_center_coord):
        """
        based on the region's offset location and the window's center coord
        get the region's current active location
        """
        left = region_location_offset.left + window_center_coord[0]
        top = region_location_offset.top + window_center_coord[1]
        return LocationBox(left, top, *region_location_offset.size())

    def get_sub_region_location(sub_region_offset, region_offset, window_center_coord):
        """
        based on subregion's offset to windows center coord reference and the region's offset to window center coord
        get the subregion's offset location relative to the region's location
        """
        sub_region_location_coord = window_center_coord - region_offset.coord() + sub_region_offset.coord()
        sub_region_location = LocationBox(
            *sub_region_location_coord,
            *sub_region_offset.size()
        )
        return sub_region_location
    
    def get_location_image(image_location, region_image=None):
        """
            take a screenshot of the image location screen
            if a region_image is provided, use tha region image as the screen instead
        """
        if region_image is not None:
            location_im = region_image.crop(image_location.to_bounding())
        else:
            location_im = ImageGrab.grab(bbox=image_location.to_bounding())
        return location_im