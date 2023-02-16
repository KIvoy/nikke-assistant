from functools import wraps
from types import GeneratorType
import numpy as np
from easyocr import Reader
import pyautogui
import time
import os
import numpy as np
from PIL import ImageGrab
from easyocr import Reader
from types import GeneratorType

import cv2
import pytesseract

pytesseract.pytesseract.tesseract_cmd=r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
import logging

## Nikke Agent
import json
from PIL import Image
from operator import itemgetter
import keyboard
import pygetwindow as gw


for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
logging.basicConfig(format=' %(asctime)s - %(levelname)s - %(message)s')

profile = {
    "name": "default profile",
    "agent_type": "nikke",
    "desc": "a default template for Nikke helper",
    "setting":{
        "load_to_memory":True,
        "active_window": "BlueStacks Keymap Overlay"
    },
    "routine": {
        "1":{
            "name":"claim_outpost_reward",
            "display_name": "Claim Outpost Reward",
            "frequency": "daily",
            "priority": 2,
            "auto":True,
            "setting":{
            }
        },
        "2":{
            "name":"claim_friend_points",
            "display_name": "Claim Friend Points",
            "priority": 1,
            "frequency": "daily",
            "auto":True,
            "setting":{
            }
        },
        "3":{
            "name":"advise_nikke",
            "display_name": "Advise Nikke",
            "priority": 3,
            "frequency": "daily",
            "auto":True,
            "setting":{
            }
        },
        "4":{
            "name":"event",
            "display_name": "Repeat Event Levels",
            "priority": 4,
            "frequency": "daily",
            "auto":False,
            "setting":{
                "level_to_repeat":"1-11"
            }
        }, 
        "5":{
            "name":"arena_rookie",
            "display_name": "Rookie Arena",
            "priority": 5,
            "frequency": "daily",
            "auto":True,
            "setting":{
                "max_power_gap": 1000
            }
        }
    }
}




import json
from PIL import Image
from operator import itemgetter
import keyboard

class LocationBox:
    def __init__(self, left=0, top=0, width=0, height=0, box=None, _box=None):
        if box:
            left = box.left
            top = box.top
            width = box.width
            height = box.height
        elif _box:
            left = _box._left
            top = _box._top
            width = _box._width
            height = _box._height 
        
        self.left = left
        self.top = top
        self.width = width
        self.height = height

    def to_array(self):
        return [self.left, self.top, self.width, self.height]
    
    def to_bounding(self):
        return [self.left, self.top, self.left+self.width, self.top+self.height]
    
    def translate(self, x, y):
        return LocationBox(self.left+x, self.top+y, self.width, self.height)
    
    def coord(self):
        return np.array([self.left, self.top])
    
    def size(self):
        return np.array([self.width, self.height])    
    
    def stretch(self, value, axis=0, direction="right", in_place=False):
        new_box = LocationBox(box=self)
        if axis==0:
            new_box.width += value
            if direction=="left":
                new_box.left -= value
        elif axis==1:
            new_box.height+=value
            if direction=="up":
                new_box.top-=value
        
        if in_place:
            if axis == 0:
                new_box.width -= self.width
                if direction == "left":
                    new_box.left -= self.width
                elif direction == "right":
                    new_box.left += self.width
            
            elif axis == 1:
                new_box.height -= self.height
                if direction == "up":
                    new_box.top -= self.height
                elif direction == "down":
                    new_box.top += self.height
        
        return new_box
    
    def __repr__(self):
        return f'LocationBox(left={self.left}, top={self.top}, width={self.width}, height={self.height})'
    

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
        stretch_image, digit = stretch_white_space(erode)
        return stretch_image 
    
    
    def read_text(image_name, model_name=None, detail=1, in_line=True):
        if not model_name:
            model_name = GameInteractionIO.reader

        frame = cv2.cvtColor(np.array(image_name), cv2.COLOR_RGB2BGR)
        
        # Read the data
        result = model_name.readtext(frame, detail=detail, paragraph=in_line)
        return result
    
    def read_number(image, l=0):
        if l==0:
            value = pytesseract.image_to_string(image,
                        config='--psm 6 outputbase digits tessedit_char_whitelist=0123456789').strip().replace(" ", "")
        elif l==1:
            image = GameInteractionIO.preprocess_image_number(image)
            value = pytesseract.image_to_string(image,
                        config='--psm 10 outputbase digits tessedit_char_whitelist=0123456789').strip().replace(" ", "")
        
        value = re.sub('[^A-Za-z0-9]+', '\n', value)
        if not value.isdigit():
            return False
        value = int(value)
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
    
    def locate_image(image_path, master_image_path=None, confidence=0.85, region=None, multi=False, multi_threshold=0.3):
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
    
    def exist_image(image_path, master_image_path=None, confidence=0.9, region=None, loop=False, timeout=10):
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
                            gio.delay(1)
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
                        gio.delay(1)
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
    def locate_image_and_click(image_path, region_im=None, region_location=None, confidence=0.9,
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
gio=GameInteractionIO

class Agent:
    def retry_action(timeout=3, delay=3):
        def post_action(function):
            @wraps(function)
            def wrapper(*args, **kwargs):
                attempt = 0
                while attempt < timeout:
                    try:
                        retval = function(*args, **kwargs)
                        return retval
                    except Exception as e:
                        self.logger.error(e)
                        GameInteractionIO.delay(delay)
                return None
            return wrapper
        return post_action
        
    def __init__(
        self,
        app_name = None,
        profile=None,
        profile_path=None,
    ):
        # set logging
        self.set_logger()
        
        # load up the profile
        self.load_profile(profile=profile, profile_path=profile_path)
        
        # set the active window region
        self.initialize_game(app_name)
    
    

    def _sort_dict_by_value(self, unsorted_dict, value):
        """
        helper function to sort a dictionary by the values of it's sub dictionaries
        """
        return {k: v for k, v in sorted(unsorted_dict.items(), key=lambda item: item[1][value])}
        
    
    def set_logger(self):
        self.logger = logging.getLogger('==============NIKKE DEBUGGER=============')
        self.logger.setLevel(logging.DEBUG)
    
    def initialize_game(self, app_name=None):
        # initialize all features
        self.default_resolution = [575, 1022]
        self.default_advise_nikke_stretch_length = 250
        self.image_path = 'images'
        self.NIKKE_PC_WINDOW = 'NIKKE'
        self.NIKKE_PC_SCROLL_CONSTANT = 13
        self.init_location_map()
        self.set_active_window(app_name)
        self.setup_image_profile()
    
    def select_active_window(self, app_name=None):
        self.set_active_window(app_name)
        self.setup_image_profile()
        return True
    
    def resize_image(self, im):
        new_resolution = self.resolution
        if new_resolution != self.default_resolution:
            ratio = new_resolution[1]/self.default_resolution[1]
            im = im.resize((round(s*ratio) for s in im.size))
        return im
    
    def resize_value(self, value):
        new_resolution = self.resolution
        if new_resolution != self.default_resolution:
            ratio = new_resolution[1]/self.resolution[1]
            value = value*ratio
        return value        
    
    def load_image_path(self, image_path):
        image_path_dict = {}    
        
        for root, dirs, files in os.walk(image_path):
            if root[-1] != "\\":
                root = root+"\\"
            sub_dir = root.replace(image_path+'\\', '')
            for file in files:
                if file.endswith('.png') or file.endswith('.PNG'):
                    pretty_name = "_".join(os.path.join(sub_dir, file).split('.')[0].split('\\'))
                    if self.setting['load_to_memory'] is True:
                        image_path_dict[pretty_name] = self.resize_image(Image.open(os.path.join(root, file)))
                    else:
                        image_path_dict[pretty_name] = os.path.join(root, file)
        return image_path_dict
    
    def setup_image_profile(self):
        """
        load the matching images
        """
        current_path = os.getcwd()
        image_dir_name = self.image_path
        agent_dir_name = self.type

        image_path = os.path.join(current_path, image_dir_name, agent_dir_name)
        self.image_map = self.load_image_path(image_path=image_path)
        return True
    
    
    def init_location_map(self):
        self.location_map = {}
        return True
    
    def set_active_window(self, app_name=None):
        """
        set the current active window info
        """
        if not app_name:
            if self.setting.get('active_window'):
                app_name = self.setting.get('active_window')
            else:
                app_name = "BlueStacks Keymap Overlay"
        
        # get all apps open
        app_list = gio.get_available_applications(verbose=True)
        
        # find the selected app by name
        app = [app for app in app_list if app.title==app_name]

        if len(app) == 0:
            self.resolution = self.default_resolution
            self.logger.error('cannot find active game window')
            return False
        app = app[0]
        
        self.setting['active_window'] = app_name
        
        # record the app location
        app_location = LocationBox(_box=app._rect)
        
        if app_name == self.NIKKE_PC_WINDOW:
            self.logger.info('Detected PC version of Nikke')
            title_height = 39
            edge_width = 8

            app_location = app_location.stretch(-title_height,axis=1, direction='down'
                                        ).translate(0,title_height-edge_width
                                        ).stretch(-edge_width*2,axis=0, direction='left'
                                        ).translate(-edge_width,0)
        
        
        self.location_map['home'] = app_location
        
        self.resolution = [app_location.width, app_location.height]
        print('succesfully detected app window')
        return True         
        
    
    def load_profile(self, profile=None, profile_path=None):
        """
        load the skill profile for a given agent based on either a skill_path or a skill profile
        if none provided, the profile will be initialized to the default profile from the default skill 
        """
        if not profile_path:
            default_profile_path = 'agent\\default\\default_skill_profile.json'
            current_path = os.getcwd()
            profile_path = os.path.join(current_path, default_profile_path)
        
        if not profile:
            with open(profile_path) as f:
                profile = json.load(f)
        
        self.profile_path = profile_path
        self.profile_name = profile.get('name', 'unknown name')
        self.desc = profile.get('desc', 'unknown desc')
        self.routine = profile.get('routine', 'unknown routine')
        self.type = profile.get('agent_type', 'unknown type')
        self.setting = profile.get('setting', 'unknown setting')
                
        print('Loaded profile {}'.format(self.profile_name))
    
    def save_profile(self):
        profile = {}
        profile['name'] = self.profile_name
        profile['desc'] = self.desc
        profile['routine'] = self.routine
        profile['agent_type'] = self.type
        profile['setting'] = self.setting
        
        with open(self.profile_path, 'w') as json_file:
            json.dump(profile, json_file, indent=4)
        self.logger.info(f'Succesfully saved profile to {self.profile_path}')
    
    
    def is_home(self):
        pass
    def terminate_action(self):
        raise KeyboardInterrupt
    
    def back(self):
        gio.single_click('esc')
    
    def exit_to_home(self):
        self.logger.info('Exiting to home...')
        potential_actions = [self.image_map['home_outpost_express_reward'],
                             self.image_map['home_outpost_express_confirm'],
                             self.image_map['home_outpost_express_level_up']]
        
        # click on first available action to exit the outpost express claim panel
        if gio.locate_image_and_click(potential_actions,
                                   region=self.location_map['home'].to_bounding(), loop=True, timeout=2):
            return True
        if gio.locate_image_and_click(self.image_map['home_flash_sale'],
                                   region=self.location_map['home'].to_bounding(), loop=True, timeout=2):
             if gio.locate_image_and_click(self.image_map['confirm'],
                                   region=self.location_map['home'].to_bounding(), loop=True, timeout=2):
                    return True
        
        if gio.locate_image_and_click(self.image_map['back_home'],
                           region=self.location_map['home'].to_bounding(), loop=True, timeout=3):
            return True
        else:
            item_list = [self.image_map['home_blabla'],self.image_map['home_friend'],self.image_map['home_union']]
            while gio.exist_image(item_list, region=self.location_map['home'].to_bounding()) is False:
                gio.single_click("esc")
                gio.delay(1)
            return True
    
    def scroll(self, scroll_distance=100, direction='down', delay=2, time=1):
        if self.setting['active_window']== self.NIKKE_PC_WINDOW:
            time = time*self.NIKKE_PC_SCROLL_CONSTANT
            
        direction_multiplier = 1 if direction=='up' else -1
        gio.move_to_image_location(self.location_map['home'])
        for _ in range(time):
            gio.scroll(direction_multiplier*scroll_distance)
        gio.delay(delay)
    
    def claim_outpost_reward_wipe(self):
        """
            try to do outpost wipe
        """
        self.logger.info('Checking if outpost wipe is available')
        wipe_count = 0
        # return to home if not on the page and enter the screen
        if not gio.locate_image(self.image_map['home_outpost_express_wipe'],
                           region=self.location_map['home'].to_bounding()):
            self.exit_to_home()
            gio.locate_image_and_click(self.image_map['home_outpost_express'],
                               region=self.location_map['home'].to_bounding(), confidence=0.8)        
        
        gio.locate_image_and_click(self.image_map['home_outpost_express_wipe'],
                               region=self.location_map['home'].to_bounding(), loop=True, timeout=2)
        # if the wipe is free
        if not gio.locate_image(self.image_map['home_outpost_express_wipe_gem'],
                           region=self.location_map['home'].to_bounding()):
            if gio.locate_image_and_click(self.image_map['home_outpost_express_wipe_wipe'],
                                   region=self.location_map['home'].to_bounding(), loop=True, timeout=2):
                wipe_count += 1
        
        self.logger.info(f'Performed {wipe_count} outpost wipe')    
        self.exit_to_home()
    
    def claim_outpost_reward(self):
        """
            claim the rewards for the outposts
        """
        self.logger.info("claiming outpost reward start")
        
        # click on outpost
        gio.locate_image_and_click(self.image_map['home_outpost_express'],
                           region=self.location_map['home'].to_bounding(), confidence=0.8)
        
        # click on get reward
        gio.locate_image_and_click(self.image_map['home_outpost_express_obtain_reward'],
                                   region=self.location_map['home'].to_bounding(), loop=True)
        
        # different pop ups could happen depending on whether
        # 1. there's reward
        # 2. there's no reward ready
        # 3. there's a level up
        potential_actions = [self.image_map['home_outpost_express_reward'],
                             self.image_map['home_outpost_express_confirm'],
                             self.image_map['home_outpost_express_level_up']]
        
        # click on first available action to exit the outpost express claim panel
        gio.locate_image_and_click(potential_actions,
                                   region=self.location_map['home'].to_bounding(), loop=True)
        
        # try to do outpost wipe if possible
        self.claim_outpost_reward_wipe()

        self.logger.info("claiming outpost reward end successful")
        
        self.exit_to_home()
    
    def claim_friend_points(self):
        """
        claim all existing friendship points
        """
        self.logger.info("claiming friend points start")
        
        # click on friendship icon
        gio.locate_image_and_click(self.image_map['home_friend'],
                                   region=self.location_map['home'].to_bounding())
        
        # wait for the friendlist to refresh
        gio.exist_image(self.image_map['home_friend_send_ready'], region=self.location_map['home'].to_bounding(), loop=True)
        
        # TODO: Might want to make this into a setting
        gio.delay(2) # usually friendship takes sometime to refresh
        
        # if you can still send/receive points, do it and confirm
        if not gio.exist_image(self.image_map['home_friend_send_not_ready'],
                               region=self.location_map['home'].to_bounding(), loop=True, timeout=2):
            gio.locate_image_and_click(self.image_map['home_friend_send'],
                                       region=self.location_map['home'].to_bounding(), loop=True)
            gio.locate_image_and_click(self.image_map['confirm'],
                                       region=self.location_map['home'].to_bounding())

        self.logger.info("claiming friend points end")
        self.exit_to_home()
    
    @retry_action()
    def advise_check_available_session(self):
        ADVISE_AMOUT_TEXT = '咨询次数'
        if not gio.exist_image(self.image_map['home_advise_home'], loop=True, timeout=3):
            self.logger.info('Leaving advising because not in advising UI')
            return None
        im = gio.get_location_image(self.location_map['home'])
        result = gio.read_text(im, detail=0)
        available_advise_session = int([result[ind+1] for ind, s in enumerate(result) if s==ADVISE_AMOUT_TEXT][0].strip()[0])
        return available_advise_session
    
    def advise_nikke_make_choice(self, nikke_name, choice_location):
        # TODO: select choice based on lookup table of actual answers
        # this will require a copy of the answer sheet
        return choice_location[0]
    
    def advise_nikke_single_round(self, nikke_advised={}, nikke_last_round=[]):
        self.logger.info("started a round of advising nikkes")
        end_session = False
        stretch_length = self.resize_value(self.default_advise_nikke_stretch_length)
        stretch_direction = "right"
        nikke_current_round = []

        star_location = gio.locate_image(self.image_map['home_advise_star'],
                                         region=self.location_map['home'].to_bounding(), multi=True)
        if not star_location:
            end_session = True
        else:
            for loc in star_location:
                # check if there's available session
                session_available = self.advise_check_available_session()
                if not session_available or session_available == 0:
                    end_session = True
                    self.logger.info("No more sessions available today")
                    break
                nikke_location = loc.stretch(value=stretch_length, direction=stretch_direction)
                name_im = gio.get_location_image(nikke_location)
                nikke_name = gio.read_text(name_im)[0][-1]
                nikke_current_round.append(nikke_name)
                print(loc)
                print(nikke_location)
                self.logger.info(f"started advising {nikke_name}")
                if nikke_advised.get(nikke_name) is None:
                    nikke_advised[nikke_name] = {}
                    nikke_advised[nikke_name]['location'] = nikke_location
                    nikke_advised[nikke_name]['advised'] = False
                if nikke_advised.get(nikke_name)['advised'] is False:
                    # click on the nikke to advise
                    if not gio.locate_image_and_click(name_im,
                                                    region=self.location_map['home'].to_bounding(), loop=True, confidence=0.99):
                        break
                    # in case rare circumstances would cause the nikke to be already advised
                    # mark it and move to the next nikke
                    if gio.locate_image_and_click(self.image_map['home_advise_advise_unavailable'], region=self.location_map['home'].to_bounding(),
                                        loop=True, timeout=2):
                        nikke_advised[nikke_name]['advised'] = True
                        gio.locate_image_and_click(self.image_map['back'], region=self.location_map['home'].to_bounding(),
                                        loop=True, timeout=2)
                        continue
                    # click on the advise button 
                    if not gio.locate_image_and_click(self.image_map['home_advise_advise'],
                                                    region=self.location_map['home'].to_bounding(), loop=True):
                        break
                    # click on confirm
                    if not gio.locate_image_and_click(self.image_map['confirm'],
                                                    region=self.location_map['home'].to_bounding(), loop=True):
                        break
                    # start the advise session, continue until reaching a decision point
                    while gio.locate_image_and_click(self.image_map['home_advise_continue'],
                                                    region=self.location_map['home'].to_bounding(), loop=True, timeout=3):
                        continue
                    # grab the choices and make one
                    choice_location = gio.locate_image(self.image_map['home_advise_choice'],
                                                    region=self.location_map['home'].to_bounding(), multi=True)
                    current_choice = self.advise_nikke_make_choice(nikke_name=nikke_name, choice_location=choice_location)
                    gio.mouse_left_click(current_choice.coord())

                    # finish the conversation
                    while gio.locate_image_and_click(self.image_map['home_advise_continue'],
                                                    region=self.location_map['home'].to_bounding(), loop=True, timeout=3):
                        continue
                    # back to advise menu
                    
                    # if rank up, confirm
                    gio.locate_image_and_click(self.image_map['home_advise_rank_up_confirm'],
                                                    region=self.location_map['home'].to_bounding(), loop=True, timeout=4)
                        
                    
                    if not gio.locate_image_and_click(self.image_map['back'],
                                                    region=self.location_map['home'].to_bounding(), loop=True):
                        break
                    nikke_advised.get(nikke_name)['advised'] = True

        # scroll down to find new nikkes
        self.scroll()

        # if there hasn't been any changes in Nikke advised
        if set(nikke_last_round) == set(nikke_current_round):
            self.logger.info("No more new nikkes to advise")
            end_session=True
        
        self.logger.info("ended a round of advising nikkes")
        
        return end_session, nikke_advised, nikke_current_round
    
    def advise_nikke(self):
        self.logger.info("advising nikkes start")
        nikke_advised = {}
        nikke_last_round = []
        end_session = False
        if not gio.locate_image_and_click(self.image_map['home_advise'],
                                                  region=self.location_map['home'].to_bounding(), loop=True, timeout=3):
            self.logger.warning("advising nikkes failed because the nikke icon is not found")
            return False
        if not gio.locate_image_and_click(self.image_map['home_advise_home'],
                                                  region=self.location_map['home'].to_bounding(), loop=True, timeout=3):
            self.logger.warning("advising nikkes failed because the advise icon is not found")
            return False
        
        # keep advising nikkes until reaching the stopping condition
        while not end_session:
            end_session, nikke_advised, nikke_last_round = self.advise_nikke_single_round(nikke_advised, nikke_last_round)
        
        self.logger.info("advising nikkes end successful")
        #     
        self.exit_to_home()
    
    def event(self, event_type="valentine_2023", repeat_level="1-11"):
        self.logger.info(f"repeating event {event_type} start")
        # keep advising nikkes until reaching the stopping condition
        end_session = False
        stretch_length = self.resize_value(self.default_event_stretch_length)
        stretch_direction = "right"
        
        # TODO: complete the directions from home to the event repeat page
        

        start_location_found = False
        start_im = None
        level_last_search = []

        # search for the start of the event
        while not start_location_found:
            level_current_search = []        
            level_locations = gio.locate_image(self.image_map[f'home_event_{event_type}_level_icon'],
                                 region=self.location_map['home'].to_bounding(), multi=True)  
            for _loc in level_locations:
                loc = _loc.stretch(value=stretch_length, direction=stretch_direction)
                level_im = gio.get_location_image(loc)
                level_name = gio.read_text(level_im, detail=0)
                level_current_search.append(level_name)
                if level_name == repeat_level:
                    start_location_found = True
                    start_im = level_im
                    break
            
            self.scroll()
            
            # if we are not finding new levels that match the search, return False
            if set(level_last_search) == set(level_current_search) and start_location_found is False:
                self.logger.info(f"Cannot find level {repeat_level}")
                return False
            else:
                level_last_search = level_current_search
        
        gio.locate_image_and_click(start_im, region=agent.location_map['home'].to_bounding(), loop=True, confidence=0.95)
        gio.locate_image_and_click(agent.image_map[f'home_event_start'],
                                   region=agent.location_map['home'].to_bounding(), loop=True, confidence=0.95)
        
        event_continue = True
        while event_continue:
            event_continue = gio.locate_image_and_click(agent.image_map[f'home_event_restart'],
                                                        region=agent.location_map['home'].to_bounding(),
                                                        loop=True, confidence=0.95, timeout=18, delay=10)
            
        self.logger.info(f"repeating event {event_type} end")
        #     
        self.exit_to_home()
    
    
    def rookie_arena_get_enemy_information(self):
        enemy_info = {}
        rank_locs = gio.locate_image(self.image_map['home_ark_arena_rookie_star'],
                        region=self.location_map['home'].to_bounding(), confidence=0.7, multi=True)
        for ind, rank_loc in enumerate(rank_locs):
            r = rank_loc.stretch(40, in_place=True).stretch(5, axis=1, direction='up').translate(0,6)
            r_img = gio.get_location_image(r)
            r_rank = gio.read_number(r_img, l=1)
            enemy_info[ind] = {}
            enemy_info[ind]['rank'] = r_rank

        power_level_locs = gio.locate_image(self.image_map['home_ark_arena_rookie_enemy_power_level'],
                        region=self.location_map['home'].to_bounding(), confidence=0.7, multi=True)

        for ind, power_level_loc in enumerate(power_level_locs):
            p = power_level_loc.stretch(40, in_place=True).stretch(5, axis=1, direction='up').translate(0,5)
            p_img = gio.get_location_image(p)
            p_rank = gio.read_number(p_img, l=0)
            enemy_info[ind]['power_level'] = p_rank   

        fight_locs = gio.locate_image(self.image_map['home_ark_arena_rookie_free'],
                        region=self.location_map['home'].to_bounding(), confidence=0.8, multi=True)        
        if not fight_locs:
            return enemy_info
        
        for ind, fight_loc in enumerate(fight_locs):
            enemy_info[ind]['fight_loc'] = fight_loc

        return enemy_info

    def rookie_arena_get_self_information(self):
        self_info = {}

        rank_loc = gio.locate_image(self.image_map['home_ark_arena_rookie_star_self'],
                        region=self.location_map['home'].to_bounding(), confidence=0.7)
        if rank_loc:
            r = rank_loc.stretch(40, in_place=True).stretch(5, axis=1, direction='up').translate(10,6)
            r_img = gio.get_location_image(r)
            r_rank = gio.read_number(r_img, l=0)
            self_info['rank'] = r_rank

        power_level_loc = gio.locate_image(self.image_map['home_ark_arena_rookie_power_level'],
                        region=self.location_map['home'].to_bounding(), confidence=0.7)

        if power_level_loc:
            p = power_level_loc.stretch(40, in_place=True).stretch(5, axis=1, direction='up').translate(0,5)
            p_img = gio.get_location_image(p)
            p_rank_text = gio.read_text(p_img, detail=0)[0]
            if p_rank_text.isdigit():
                p_rank = int(p_rank_text)
                self_info['power_level'] = p_rank
        return self_info


    def select_opponent(self, self_info, enemy_info, max_power_level_gap=1000):
        optimal_opponent = None
        for ind, enemy in enemy_info.items():
            # don't fight enemy with greater power level
            power_gap = enemy.get('power_level') - self_info.get('power_level')
            if power_gap >= max_power_level_gap:
                continue
            if not optimal_opponent:
                print(optimal_opponent)
                optimal_opponent = enemy
                # if difference > 2x self rank, rank should not be considered
                if optimal_opponent.get('rank') and self_info.get('rank'):
                    diff = optimal_opponent['rank'] - self_info['rank']
                    if abs(diff) / self_info['rank'] > 2:
                        optimal_opponent['rank'] = False
            else:
                # if enemy and self both have rank, only valid if diff is less than 2x
                if enemy.get('rank') and self_info.get('rank'):
                    diff = enemy['rank'] - self_info['rank']
                    if diff / self_info['rank'] > 2:
                        enemy['rank'] = False
                # if enemy has no rank, it would be implied to be optimal with a greater power level
                if not enemy.get('rank') and (enemy['power_level'] > optimal_opponent['power_level']):
                    optimal_opponent = enemy
                # if enemy has rank, you would want it if it's greater than the current optimal opponent
                elif enemy.get('rank') and optimal_opponent.get('rank') and (enemy.get('rank') > optimal_opponent.get('rank')):
                    optimal_opponent = enemy

        return optimal_opponent    
    
    
    def arena_rookie(self):
        self.logger.info("rookie arena run start")
        
        if not gio.locate_image_and_click(self.image_map['home_ark'],
                                                  region=self.location_map['home'].to_bounding(), loop=True, timeout=3):
            self.logger.warning("rookie arena run failed because the ark icon is not found")
            return False
        gio.delay(2)
        if not gio.locate_image_and_click(self.image_map['home_ark_arena'],
                                                  region=self.location_map['home'].to_bounding(), loop=True, timeout=3):
            self.logger.warning("rookie arena run failed because the arena icon is not found")
            return False
        gio.delay(2)
        if not gio.locate_image_and_click(self.image_map['home_ark_arena_rookie'],
                                                  region=self.location_map['home'].to_bounding(), loop=True, timeout=3):
            self.logger.warning("rookie arena run failed because the rookie area icon is not found")
            return False
        gio.delay(2)
        free_arena_available = True
        
        while free_arena_available:
            # retrieve arena information
            self.logger.info('Retrieving rookie arena information')
            self_info = self.rookie_arena_get_self_information()
            enemy_info = self.rookie_arena_get_enemy_information()
            
            # if no free fight, leave
            if not enemy_info[0].get('fight_loc'):
                self.logger.info('No more free battle available')
                break
                
            # select opponent based on information    
            self.logger.info('Selected opponent')
            optimal_opponent = self.select_opponent(self_info, enemy_info, max_power_level_gap=1000)
            
            gio.locate_image_and_click(self.image_map['home_ark_arena_rookie_free'],
                                                  region=optimal_opponent['fight_loc'].to_bounding(), loop=True, timeout=3)
            
            # start fight
            if gio.locate_image_and_click(self.image_map['home_ark_arena_rookie_fight'],
                                                  region=self.location_map['home'].to_bounding(), loop=True, timeout=3):
                self.logger.info('Battle session started')
            
            # wait for arena to load
            gio.delay(3)
            
            # wait for fight to finish
            while not self.rookie_arena_get_self_information():
                if not gio.locate_image_and_click(self.image_map['home_ark_arena_rookie_arena_end'],
                                                      region=self.location_map['home'].to_bounding(), loop=True, timeout=3):
                    self.logger.info('Waiting for battle session to finish')
                else:
                    self.logger.info('Battle session ended')
                
                gio.delay(5)
      
            
        self.logger.info("rookie arena run end")  
        self.exit_to_home()        
        
        
    
    def arena_claim_special_arena_points(self):
        pass
    
    def auto_daily(self):
        self.logger.info(f'starting daily')
        self.logger.info(f'{len([r for k, r in self.routine.items() if (r.get("auto") is True and r.get("frequency") == "daily") ])} dailies to run')
        prioritized_routine = self._sort_dict_by_value(self.routine, "priority")
        for key, r in prioritized_routine.items():
            if r.get("auto") is True and r.get("frequency") == "daily":
                func = getattr(self, r.get("name"))
                self.logger.info(f'running daily {r.get("name")}')
                func()
    
    def test(self):
        return locals()
    
    def __repr__(self):
        output_list = []
        sep_long = "".join(["*" for i in range(40)])
        sep_short = " ".join(["*" for i in range(3)])
        output_list.append(sep_long)
        output_list.append('Agent Profile')
        output_list.append(sep_long)
        output_list.append('Agent Profile Name :{}'.format(self.profile_name))
        output_list.append(sep_short)
        output_list.append('Agent Description: {}'.format(self.desc))
        output_list.append(sep_short)
        output_list.append('Agent Type: {}'.format(self.type))
        output_list.append(sep_short)
        output_list.append('Agent Routine:')
        output_list.append(json.dumps(self.routine, indent=2))
        output_list.append(sep_short)
        output_list.append('Agent Setting:')
        output_list.append(json.dumps(self.setting, indent=2))
        output_list.append(sep_short)
        output_list.append(sep_long)
        return "\n".join(output_list)            


if __name__ == "__main__":
    import admin
    if not admin.isUserAdmin():
        admin.runAsAdmin()
    agent = Agent(app_name="NIKKE", profile=profile)
    # app_list = gw.getWindowsAt(*gio.get_image_center(agent.location_map['home']))
    # app = [app for app in app_list if app.title == agent.NIKKE_PC_WINDOW][0]
    # app.activate()

    gio.locate_image_and_click(agent.image_map['home_outpost_express'],
                            region=agent.location_map['home'].to_bounding(), confidence=0.8)