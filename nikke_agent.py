from functools import wraps
import os
import logging
from PIL import Image
import json
import numpy as np

from location_box import LocationBox
from game_interaction_io import GameInteractionIO as gio


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
        app_name=None,
        profile=None,
        profile_path=None,
        game_settings=None,
        game_settings_path=None,
        custom_logger=None
    ):
        # set logging
        self.set_logger(custom_logger)

        # load up the profile
        self.load_profile(profile=profile, profile_path=profile_path)

        # Load up game settings
        self.load_game_settings(profile=game_settings,
                                profile_path=game_settings_path)

        # set the active window region
        self.initialize_game(app_name)

    def _sort_dict_by_value(self, unsorted_dict, value):
        """
        helper function to sort a dictionary by the values of it's sub dictionaries
        """
        return {k: v for k, v in sorted(unsorted_dict.items(), key=lambda item: item[1][value])}

    def set_logger(self, custom_logger=None):
        if not custom_logger:
            for handler in logging.root.handlers[:]:
                logging.root.removeHandler(handler)
            logging.basicConfig(
                format=' %(asctime)s - %(levelname)s - %(message)s')
            self.logger = logging.getLogger(
                '==============NIKKE DEBUGGER=============')
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger = custom_logger

    def initialize_game(self, app_name=None):
        # initialize all features
        self.default_resolution = [575, 1022]
        self.default_real_resolution = [591, 1061]
        self.default_advise_nikke_stretch_length = 250
        self.image_path = 'images'
        self.NIKKE_PC_WINDOW = 'NIKKE'
        self.NIKKE_PC_SCROLL_CONSTANT = 13
        self.init_location_map()
        self.set_active_window(app_name)
        self.set_game_settings()
        if self.settings.get('auto_rescale'):
            self.resize_to_optimal()
            self.set_active_window(app_name)
        self.setup_image_profile()
        return True

    def select_active_window(self, app_name=None):
        if not app_name:
            app_name = self.settings.get('active_window')
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
                    pretty_name = "_".join(os.path.join(
                        sub_dir, file).split('.')[0].split('\\'))
                    if self.settings['load_to_memory'] is True:
                        image_path_dict[pretty_name] = self.resize_image(
                            Image.open(os.path.join(root, file)))
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
                app_name = "NIKKE"

        # get all apps open
        app_list = gio.get_available_applications(verbose=True)

        # find the selected app by name
        app = [app for app in app_list if app.title == app_name]

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

            app_location = app_location.stretch(-title_height, axis=1, direction='down'
                                                ).translate(0, title_height-edge_width
                                                            ).stretch(-edge_width*2, axis=0, direction='left'
                                                                      ).translate(-edge_width, 0)

        self.location_map['home'] = app_location

        self.resolution = [app_location.width, app_location.height]
        self.res_multi = self.resolution[1]/self.default_resolution[1]
        self.logger.info('succesfully detected app window')
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

        self.logger.info('Loaded profile {}'.format(self.profile_name))

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
        self.logger.info(f'loaded {setting_type} game settings')

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

    def focus(self):
        return gio.switch_active_application(app_name=self.settings['active_window'], app_loc=self.location_map['home'])

    def resize(self, resolution=None):
        if not resolution:
            resolution = self.default_real_resolution
        gio.resize_application(app_name=self.settings['active_window'],
                               app_loc=self.location_map['home'],
                               size=resolution)
        self.select_active_window()
        return True

    def resize_to_optimal(self):
        self.resize(resolution=self.default_real_resolution)

    def is_home(self):
        pass

    def terminate_action(self):
        raise KeyboardInterrupt

    def back(self):
        gio.single_click('esc')
        gio.delay(1)

    def exit_to_home(self):
        self.logger.info('Exiting to home...')
        potential_actions = [self.image_map['home_outpost_express_reward'],
                             self.image_map['home_outpost_express_confirm'],
                             self.image_map['home_outpost_express_level_up']]

        # click on first available action to exit the outpost express claim panel
        gio.locate_image_and_click(potential_actions,
                                   region=self.location_map['home'].to_bounding(), loop=True, timeout=2)

        if gio.locate_image_and_click(self.image_map['home_flash_sale'],
                                      region=self.location_map['home'].to_bounding(), loop=True, timeout=2):
            gio.locate_image_and_click(self.image_map['confirm'],
                                       region=self.location_map['home'].to_bounding(), loop=True, timeout=2)

        gio.locate_image_and_click(self.image_map['back_home'],
                                   region=self.location_map['home'].to_bounding(), loop=True, timeout=3)

        item_list = [self.image_map['home_blabla'],
                     self.image_map['home_friend'], self.image_map['home_union']]
        self.focus()
        while gio.exist_image(item_list, region=self.location_map['home'].to_bounding()) is False:
            self.back()
        self.logger.info('Exited to home succesfully')
        return True

    def scroll(self, scroll_distance=100, direction='down', delay=2, time=1):
        if self.settings['active_window'] == self.NIKKE_PC_WINDOW:
            time = time*self.NIKKE_PC_SCROLL_CONSTANT

        direction_multiplier = 1 if direction == 'up' else -1
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
        gio.exist_image(self.image_map['home_friend_send_ready'],
                        region=self.location_map['home'].to_bounding(), loop=True)

        # TODO: Might want to make this into a setting
        gio.delay(2)  # usually friendship takes sometime to refresh

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
        ADVISE_AMOUNT_TEXT_1 = '咨询次数'
        ADVISE_AMOUNT_TEXT_2 = '追踪妮姬'
        available_advise_session = 0
        if not gio.exist_image(self.image_map['home_advise_home'], loop=True, timeout=3):
            self.logger.info('Leaving advising because not in advising UI')
            return None
        im = gio.get_location_image(self.location_map['home'])
        result = gio.read_text(im, detail=0)
        if result:
            for ind, s in enumerate(result):
                if s == ADVISE_AMOUNT_TEXT_1:
                    available_advise_session = int(result[ind+1][0].strip()[0])
                elif s == ADVISE_AMOUNT_TEXT_2:
                    available_advise_session = int(result[ind-1][0].strip()[0])

        return available_advise_session

    def advise_nikke_make_choice(self, nikke_name, choice_location):
        # TODO: select choice based on lookup table of actual answers
        # this will require a copy of the answer sheet
        return choice_location[0]

    def advise_nikke_single_round(self, nikke_advised={}, nikke_last_round=[]):
        self.logger.info("started a round of advising nikkes")
        end_session = False
        stretch_length = self.resize_value(
            self.default_advise_nikke_stretch_length)
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
                nikke_location = loc.stretch(
                    value=stretch_length, direction=stretch_direction)
                name_im = gio.get_location_image(nikke_location)
                name_raw = gio.read_text(name_im)[0]
                if name_raw:
                    nikke_name = name_raw[-1]
                else:
                    nikke_name = f'Unknown Nikke at location ({nikke_location.left}, {nikke_location.top})'

                nikke_current_round.append(nikke_name)
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
                        self.logger.info(
                            f'Nikke {nikke_name} is not available or has already been advised')
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
                                                     region=self.location_map['home'].to_bounding(), confidence=0.7, loop=True, timeout=3):
                        continue
                    # grab the choices and make one
                    choice_location = gio.locate_image(self.image_map['home_advise_choice'],
                                                       region=self.location_map['home'].to_bounding(), multi=True)
                    current_choice = self.advise_nikke_make_choice(
                        nikke_name=nikke_name, choice_location=choice_location)
                    gio.mouse_left_click(current_choice.coord())

                    # finish the conversation
                    while gio.locate_image_and_click(self.image_map['home_advise_continue'],
                                                     region=self.location_map['home'].to_bounding(), confidence=0.7, loop=True, timeout=3):
                        continue
                    # back to advise menu

                    # if rank up, confirm
                    gio.locate_image_and_click(self.image_map['home_advise_rank_up_confirm'],
                                               region=self.location_map['home'].to_bounding(), loop=True, timeout=4)

                    if not gio.locate_image_and_click(self.image_map['back'],
                                                      region=self.location_map['home'].to_bounding(), loop=True):
                        break
                    nikke_advised.get(nikke_name)['advised'] = True

        # if there hasn't been any changes in Nikke advised
        if nikke_last_round == nikke_current_round:
            self.logger.info("No more new nikkes to advise")
            end_session = True

        self.logger.info("ended a round of advising nikkes")

        return end_session, nikke_advised, nikke_current_round

    def conversation_choice(self, choice_location, choice_information=None, decision_func=None):
        """
            make a decision choice based on the information and decision function
            if no decision function presented, always return the first choice location available
        """
        final_choice_loc = None
        if not decision_func:
            final_choice_loc = choice_location[0]
        return final_choice_loc

    def conversation(self):
        self.logger.info('checking to start a conversation...')
        in_progress = True
        while in_progress:
            in_progress = gio.locate_image_and_click(self.image_map['home_advise_continue'],
                                                     region=self.location_map['home'].to_bounding(), confidence=0.7, loop=True, timeout=3)
            if not in_progress:
                # grab the choices and make one
                choice_location = gio.locate_image(self.image_map['home_advise_choice'],
                                                   region=self.location_map['home'].to_bounding(), multi=True)
                if choice_location:
                    in_progress = True
                else:
                    break
                current_choice = self.conversation_choice(
                    choice_location=choice_location)
                gio.mouse_left_click(current_choice.coord())
        self.logger.info('conversation ended.')
        return True

    def advise_nikke(self):
        self.logger.info("advising nikkes start")
        nikke_advised = {}
        nikke_last_round = []
        end_session = False
        if not gio.locate_image_and_click(self.image_map['home_advise'],
                                          region=self.location_map['home'].to_bounding(), loop=True, timeout=3):

            self.logger.warning(
                "advise option now found, returning home to try again")
            self.exit_to_home()
            if not gio.locate_image_and_click(self.image_map['home_advise'],
                                              region=self.location_map['home'].to_bounding(), loop=True, timeout=3):
                self.logger.warning(
                    "advising nikkes failed because the nikke icon is not found")
                return False

        if not gio.locate_image_and_click(self.image_map['home_advise_home'],
                                          region=self.location_map['home'].to_bounding(), loop=True, timeout=3):
            self.logger.warning(
                "advising nikkes failed because the advise icon is not found")
            return False

        # keep advising nikkes until reaching the stopping condition
        while not end_session:
            end_session, nikke_advised, nikke_current_round = self.advise_nikke_single_round(
                nikke_advised, nikke_last_round)
            if nikke_last_round == nikke_current_round:
                self.scroll()
                end_session, nikke_advised, nikke_current_round = self.advise_nikke_single_round(
                    nikke_advised, nikke_last_round)
            nikke_last_round = nikke_current_round

        self.logger.info("advising nikkes end successful")
        #
        self.exit_to_home()

    def event(self, event_type="valentine_2023", repeat_level="1-11"):
        """
        deprecated old event system
        """
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
                loc = _loc.stretch(value=stretch_length,
                                   direction=stretch_direction)
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

        gio.locate_image_and_click(
            start_im, region=self.location_map['home'].to_bounding(), loop=True, confidence=0.95)
        gio.locate_image_and_click(self.image_map[f'home_event_start'],
                                   region=self.location_map['home'].to_bounding(), loop=True, confidence=0.95)

        event_continue = True
        while event_continue:
            event_continue = gio.locate_image_and_click(self.image_map[f'home_event_restart'],
                                                        region=self.location_map['home'].to_bounding(
            ),
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

        timeout = 3
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
                r = rank_loc.stretch(ras['ENEMY_RANK_H_STRETCH'], in_place=True
                                     ).stretch(ras['ENEMY_RANK_V_STRETCH'], axis=1, direction='up'
                                               ).translate(ras['ENEMY_RANK_H_TRANS'], ras['ENEMY_RANK_V_TRANS'])
                r_img = gio.get_location_image(r)
                r_rank = gio.read_number(r_img, l=1)
                enemy_info[ind]['rank'] = r_rank

        power_level_locs = gio.locate_image(self.image_map['home_ark_arena_rookie_enemy_power_level'],
                                            region=self.location_map['home'].to_bounding(), confidence=0.7, multi=True)

        if power_level_locs:
            for ind, power_level_loc in enumerate(power_level_locs):
                p = power_level_loc.stretch(ras['ENEMY_POWER_H_STRETCH'], in_place=True
                                            ).stretch(ras['ENEMY_POWER_V_STRETCH'], axis=1, direction='up'
                                                      ).translate(ras['ENEMY_POWER_H_TRANS'], ras['ENEMY_POWER_V_TRANS'])
                p_img = gio.get_location_image(p)
                p_rank = gio.read_number(p_img, l=1)
                enemy_info[ind]['power_level'] = p_rank

        return enemy_info

    def rookie_arena_get_self_information(self):
        ras = self.game_settings.get('rookie_arena', {}).get('var')
        if not ras:
            self.logger.info('Cannot find settings for rookie arena')
            return None

        if not gio.locate_image(self.image_map['home_ark_arena_rookie_home'],
                                region=self.location_map['home'].to_bounding(), confidence=0.8):
            self.logger.info('Not at rookie arena home')
            return None

        self_info = {}

        rank_loc = gio.locate_image(self.image_map['home_ark_arena_rookie_star_self'],
                                    region=self.location_map['home'].to_bounding(), confidence=0.7)
        if rank_loc:
            r = rank_loc.stretch(ras['SELF_RANK_H_STRETCH'], in_place=True
                                 ).stretch(ras['SELF_RANK_V_STRETCH'], axis=1, direction='up'
                                           ).translate(ras['SELF_RANK_H_TRANS'], ras['SELF_RANK_V_TRANS'])
            r_img = gio.get_location_image(r)
            r_rank = gio.read_number(r_img, l=1)
            self_info['rank'] = r_rank

        power_level_loc = gio.locate_image(self.image_map['home_ark_arena_rookie_power_level'],
                                           region=self.location_map['home'].to_bounding(), confidence=0.7, multi=True)

        if power_level_loc:
            power_level_loc = power_level_loc[1] if len(
                power_level_loc) > 1 else power_level_loc[0]
            p = power_level_loc.stretch(ras['SELF_POWER_H_STRETCH'], in_place=True
                                        ).stretch(ras['SELF_POWER_V_STRETCH'], axis=1, direction='up'
                                                  ).translate(ras['SELF_POWER_H_TRANS'], ras['SELF_POWER_V_TRANS'])
            p_img = gio.get_location_image(p)
            p_rank = gio.read_number(p_img, l=1)
            self_info['power_level'] = p_rank
        return self_info

    def select_opponent(self, self_info, enemy_info, max_power_level_gap=1000):
        self.logger.info('Selecting opponent...')
        self.logger.debug('My information')
        self.logger.debug(self_info)
        self.logger.debug('Opponent information')
        self.logger.debug(enemy_info)
        optimal_opponent = None
        average_rank = None
        average_power_level = None
        rank_list = [enemy['rank']
                     for ind, enemy in enemy_info.items() if enemy.get('rank')]
        if len(rank_list) == 3:
            average_rank = np.mean(rank_list)
        power_level_list = [enemy['power_level'] for ind,
                            enemy in enemy_info.items() if enemy.get('power_level')]
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
            self.logger.warning(
                'Opponent information invalid. Selecting middle opponent')
            optimal_opponent = enemy_info.get(1)

        if optimal_opponent:
            self.logger.info(
                f"Opponent select with power level {optimal_opponent.get('power_level')} and rank {optimal_opponent.get('rank')}")
        else:
            self.logger.error('unable to detect opponent')
        return optimal_opponent

    def rookie_arena_single_session(self):
        self.logger.info('Retrieving rookie arena information')
        self_info = self.rookie_arena_get_self_information()
        enemy_info = self.rookie_arena_get_enemy_information()

        timeout = 2
        wait_time = 0
        # if no free fight, leave
        while not enemy_info or not enemy_info[0].get('fight_loc'):
            if wait_time > timeout:
                self.logger.info('No more free battle available')
                return False
            gio.delay(1)
            self.logger.info('Seems like no more free battles. Retrying...')
            enemy_info = self.rookie_arena_get_enemy_information()
            wait_time += 1

        # select opponent based on information
        self.logger.info('Selected opponent')
        optimal_opponent = self.select_opponent(
            self_info, enemy_info, max_power_level_gap=1000)

        gio.locate_image_and_click(self.image_map['home_ark_arena_rookie_free'],
                                   region=optimal_opponent['fight_loc'].to_bounding(), loop=True, timeout=3)

        # start fight
        if gio.locate_image_and_click(self.image_map['home_ark_arena_rookie_fight'],
                                      region=self.location_map['home'].to_bounding(), loop=True):
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
        return True

    def rookie_arena(self):
        self.logger.info("rookie arena run start")

        if not gio.locate_image_and_click(self.image_map['home_ark'],
                                          region=self.location_map['home'].to_bounding(), loop=True, timeout=3):
            self.logger.warning(
                "rookie arena ark icon is not found, retrying at home...")
            self.exit_to_home()
            if not gio.locate_image_and_click(self.image_map['home_ark'],
                                              region=self.location_map['home'].to_bounding(), loop=True, timeout=3):
                self.logger.warning(
                    "rookie arena run failed because the ark icon is not found")
                return False
        gio.delay(2)
        if not gio.locate_image_and_click(self.image_map['home_ark_arena'],
                                          region=self.location_map['home'].to_bounding(), loop=True, timeout=3):
            self.logger.warning(
                "rookie arena run failed because the arena icon is not found")
            return False
        gio.delay(2)
        if not gio.locate_image_and_click(self.image_map['home_ark_arena_rookie'],
                                          region=self.location_map['home'].to_bounding(), loop=True, timeout=3):
            self.logger.warning(
                "rookie arena run failed because the rookie area icon is not found")
            return False
        gio.delay(2)
        free_arena_available = True

        while free_arena_available:
            # retrieve arena information
            free_arena_available = self.rookie_arena_single_session()

        self.logger.info("rookie arena run end")
        self.exit_to_home()

    def arena_claim_special_arena_points(self):
        pass

    def normal_shop_refresh(self, free=True):
        """
        try to refresh a normal shop
        """
        self.logger.info('Tryin to refresh normal shop')
        if not gio.locate_image_and_click(self.image_map['home_shop_refresh'],
                                          region=self.location_map['home'].to_bounding(
        ),
                loop=True, timeout=3):
            self.logger.info('Could not find refresh button')
            return False
        if free:
            if not gio.locate_image_and_click(self.image_map['home_shop_cost_0'],
                                              region=self.location_map['home'].to_bounding(
            ),
                    confidence=0.95, loop=True, timeout=3):
                gio.locate_image_and_click(self.image_map['cancel'],
                                           region=self.location_map['home'].to_bounding(
                ),
                    loop=True, timeout=3)
                self.logger.info('The refresh is not free')
                return False
        if not gio.locate_image_and_click(self.image_map['confirm'],
                                          region=self.location_map['home'].to_bounding(
        ),
                loop=True, timeout=3):
            gio.locate_image_and_click(self.image_map['cancel'],
                                       region=self.location_map['home'].to_bounding(
            ),
                loop=True, timeout=3)
            self.logger.info('Could not refresh the normal shop')
            return False

        return True

    def normal_shop_buy_item(self, free=True):
        if free:
            if not gio.locate_image_and_click(self.image_map['home_shop_sale_100'],
                                              region=self.location_map['home'].to_bounding(
            ),
                    confidence=0.95, loop=True, timeout=3):
                self.logger.info('Cannot find free item')
                return False
            if not gio.locate_image_and_click(self.image_map['home_shop_buy_100'],
                                              region=self.location_map['home'].to_bounding(
            ),
                    confidence=0.95, loop=True, timeout=3):
                self.logger.info('Item to purchase does not seem to be free')
                gio.locate_image_and_click(self.image_map['cancel'],
                                           region=self.location_map['home'].to_bounding(
                ),
                    loop=True, timeout=3)
                return False
            if not gio.locate_image_and_click(self.image_map['confirm'], region=self.location_map['home'].to_bounding()):
                self.logger.info('Cannot find confirmation to purchase')
                gio.locate_image_and_click(self.image_map['cancel'],
                                           region=self.location_map['home'].to_bounding(
                ),
                    loop=True, timeout=3)
                return False
            if not gio.locate_image_and_click(self.image_map['reward'], region=self.location_map['home'].to_bounding(),
                                              loop=True, timeout=3):
                self.logger.info('Could not claim reward')
                return False
            gio.delay(1)
        return True

    def normal_shop(self):
        """
        A daily shopping session to buy free material at the shop
        Refreshes for free if no free material
        Stops if no more free materials
        """
        self.logger.info('Normal shop session started...')

        # if no shop starting point available exit home
        if not gio.locate_image_and_click(self.image_map['home_shop'], region=self.location_map['home'].to_bounding()):
            self.logger.info(
                'Could not find shop entrance, exiting home to restart')
            self.exit_to_home()
            # if still no shop detected, return false
            if not gio.locate_image_and_click(self.image_map['home_shop'], region=self.location_map['home'].to_bounding()):
                self.logger.info('Could not find shop entrance, session ended')
                return False

        shop_session = True
        item_available = False
        items_shopped = 0
        while shop_session:
            item_available = self.normal_shop_buy_item()
            if not item_available:
                shop_session = self.normal_shop_refresh()
            else:
                items_shopped += 1
                self.logger.info('Bought one item for free')

        self.logger.info(
            f'Shopping session ended. Bought in total of {items_shopped} items.')
        self.exit_to_home()

    def claim_nikke_rehab_reward_single_session(self):
        self.logger.info('Started single round of rehab reward claiming...')
        if not gio.locate_image_and_click(self.image_map['home_outpost_elevator_rehab_home'],
                                          region=self.location_map['home'].to_bounding(
        ),
                loop=True, timeout=20, button=None):
            self.logger.info('Could not reach rehab home')
            return False

        r_reward_loc = gio.locate_image(self.image_map['home_outpost_elevator_rehab_complete_r'],
                                        region=self.location_map['home'].to_bounding(), multi=True)
        sr_reward_loc = gio.locate_image(self.image_map['home_outpost_elevator_rehab_complete_sr'],
                                         region=self.location_map['home'].to_bounding(), multi=True)
        ssr_reward_loc = gio.locate_image(self.image_map['home_outpost_elevator_rehab_complete_ssr'],
                                          region=self.location_map['home'].to_bounding(), multi=True)

        r_reward_loc = r_reward_loc if r_reward_loc is not None else []
        sr_reward_loc = sr_reward_loc if sr_reward_loc is not None else []
        ssr_reward_loc = ssr_reward_loc if ssr_reward_loc is not None else []

        expected_reward_count = 3
        total_reward_count = len(r_reward_loc) + \
            len(sr_reward_loc) + len(ssr_reward_loc)

        for r_loc in r_reward_loc:
            gio.mouse_left_click(r_loc.coord())
            self.conversation()
        for r_loc in sr_reward_loc:
            gio.mouse_left_click(r_loc.coord())
            self.conversation()
        for r_loc in ssr_reward_loc:
            gio.mouse_left_click(r_loc.coord())
            self.conversation()

        if total_reward_count < expected_reward_count:
            self.logger.info(
                f'there are {expected_reward_count - total_reward_count} rewards that needs manual intervention to claim')
        elif total_reward_count > expected_reward_count:
            self.logger.warning(
                f'there are unexpected amount of {total_reward_count} when the maximum expected reward count is {expected_reward_count}')

        self.logger.info(
            f'Successfully claimed {total_reward_count} rehab rewards')

        return total_reward_count

    def claim_nikke_rehab_reward(self):
        self.logger.info('Claiming rehab reward session started...')

        # if no shop starting point available exit home
        if not gio.locate_image_and_click(self.image_map['home_outpost'],
                                          region=self.location_map['home'].to_bounding(
        ),
                loop=True, timeout=3):
            self.logger.info(
                'Could not find rehab entrance, exiting home to restart')
            self.exit_to_home()
            # if still no shop detected, return false
            if not gio.locate_image_and_click(self.image_map['home_outpost'],
                                              region=self.location_map['home'].to_bounding(
            ),
                    loop=True):
                self.logger.info(
                    'Could not find rehab entrance, session ended')
                return False

        if not gio.locate_image_and_click(self.image_map['home_outpost_elevator'],
                                          region=self.location_map['home'].to_bounding(
        ),
                loop=True):
            self.logger.info('Could not find elevator entrance')
            return False

        if not gio.locate_image_and_click(self.image_map['home_outpost_elevator_enter'],
                                          region=self.location_map['home'].to_bounding(
        ),
                loop=True):
            self.logger.info('Could enter elevator')
            return False

        reward_count = self.claim_nikke_rehab_reward_single_session()

        self.logger.info(f'Rehab reward claiming ended.')
        self.exit_to_home()

    def get_valid_buff_location(self, buff_loc_list):
        valid_buff_loc = []
        for buff_loc in buff_loc_list:
            if not gio.exist_image(self.image_map['home_ark_simulation_room_buff_unavailable_buff_home'],
                                   region=buff_loc.to_bounding(), confidence=0.8):
                valid_buff_loc.append(buff_loc)
        return valid_buff_loc

    def get_buff_location(self):
        buff_rarity = ['r', 'sr', 'ssr', 'epic']
        buff_size = ['s', 'm', 'l']
        buff_loc_list = []
        for rarity in buff_rarity:
            for size in buff_size:
                buff_im = self.image_map.get(
                    f'home_ark_simulation_room_buff_rarity_{rarity}_{size}')
                if buff_im:
                    buff_locs = gio.locate_image(buff_im,
                                                 region=self.location_map['home'].to_bounding(), confidence=0.9, multi=True)
                    if buff_locs:
                        buff_loc_list.extend(buff_locs)
        buff_loc_list = gio.non_maximum_suppresion(
            buff_loc_list, threshold=0.1)
        buff_loc_list = [buff_loc.stretch(440) for buff_loc in buff_loc_list]
        buff_loc_list = self.get_valid_buff_location(buff_loc_list)
        return buff_loc_list

    def simulation_room_select_buff_simple(self, buff_locs):
        buff_info = {}
        buff_selected = None
        buff_types = ["boss", "choice", "heal", "normal", "upgrade"]
        buff_subtypes = ["attack", "survival", "strategic",
                         "circle", "square", "diamond", "triangle", "mixed"]
        for ind, buff_loc in enumerate(buff_locs):
            info = {}
            info['loc'] = buff_loc
            buff_im = gio.get_location_image(buff_loc)
            buff_types = ["boss", "choice", "heal", "normal", "upgrade"]
            for buff_type in buff_types:
                is_buff_type = gio.exist_image(self.image_map[f'home_ark_simulation_room_buff_type_{buff_type}'],
                                               master_image_path=buff_im)
                if is_buff_type:
                    info['buff_type'] = buff_type
                    break
            for buff_subtype in buff_subtypes:
                is_buff_subtype = gio.exist_image(self.image_map[f'home_ark_simulation_room_buff_subtype_{buff_subtype}'],
                                                  master_image_path=buff_im)
                if is_buff_subtype:
                    info['buff_subtype'] = buff_subtype
                    break
            buff_info[ind] = info

        buff_types_info = [info['buff_type']
                           for ind, info in buff_info.items()]
        if 'boss' in buff_types_info:
            ind = buff_types_info.index('boss')
            buff_selected = buff_info[ind]
        elif 'upgrade' in buff_types_info:
            ind = buff_types_info.index('upgrade')
            buff_selected = buff_info[ind]
        elif 'heal' in buff_types_info:
            ind = buff_types_info.index('heal')
            buff_selected = buff_info[ind]
        elif 'choice' in buff_types_info:
            ind = buff_types_info.index('choice')
            buff_selected = buff_info[ind]
        elif 'normal' in buff_types_info:
            buff_subtypes_info = [info['buff_subtype']
                                  for ind, info in buff_info.items()]
            if 'strategy' in buff_subtypes_info:
                ind = buff_subtypes_info.index('strategy')
                buff_selected = buff_info[ind]
            elif 'survival' in buff_subtypes_info:
                ind = buff_subtypes_info.index('survival')
                buff_selected = buff_info[ind]
            else:
                buff_selected = buff_info[0]

        self.logger.info(f'selected buff {buff_selected}')

        return buff_selected

    def simulation_room_select_buff(self, buff_locs, select_func=None, buff_history=None):
        if not buff_locs:
            return False
        if not select_func:
            buff_info = {'loc': buff_locs[0]}
            return buff_info
        else:
            buff_info = select_func(buff_locs)
        return buff_info

    def simulation_room_get_buff_count(self, loc):
        buff_types = ["boss", "choice", "heal", "normal", "upgrade"]
        buff_count = 0
        for buff_type in buff_types:
            buff_locs = gio.locate_image(self.image_map[f'home_ark_simulation_room_buff_type_{buff_type}'],
                                         region=loc.to_bounding(), multi=True, multi_threshold=0.5)
            if buff_locs:
                buff_count += len(buff_locs)
        return buff_count

    def simulation_room_get_buff_selection(self):
        buff_icon_loc = gio.locate_image(self.image_map['home_ark_simulation_room_buff_buff_select_icon'],
                                         region=self.location_map['home'].to_bounding())
        if not buff_icon_loc:
            return False

        three_buff_loc = buff_icon_loc.translate(-118, 181).resize(480, 240)

        buff_count = self.simulation_room_get_buff_count(three_buff_loc)
        buff_locs = []

        if buff_count == 3:
            buff_1_loc = three_buff_loc.translate(0, 0).resize(160, 240)
            buff_2_loc = three_buff_loc.translate(160, 0).resize(160, 240)
            buff_3_loc = three_buff_loc.translate(320, 0).resize(160, 240)
            buff_locs = [buff_1_loc, buff_2_loc, buff_3_loc]
        elif buff_count == 2:
            buff_1_loc = three_buff_loc.translate(80, 0).resize(160, 240)
            buff_2_loc = three_buff_loc.translate(240, 0).resize(160, 240)
            buff_locs = [buff_1_loc, buff_2_loc]
        elif buff_count == 1:
            buff_1_loc = three_buff_loc.translate(160, 0).resize(160, 240)
            buff_locs = [buff_1_loc]

        return buff_locs

    def simulation_room_choose_substitute_buff_simple(self, buff_locations):
        buff_info = {}
        buff_locations = sorted(
            buff_locations, key=lambda item: item.height, reverse=True)
        return buff_locations[0], buff_info

    def simulation_room_choose_limit_replace_simple(self, buff_locations):
        buff_info = {}
        buff_locations = sorted(
            buff_locations, key=lambda item: item.height, reverse=True)
        return buff_locations[2], buff_info

    def simulation_room_obtain_buff_choose(self, buff_locations, decision_func=None):
        if not buff_locations:
            return None, {}
        buff_info = {}

        if not decision_func:
            return buff_locations[0], buff_info
        else:
            buff_location, buff_info = decision_func(buff_locations)
            return buff_location, buff_info

    def simulation_room_obtain_buff(self, decision_func=None):
        self.logger.info('selecting the buff to obtain...')
        buff_locations = self.get_buff_location()
        buff_location, buff_info = self.simulation_room_obtain_buff_choose(
            buff_locations, decision_func)
        if buff_location:
            gio.mouse_center_click(buff_location)
            gio.locate_image_and_click(self.image_map['home_ark_simulation_room_buff_confirm'],
                                       region=self.location_map['home'].to_bounding(
            ),
                loop=True, timeout=3)
        else:
            self.logger.info('cannot choose buff any further')
            return False
        return buff_info

    def simulation_room_battle_session(self):
        quick_battle = gio.locate_image_and_click(self.image_map['home_ark_simulation_room_quick_battle'],
                                                  region=self.location_map['home'].to_bounding(
        ),
            loop=True, timeout=3)
        if not quick_battle:
            if not gio.locate_image_and_click(self.image_map['home_ark_simulation_room_battle'],
                                              region=self.location_map['home'].to_bounding(
            ),
                    loop=True):
                self.logger.info('could not enter battle')
                return False
            self.logger.info('waiting for battle session to end...')
            if not gio.locate_image_and_click(self.image_map['home_ark_simulation_room_battle_end'],
                                              region=self.location_map['home'].to_bounding(
            ),
                    loop=True, delay=10, timeout=18):
                self.logger.info('could not end battle')
                return False
        gio.delay(2)
        self.logger.info('battle session ended')
        return True

    def simulation_room_select_buff_secondary_action(self, buff_info):
        buff_type = buff_info.get('buff_type')
        if buff_type and buff_type in ['heal', 'choice', 'upgrade']:
            self.logger.info(
                f"selecting a secondary action for the buff with buff type {buff_type}")
            actions = gio.locate_image(self.image_map[f'home_ark_simulation_room_buff_{buff_type}_{buff_type}_icon'],
                                       region=self.location_map['home'].to_bounding(), multi=True)
            if not actions:
                self.logger.warning(
                    f'could not follow up on buff selection with buff type {buff_type}')
                gio.locate_image_and_click(self.image_map[f'home_ark_simulation_room_buff_cancel'],
                                           region=self.location_map['home'].to_bounding(
                ),
                    loop=True, timeout=3)
            else:
                gio.mouse_center_click(actions[0])
            gio.delay(1)
            gio.locate_image_and_click(self.image_map[f'confirm'],
                                       region=self.location_map['home'].to_bounding(
            ),
                loop=True, timeout=3)
            gio.delay(1)
            if buff_type == 'heal':
                gio.locate_image_and_click(self.image_map[f'confirm'],
                                           region=self.location_map['home'].to_bounding(
                ),
                    loop=True, timeout=5)
            elif buff_type == 'choice':
                gio.locate_image_and_click(self.image_map[f'confirm'],
                                           region=self.location_map['home'].to_bounding(
                ),
                    loop=True, timeout=5)
            elif buff_type == 'upgrade':
                gio.locate_image_and_click(self.image_map[f'confirm'],
                                           region=self.location_map['home'].to_bounding(
                ),
                    loop=True, timeout=5)

            if gio.locate_image_and_click(self.image_map[f'home_ark_simulation_room_buff_unavailable_buff_home'],
                                          region=self.location_map['home'].to_bounding(
            ),
                    loop=True, timeout=2):
                gio.locate_image_and_click(self.image_map[f'home_ark_simulation_room_buff_cancel'],
                                           region=self.location_map['home'].to_bounding(
                ),
                    loop=True, timeout=1)

                gio.locate_image_and_click(self.image_map[f'confirm'],
                                           region=self.location_map['home'].to_bounding(
                ),
                    loop=True, timeout=2)
                gio.locate_image_and_click(self.image_map[f'confirm'],
                                           region=self.location_map['home'].to_bounding(
                ),
                    loop=True, timeout=2)
            return True
        else:
            return False

    def simulation_room_single_battle(self, buff_list=[]):
        buff_locs = self.simulation_room_get_buff_selection()
        self.logger.info('single simulation battle started...')
        if buff_locs:
            self.logger.info('arrvied at challenge selection')
            buff_info = self.simulation_room_select_buff(
                buff_locs, select_func=self.simulation_room_select_buff_simple)
            gio.mouse_center_click(buff_info.get('loc'))
            buff_obtained = self.simulation_room_select_buff_secondary_action(
                buff_info)

            battle_end = False
            if not buff_obtained:
                battle_end = self.simulation_room_battle_session()

            if not battle_end and not buff_obtained:
                self.logger.info('battle session failed')
                return buff_list

        self.logger.info('started selecting buffs')

        buff = None
        if gio.locate_image_and_click(self.image_map['home_ark_simulation_room_buff_obtain_buff_home'],
                                      region=self.location_map['home'].to_bounding(
        ),
                loop=True, timeout=5, button=None):
            self.logger.info('reached buff select window')
            buff = self.simulation_room_obtain_buff()
        elif gio.locate_image_and_click(self.image_map['home_ark_simulation_room_buff_change_buff_home'],
                                        region=self.location_map['home'].to_bounding(
        ),
                loop=True, timeout=1, button=None):
            buff = self.simulation_room_obtain_buff()
            gio.locate_image_and_click(self.image_map[f'confirm'],
                                       region=self.location_map['home'].to_bounding(
            ),
                loop=True, timeout=3)
        elif gio.locate_image_and_click(self.image_map['home_ark_simulation_room_buff_alter_buff_home'],
                                        region=self.location_map['home'].to_bounding(
        ),
                loop=True, timeout=1, button=None):
            buff = self.simulation_room_obtain_buff()
            gio.locate_image_and_click(self.image_map[f'confirm'],
                                       region=self.location_map['home'].to_bounding(
            ),
                loop=True, timeout=3)

        if gio.locate_image_and_click(self.image_map['home_ark_simulation_room_buff_substitute_buff_home'],
                                      region=self.location_map['home'].to_bounding(
        ),
                loop=True, timeout=5, button=None):
            buff = self.simulation_room_obtain_buff(
                decision_func=self.simulation_room_choose_substitute_buff_simple)
            gio.locate_image_and_click(self.image_map[f'confirm'],
                                       region=self.location_map['home'].to_bounding(
            ),
                loop=True, timeout=3)
        elif gio.locate_image_and_click(self.image_map['home_ark_simulation_room_buff_remove_buff_home'],
                                        region=self.location_map['home'].to_bounding(
        ),
                loop=True, timeout=1, button=None):
            buff = self.simulation_room_obtain_buff()
            gio.locate_image_and_click(self.image_map[f'confirm'],
                                       region=self.location_map['home'].to_bounding(
            ),
                loop=True, timeout=3)
        elif gio.locate_image_and_click(self.image_map['home_ark_simulation_room_buff_limit_replace_buff_home'],
                                        region=self.location_map['home'].to_bounding(
        ),
                loop=True, timeout=1, button=None):
            buff = self.simulation_room_obtain_buff(
                decision_func=self.simulation_room_choose_limit_replace_simple)
            gio.locate_image_and_click(self.image_map['confirm'],
                                       region=self.location_map['home'].to_bounding(
            ),
                loop=True, timeout=3)

        self.logger.info('buff selection ended')

        if buff:
            buff_list.append(buff)
        self.logger.info('single simulation battle ended, moving on...')
        return buff_list

    def simulation_room_single_run(self, difficulty=5, sector="C", ignore_clear=False, simulation_status='start'):
        """
        perform simulation run at the given difficulty and level
        default at difficulty 5 and sector C
        """

        # assuming starting at a random point in the game
        # start a new simulation sesson at the given difficulty and level
        sector = sector.lower()

        if simulation_status == 'start':
            self.logger.info(
                f'starting simulation run difficulty {difficulty} sector {sector}...')

            if not gio.locate_image_and_click(self.image_map[f'home_ark_simulation_room_level_{difficulty}'],
                                              region=self.location_map['home'].to_bounding(
            ),
                    loop=True):
                self.logger.info(f'Could not find difficulty {difficulty}')
                return False

            if not gio.locate_image_and_click(self.image_map[f'home_ark_simulation_room_sector_{sector}'],
                                              region=self.location_map['home'].to_bounding(
            ),
                    loop=True):
                self.logger.info(f'Could not find sector {difficulty}')
                return False

            if ignore_clear is False:
                if gio.locate_image_and_click(self.image_map[f'home_ark_simulation_room_simulation_cleared'],
                                              region=self.location_map['home'].to_bounding(
                ),
                        loop=True):
                    self.logger.info(
                        f'Sector cleared, ignoring clear is set to false, exiting...')
                    simulation_status = "end_simulation"
                    return simulation_status

            if not gio.locate_image_and_click(self.image_map[f'home_ark_simulation_room_start_session'],
                                              region=self.location_map['home'].to_bounding(
            ),
                    loop=True):
                self.logger.info(f'Could not start session')
                return False

        # confirm that we are now inside the simulation
        if not gio.locate_image_and_click(self.image_map[f'home_ark_simulation_room_end_session'],
                                          region=self.location_map['home'].to_bounding(
        ),
                loop=True, button=None):
            self.logger.info(f'Could not load simulation screen')
            return False

        simulation_status = "continue"
        buff_list = []
        while simulation_status == "continue":
            if gio.locate_image_and_click(self.image_map[f'home_ark_simulation_room_next_sector'],
                                          region=self.location_map['home'].to_bounding(
            ),
                    loop=True, timeout=3):
                simulation_status = 'next_sector'
                break
            elif gio.locate_image_and_click(self.image_map[f'home_ark_simulation_room_end_simulation'],
                                            region=self.location_map['home'].to_bounding(
            ),
                    loop=True, timeout=1):
                simulation_status = 'end_simulation'
                gio.locate_image_and_click(self.image_map[f'confirm'],
                                           region=self.location_map['home'].to_bounding(
                ),
                    loop=True, timeout=3)
                gio.locate_image_and_click(self.image_map[f'home_ark_simulation_room_buff_pass'],
                                           region=self.location_map['home'].to_bounding(
                ),
                    loop=True, timeout=3)
                gio.locate_image_and_click(self.image_map[f'confirm'],
                                           region=self.location_map['home'].to_bounding(
                ),
                    loop=True, timeout=3)
                gio.locate_image_and_click(self.image_map[f'confirm'],
                                           region=self.location_map['home'].to_bounding(
                ),
                    loop=True, timeout=3)
                break
            else:
                buff_list = self.simulation_room_single_battle(buff_list)

        self.logger.info(
            f'Finished simulation run difficulty {difficulty} sector {sector}...')
        return simulation_status

    def simulation_room(self, difficulty=None, sector=None):
        """
        perform simulation run
        should start at the most reasonble level possible
        """
        self.logger.info('Simulation room started...')

        if not difficulty or not sector:
            settings = self.routine.get('simulation_room', {}).get('settings')
            if settings:
                difficulty = settings.get('difficulty')
                sector = settings.get('sector')
                ignore_clear = settings.get('ignore_clear')
            if not difficulty or not sector:
                difficulty = 1
                sector = 'A'
                ignore_clear = False

        # if no shop starting point available exit home
        if not gio.locate_image_and_click(self.image_map['home_ark'],
                                          region=self.location_map['home'].to_bounding(
        ),
                loop=True, timeout=3):
            self.logger.info(
                'Could not find ark entrance, exiting home to restart')
            self.exit_to_home()
            # if still no shop detected, return false
            if not gio.locate_image_and_click(self.image_map['home_ark'],
                                              region=self.location_map['home'].to_bounding(
            ),
                    loop=True):
                self.logger.info(
                    'Could not find ark entrance, session ended')
                return False

        gio.delay(3)

        if not gio.locate_image_and_click(self.image_map['home_ark_simulation_room'],
                                          region=self.location_map['home'].to_bounding(
        ),
                loop=True):
            self.logger.info('Could not find simulation room entrance')
            return False

        if not gio.locate_image_and_click(self.image_map['home_ark_simulation_room_start'],
                                          region=self.location_map['home'].to_bounding(
        ),
                loop=True):
            self.logger.info('Could not start simulation')
            return False

        simulation_status = self.simulation_room_single_run(
            difficulty, sector, ignore_clear)
        while simulation_status and simulation_status != 'end_simulation':
            simulation_status = self.simulation_room_single_run(
                simulation_status=simulation_status)

        if not simulation_status:
            self.logger.info(f'Simulation room ended with errors.')

        self.logger.info(f'Simulation room ended.')
        self.exit_to_home()

    def dispatch(self):
        self.logger.info('Dispatching started...')

        # if no dispatch available exit home
        if not gio.locate_image_and_click(self.image_map['home_outpost'],
                                          region=self.location_map['home'].to_bounding(
        ),
                loop=True, timeout=3):
            self.logger.info(
                'Could not find outpost entrance, exiting home to restart')
            self.exit_to_home()
            # if still no shop detected, return false
            if not gio.locate_image_and_click(self.image_map['home_outpost'],
                                              region=self.location_map['home'].to_bounding(
            ),
                    loop=True):
                self.logger.info(
                    'Could not find outpost entrance, session ended')
                return False
        if not gio.locate_image_and_click(self.image_map['home_outpost_bulletin'],
                                          region=self.location_map['home'].to_bounding(
        ),
                loop=True, timeout=3):
            self.logger.info(
                'Could not find dispatch bulletin, exiting home to restart')
            return False

        if gio.locate_image_and_click(self.image_map['home_outpost_bulletin_claim_all'],
                                      region=self.location_map['home'].to_bounding(
        ),
                loop=True, timeout=3):
            gio.delay(2)
            if gio.locate_image_and_click(self.image_map['home_outpost_express_reward'],
                                          region=self.location_map['home'].to_bounding(
            ),
                    loop=True, timeout=3):

                self.logger.info('Claimed all reward')

        self.back()

        if not gio.locate_image_and_click(self.image_map['home_outpost_bulletin'],
                                          region=self.location_map['home'].to_bounding(
        ),
                loop=True, timeout=3):
            self.logger.info(
                'Could not find dispatch bulletin, exiting home to restart')
            return False

        if gio.locate_image_and_click(self.image_map['home_outpost_bulletin_send_all'],
                                      region=self.location_map['home'].to_bounding(
        ),
                loop=True, timeout=3):
            gio.delay(2)
            if gio.locate_image_and_click(self.image_map['home_outpost_bulletin_send'],
                                          region=self.location_map['home'].to_bounding(
            ),
                    loop=True, timeout=3):

                self.logger.info('Dispatched all')

        self.logger.info('Dispatching ended, exiting home')
        self.exit_to_home()
        return True

    def claim_daily_mission_reward(self):
        self.logger.info('Daily mission reward claiming started...')

        # if no dispatch available exit home
        if not gio.locate_image_and_click(self.image_map['home_mission'],
                                          region=self.location_map['home'].to_bounding(
        ),
                loop=True, timeout=3):
            self.logger.info(
                'Could not find outpost entrance, exiting home to restart')
            self.exit_to_home()
            # if still no shop detected, return false
            if not gio.locate_image_and_click(self.image_map['home_mission'],
                                              region=self.location_map['home'].to_bounding(
            ),
                    loop=True):
                self.logger.info(
                    'Could not find outpost entrance, session ended')
                return False
        if gio.locate_image_and_click(self.image_map['home_mission_claim_all'],
                                      region=self.location_map['home'].to_bounding(
        ),
                loop=True, timeout=3):
            gio.delay(1)
            gio.locate_image_and_click(self.image_map['home_mission_claim_all'],
                                       region=self.location_map['home'].to_bounding(
            ), loop=True, timeout=3)

            self.logger.info('Claimed all daily mission reward')
        self.logger.info('Daily mission reward claiming ended, exiting home')
        self.exit_to_home()
        return True

    def get_event_steps(self, event_name):
        if not event_name:
            return []
        event_steps = {k: v for k, v in self.image_map.items()
                       if f'{event_name}_step' in k}
        event_steps = dict(sorted(event_steps.items()))
        return event_steps

    def traverse_steps(self, steps, timeout=5, delay=1, confidence=0.99):
        for step, step_im in steps.items():
            if not gio.locate_image_and_click(step_im,
                                              region=self.location_map['home'].to_bounding(
                                              ),
                                              confidence=confidence, loop=True, timeout=timeout):
                self.scroll()
                if not gio.locate_image_and_click(step_im,
                                                  region=self.location_map['home'].to_bounding(
                                                  ),
                                                  confidence=confidence, loop=True, timeout=timeout):
                    self.logger.warning(
                        f'Could not find {step}')
                    return False
            gio.delay(delay)
        return True

    def repeat_event_level(self, event_name='chainsaw_2023'):
        self.logger.info('Repeating event level started...')

        # if no dispatch available exit home
        if not gio.locate_image_and_click(self.image_map['home_event'],
                                          region=self.location_map['home'].to_bounding(
        ),
                loop=True, timeout=3):
            self.logger.info(
                'Could not find event entrance, exiting home to restart')
            self.exit_to_home()
            # if still no shop detected, return false
            if not gio.locate_image_and_click(self.image_map['home_event'],
                                              region=self.location_map['home'].to_bounding(
            ),
                    loop=True):
                self.logger.info(
                    'Could not find event entrance, session ended')
                return False

        event_steps = self.get_event_steps(event_name)

        if not event_steps:
            self.logger.warning(
                'No available events, check if event images are present')
            self.exit_to_home()
            return False

        at_event_start = self.traverse_steps(event_steps)

        if not at_event_start:
            self.logger.warning('could not repeat event levels')
            self.exit_to_home()
            return False

        if not gio.locate_image_and_click(self.image_map[f'home_event_start'],
                                          region=self.location_map['home'].to_bounding(), loop=True, confidence=0.95):
            self.logger.warning('could not start event levels')
            self.exit_to_home()
            return False

        event_stop = False
        while not event_stop:
            gio.locate_image_and_click(self.image_map[f'home_event_restart'],
                                       region=self.location_map['home'].to_bounding(
            ),
                loop=True, confidence=0.95, timeout=1, delay=10)

            event_stop = gio.locate_image_and_click(self.image_map[f'home_event_no_restart'],
                                                    region=self.location_map['home'].to_bounding(
            ),
                loop=True, confidence=0.95, timeout=1, delay=10)
            if event_stop:
                gio.mouse_center_click(self.location_map['home'])
                gio.delay(2)

        self.logger.info(f"repeating event {event_name} end")
        self.exit_to_home()
        return True

    def auto_daily(self, timeout=3):
        self.logger.info(f'starting daily')
        self.logger.info(
            f'{len([r for k, r in self.routine.items() if (r.get("auto") is True and r.get("frequency") == "daily") ])} dailies to run')
        prioritized_routine = self._sort_dict_by_value(
            self.routine, "priority")
        for key, r in prioritized_routine.items():
            if r.get("auto") is True and r.get("frequency") == "daily":
                func = getattr(self, r.get("name"))
                self.logger.info(f'running daily {r.get("name")}')
                for i in range(timeout):
                    try:
                        func()
                        break
                    except Exception as e:
                        self.logger.error(
                            f"While trying daily {i+1} time {r.get('display_name')} the following error occured")
                        self.logger.error(e)

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
