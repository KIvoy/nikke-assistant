from functools import wraps
import os
import logging
from PIL import Image
import json
import numpy as np

from location_box import LocationBox
from game_interaction_io import GameInteractionIO as gio

for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)
logging.basicConfig(format=' %(asctime)s - %(levelname)s - %(message)s')

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
                        print(e)
                        gio.delay(delay)
                return None
            return wrapper
        return post_action
        
    def __init__(
        self,
        app_name = None,
        profile=None,
        profile_path=None,
        game_settings=None,
        game_settings_path=None
    ):
        # set logging
        self.set_logger()
        
        # load up the profile
        self.load_profile(profile=profile, profile_path=profile_path)
        
        # Load up game settings
        self.load_game_settings(profile=game_settings, profile_path=game_settings_path)
        
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
        self.set_game_settings()
    
    def select_active_window(self, app_name=None):
        self.set_active_window(app_name)
        self.setup_image_profile()
        self.set_game_settings()
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
                    if self.settings['load_to_memory'] is True:
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
    
    def set_parameters(self):
        self.settings['rookie_arena'] = self.get_rookie_arena_settings()
    
    def init_location_map(self):
        self.location_map = {}
        return True
    
    def set_active_window(self, app_name=None):
        """
        set the current active window info
        """
        if not app_name:
            if self.settings.get('active_window'):
                app_name = self.settings.get('active_window')
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
        
        self.settings['active_window'] = app_name
        
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
        self.res_multi = self.resolution[1]/self.default_resolution[1]
        print('succesfully detected app window')
        return True         
        
    
    def load_profile(self, profile=None, profile_path=None):
        """
        load the skill profile for a given agent based on either a skill_path or a skill profile
        if none provided, the profile will be initialized to the default profile from the default skill 
        """
        if not profile_path:
            default_profile_path = 'agent\\default\\default_nikke_profile.json'
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
        self.settings = profile.get('settings', 'unknown settings')
                
        print('Loaded profile {}'.format(self.profile_name))

    def load_game_settings(self, profile=None, profile_path=None):
        """
        load the skill profile for a given agent based on either a skill_path or a skill profile
        if none provided, the profile will be initialized to the default profile from the default skill 
        """
        if not profile_path:
            default_profile_path = 'agent\\default\\game_settings.json'
            current_path = os.getcwd()
            profile_path = os.path.join(current_path, default_profile_path)
        
        if not profile:
            with open(profile_path) as f:
                profile = json.load(f)
        
        setting_type = 'default'
        self.game_settings = profile.get(setting_type)
        print(f'loaded {setting_type} game settings')

    def set_game_settings(self, setting_type='default'):
        # if resolution changed, modify all game related variables that would change with resolution
        settings = self.game_settings
        if self.res_multi != 1:
            m = self.res_multi
            for module, content in self.game_settings.items():
                for s_type, setting in content.items():
                    if s_type == 'var':
                        for k, v in setting.items():
                            setting[k] = round(v*m)
        self.game_settings = settings
        return True
    
    def save_profile(self):
        profile = {}
        profile['name'] = self.profile_name
        profile['desc'] = self.desc
        profile['routine'] = self.routine
        profile['agent_type'] = self.type
        profile['settings'] = self.settings
        
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
        if self.settings['active_window']== self.NIKKE_PC_WINDOW:
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
                                        loop=True, confidence=0.9, timeout=2):
                        nikke_advised[nikke_name]['advised'] = True
                        self.logger.info(f'Nikke {nikke_name} is not available or has already been advised')
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
        
        gio.locate_image_and_click(start_im, region=self.location_map['home'].to_bounding(), loop=True, confidence=0.95)
        gio.locate_image_and_click(self.image_map[f'home_event_start'],
                                   region=self.location_map['home'].to_bounding(), loop=True, confidence=0.95)
        
        event_continue = True
        while event_continue:
            event_continue = gio.locate_image_and_click(self.image_map[f'home_event_restart'],
                                                        region=self.location_map['home'].to_bounding(),
                                                        loop=True, confidence=0.95, timeout=18, delay=10)
            
        self.logger.info(f"repeating event {event_type} end")
        #     
        self.exit_to_home()
    
    
    def rookie_arena_get_enemy_information(self):
        ras = self.game_settings.get('rookie_arena', {}).get('var')
        if not ras:
            self.logger.info('Cannot find settings for rookie arena')
            return None
        enemy_info = {}

        fight_locs = gio.locate_image(self.image_map['home_ark_arena_rookie_free'],
                        region=self.location_map['home'].to_bounding(), confidence=0.8, multi=True)        
        if not fight_locs:
            return False
        
        timeout=3
        if len(fight_locs) < 3:
            for i in range(3):
                fight_locs = gio.locate_image(self.image_map['home_ark_arena_rookie_free'],
                                region=self.location_map['home'].to_bounding(), confidence=0.7, multi=True)            
                gio.delay(1)
                if len(fight_locs) == 3:
                    break
            
        for ind, fight_loc in enumerate(fight_locs):
            enemy_info[ind] = {}
            enemy_info[ind]['fight_loc'] = fight_loc        
        
        rank_locs = gio.locate_image(self.image_map['home_ark_arena_rookie_star'],
                        region=self.location_map['home'].to_bounding(), confidence=0.7, multi=True)
        if rank_locs:
            for ind, rank_loc in enumerate(rank_locs):
                r = rank_loc.stretch(ras['ENEMY_RANK_H_STRETCH'],in_place=True
                                    ).stretch(ras['ENEMY_RANK_V_STRETCH'], axis=1, direction='up'
                                    ).translate(ras['ENEMY_RANK_H_TRANS'],ras['ENEMY_RANK_V_TRANS'])
                r_img = gio.get_location_image(r)
                r_rank = gio.read_number(r_img, l=1)
                enemy_info[ind]['rank'] = r_rank

        power_level_locs = gio.locate_image(self.image_map['home_ark_arena_rookie_enemy_power_level'],
                        region=self.location_map['home'].to_bounding(), confidence=0.7, multi=True)
        
        if power_level_locs:
            for ind, power_level_loc in enumerate(power_level_locs):
                p = power_level_loc.stretch(ras['ENEMY_POWER_H_STRETCH'], in_place=True
                                           ).stretch(ras['ENEMY_POWER_V_STRETCH'], axis=1, direction='up'
                                            ).translate(ras['ENEMY_POWER_H_TRANS'],ras['ENEMY_POWER_V_TRANS'])
                p_img = gio.get_location_image(p)
                p_rank = gio.read_number(p_img, l=0)
                enemy_info[ind]['power_level'] = p_rank   

        return enemy_info

    def rookie_arena_get_self_information(self):
        ras = self.game_settings.get('rookie_arena', {}).get('var')
        if not ras:
            self.logger.info('Cannot find settings for rookie arena')
            return None
        self_info = {}

        rank_loc = gio.locate_image(self.image_map['home_ark_arena_rookie_star_self'],
                        region=self.location_map['home'].to_bounding(), confidence=0.7)
        if rank_loc:
            r = rank_loc.stretch(ras['SELF_RANK_H_STRETCH'], in_place=True
                                ).stretch(ras['SELF_RANK_V_STRETCH'], axis=1, direction='up'
                                         ).translate(ras['SELF_RANK_H_TRANS'],ras['SELF_RANK_V_TRANS'])
            r_img = gio.get_location_image(r)
            r_rank = gio.read_number(r_img, l=0)
            self_info['rank'] = r_rank

        power_level_loc = gio.locate_image(self.image_map['home_ark_arena_rookie_power_level'],
                        region=self.location_map['home'].to_bounding(), confidence=0.7, multi=True)
        
        
        if power_level_loc:
            power_level_loc = power_level_loc[1] if len(power_level_loc)>1 else power_level_loc[0]
            p = power_level_loc.stretch(ras['SELF_POWER_H_STRETCH'], in_place=True
                                       ).stretch(ras['SELF_POWER_V_STRETCH'], axis=1, direction='up'
                                                ).translate(ras['SELF_POWER_H_TRANS'],ras['SELF_POWER_V_TRANS'])
            p_img = gio.get_location_image(p)
            print(p)
            p_rank = gio.read_number(p_img, l=0)
            self_info['power_level'] = p_rank
        return self_info


    def select_opponent(self, self_info, enemy_info, max_power_level_gap=1000):
        optimal_opponent = None
        average_rank = None
        average_power_level = None
        rank_list = [enemy['rank'] for ind, enemy in enemy_info.items() if enemy.get('rank')]
        if len(rank_list) == 3:
            average_rank = np.mean(rank_list)
        power_level_list = [enemy['power_level'] for ind, enemy in enemy_info.items() if enemy.get('power_level')]
        if len(power_level_list) == 3:
            average_power_level = np.mean(power_level_list)

        rank_valid = False
        power_level_valid = False

        if self_info.get('rank') and average_rank and abs(self_info.get('rank') - average_rank)/self_info.get('rank') < 2:
            rank_valid = True
        if self_info.get('power_level') and average_power_level and abs(self_info.get('power_level') - average_power_level)/self_info.get('power_level') < 2:
            power_level_valid = True

        if rank_valid and power_level_valid:
            self.logger.info('Opponent information valid')
            for ind, enemy in enemy_info.items():
                if enemy['power_level'] - self_info['power_level'] > max_power_level_gap:
                    continue
                if not optimal_opponent:
                    optimal_opponent = enemy
                else:
                    if enemy.get('rank') > optimal_opponent.get('rank'):
                        optimal_opponent = enemy
        elif power_level_valid:
            self.logger.warning('Opponent rank information invalid')
            self.logger.warning('Selecting based on power level only')
            for ind, enemy in enemy_info.items():
                if enemy['power_level'] - self_info['power_level'] > max_power_level_gap:
                    continue
                if not optimal_opponent:
                    optimal_opponent = enemy
                else:
                    if enemy.get('power_level') > optimal_opponent.get('power_level'):
                        optimal_opponent = enemy
        else:
            self.logger.warning('Opponent information invalid. Selecting middle opponent')
            optimal_opponent = enemy_info.get(1)

        if optimal_opponent:
            self.logger.info(f"Opponent select with power level {optimal_opponent.get('power_level')} and rank {optimal_opponent.get('rank')}")
        else:
            self.logger.error('unable to detect opponent')
        return optimal_opponent   
    
    
    def rookie_arena(self):
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
            if not enemy_info or not enemy_info[0].get('fight_loc'):
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
        output_list.append('Agent Settings:')
        output_list.append(json.dumps(self.settings, indent=2))
        output_list.append(sep_short)
        output_list.append(sep_long)
        return "\n".join(output_list)     