from thread_with_trace import ThreadWithTrace, make_killable_thread
from nikke_agent import Agent
from game_interaction_io import GameInteractionIO as gio
import admin
from idlelib.tooltip import Hovertip
import gettext
import logging
from threading import *
import json
import os
import time
from tkinter import Checkbutton
import tkinter.scrolledtext as ScrolledText
from tkinter.messagebox import showinfo
from tkinter import filedialog as fd
from tkinter import ttk
import tkinter as tk
from tkinter import *
import sys
import configparser


def read_config():
    """
    helper function to read language settings
    TODO: move to helper function files
    """
    config = configparser.ConfigParser()
    config.read('NIKKE_ASSISTANT.INI')
    return config


game_config = read_config()

# redirect std messages to log files
log_to_file = bool(game_config.get('app_settings', 'log_to_file'))
if log_to_file:
    sys.stdout = open('app_output.log', 'a')
    sys.stderr = open('app_error.log', 'a')


lang = game_config.get('ui_settings', 'lang')
game_lang = game_config.get('game_settings', 'lang')
localedir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'locale')
translate = gettext.translation(
    'nikke-assistant', localedir, languages=[lang], fallback=True)
_ = translate.gettext


current_agent = None
user_profile = None
user_profile_path = 'agent\\default\\user_profile.json'

if not admin.isUserAdmin():
    admin.runAsAdmin()


class TextHandler(logging.Handler):
    # This class allows you to log to a Tkinter Text or ScrolledText widget
    # Adapted from Moshe Kaplan: https://gist.github.com/moshekaplan/c425f861de7bbf28ef06

    def __init__(self, text):
        # run the regular Handler __init__
        logging.Handler.__init__(self)
        # Store a reference to the Text it will log to
        self.text = text

    def emit(self, record):
        msg = self.format(record)

        def append():
            self.text.configure(state='normal')
            self.text.insert(tk.END, msg + '\n')
            self.text.configure(state='disabled')
            # Autoscroll to the bottom
            self.text.yview(tk.END)
        # This is necessary because we can't modify the Text from other threads
        self.text.after(0, append)
        self.text.update()


def get_user_profile():
    global user_profile
    if os.path.isfile(user_profile_path):
        with open(user_profile_path, 'r') as user_profile_file:
            data = user_profile_file.read()
            user_profile = json.loads(data)


def save_user_profile():
    with open(user_profile_path, 'w') as json_file:
        json.dump(user_profile, json_file)
    current_agent.save_profile()


def initialize_agent(logger=None):
    global current_agent
    get_user_profile()
    if user_profile is not None:
        current_agent = Agent(profile_path=user_profile.get(
            'profile_path'), custom_logger=logger)


def save_size(event):
    with open("nikke_interface.conf", "w") as conf:
        conf.write(root.geometry())  # Assuming root is the root window


def get_size():
    size = ""
    with open("nikke_interface.conf", "r") as conf:
        size = conf.readline()  # Assuming root is the root window
    return size


def select_file():
    global current_agent
    filetypes = (
        ('Profiles', '*.json'),
        ('All files', '*.*')
    )

    filename = fd.askopenfilename(
        title=_('Choose Your Profile'),
        initialdir='agent\\default\\',
        filetypes=filetypes)

    if len(filename) == 0:
        return None

    if current_agent is None:
        current_agent = Agent()
    else:
        current_agent.load_profile(profile_path=filename)

    user_profile['profile_path'] = filename
    update_profile_label(text=current_agent.profile_name)

    showinfo(
        title=_('Profile Loaded!'),
        message=(current_agent.profile_name if (current_agent is not None)
                 else _("incorrect format, please check again"))
    )


def save_settings():
    save_user_profile()
    showinfo(
        title=_('Profile Saved'),
        message=_('Profile saved successfully!')
    )


def qexit():
    root.destroy()


def update_profile_label(text):
    lblProfile.configure(text=_("Current Profile Loaded \n")+text)


def update_status_label(text):
    lblStatus.configure(text=_('Status - ') + text)


def reload_game():
    global current_agent
    if not current_agent:
        showinfo(
            title=_('Error'),
            message=_('No active agent found')
        )
    else:
        game_found = current_agent.initialize_game()
        if not game_found:
            showinfo(
                title=_('Error'),
                message=_(
                    'No valid game screen found. Make sure nothing is blocking the game screen.')
            )
            return False
        current_status.set(_('Game Loaded!'))


def auto_daily():
    global current_agent
    if not current_agent:
        showinfo(
            title=_('Error'),
            message=_('No active agent found')
        )
    else:
        current_status.set(_('Doing dailies...\npress DEL to stop'))
        root.update()

        def callback():
            current_agent.auto_daily()
            current_status.set(_('Stopped doing dailies.'))

        make_killable_thread(callback, current_status, logger)


def claim_outpost_reward():
    global current_agent
    if not current_agent:
        showinfo(
            title=_('Error'),
            message=_('No active agent found')
        )
    else:
        current_status.set(_('Claiming outpost rewards...\npress DEL to stop'))
        root.update()
        current_agent.claim_outpost_reward()
        current_status.set(_('Stopped claiming outpost rewards.'))


def claim_friend_points():
    global current_agent
    if not current_agent:
        showinfo(
            title=_('Error'),
            message=_('No active agent found')
        )
    else:
        current_status.set(
            _('claiming friendship points...\npress DEL to stop'))
        root.update()
        current_agent.claim_friend_points()
        current_status.set(_('Stopped claiming friendship points'))


def advise_nikke():
    global current_agent
    if not current_agent:
        showinfo(
            title=_('Error'),
            message=_('No active agent found')
        )
    else:
        current_status.set(_('Advising Nikkes...\npress DEL to stop'))
        root.update()
        current_agent.advise_nikke()
        current_status.set(_('Stopped advising Nikkes.'))


def rookie_arena():
    global current_agent
    if not current_agent:
        showinfo(
            title=_('Error'),
            message=_('No active agent found')
        )
    else:
        current_status.set(_('Battling rookie arena...\npress DEL to stop'))
        root.update()
        current_agent.rookie_arena()
        current_status.set(_('Stopped battling rookie arena.'))


def normal_shop():
    global current_agent
    if not current_agent:
        showinfo(
            title=_('Error'),
            message=_('No active agent found')
        )
    else:
        current_status.set(_('Shopping in normal shop...\npress DEL to stop'))
        root.update()
        current_agent.normal_shop()
        current_status.set(_('Stopped shopping in normal shop.'))


def claim_nikke_rehab_reward():
    global current_agent
    if not current_agent:
        showinfo(
            title=_('Error'),
            message=_('No active agent found')
        )
    else:
        current_status.set(
            _('Claiming Nikke rehab reward...\npress DEL to stop'))
        root.update()
        current_agent.claim_nikke_rehab_reward()
        current_status.set(_('Stopped claiming Nikke rehab reward.'))


def simulation_room():
    global current_agent
    if not current_agent:
        showinfo(
            title=_('Error'),
            message=_('No active agent found')
        )
    else:
        current_status.set(_('Running simulation room...\npress DEL to stop'))
        root.update()
        current_agent.simulation_room()
        current_status.set(_('Stopped running simulation room.'))


def dispatch():
    global current_agent
    if not current_agent:
        showinfo(
            title=_('Error'),
            message=_('No active agent found')
        )
    else:
        current_status.set(_('Dispatching...\npress DEL to stop'))
        root.update()
        current_agent.dispatch()
        current_status.set(_('Stopped Dispatching.'))


def claim_daily_mission_reward():
    global current_agent
    if not current_agent:
        showinfo(
            title=_('Error'),
            message=_('No active agent found')
        )
    else:
        current_status.set(
            _('Claiming daily mission rewards...\npress DEL to stop'))
        root.update()
        current_agent.claim_daily_mission_reward()
        current_status.set(_('Stopped claiming daily mission rewards.'))


def repeat_event_level():
    global current_agent
    if not current_agent:
        showinfo(
            title=_('Error'),
            message=_('No active agent found')
        )
    else:
        current_status.set(_('Repeating event levels...\npress DEL to stop'))
        root.update()
        current_agent.repeat_event_level()
        current_status.set(_('Stopped repeating event levels.'))


def tower():
    global current_agent
    if not current_agent:
        showinfo(
            title=_('Error'),
            message=_('No active agent found')
        )
    else:
        current_status.set(_('Running tower...\npress DEL to stop'))
        root.update()
        current_agent.tower()
        current_status.set(_('Stopped tower.'))


def select_game_window():
    global current_agent
    if not current_agent:
        showinfo(
            title=_('Error'),
            message=_('No active agent found')
        )
    else:
        current_status.set(_('Selecting active window...\npress DEL to stop'))
        root.update()
        top = Toplevel(root)
        top.geometry(app_size)
        top.title(_("Select your Nikke application window"))
        Label(top, font=('aria', 10, 'bold'), text=_("Click on the name below"),
              fg="steel blue", bd=10, anchor='w').pack()
        Label(top, font=('aria', 10, 'bold'), text=_("To select your Nikke game window"),
              fg="steel blue", bd=10, anchor='w').pack()
        apps = gio.get_available_applications()

        variable = StringVar(top)
        if current_agent.settings.get('active_window') in apps:
            variable.set(current_agent.settings.get('active_window'))
        else:
            variable.set(apps[0])  # default value
        w = OptionMenu(top, variable, *apps)
        w.pack()

        def ok():
            active_window_name = variable.get()
            current_agent.select_active_window(active_window_name)
            current_status.set(
                _('Selected {} as the game window').format(active_window_name))
            top.destroy()

        button = Button(top, text="OK", command=ok)
        button.pack()


def select_resolution():
    global current_agent
    if not current_agent:
        showinfo(
            title=_('Error'),
            message=_('No active agent found')
        )
    else:
        current_status.set(_('Selecting resolution...\npress DEL to stop'))
        root.update()
        top = Toplevel(root)
        top.geometry(app_size)
        top.title(_("Select your Nikke resolution"))
        resolution = current_agent.default_real_resolution

        width_label = Label(top, padx=16, pady=8, bd=10, fg="black", font=(
            'ariel', 12, 'bold'), width=20, text=_("Width"), bg="powder blue")
        width_label.grid(row=0, column=0)
        width = Text(top, padx=16, pady=8, bd=10, fg="black", font=(
            'ariel', 12, 'bold'), width=20, bg="powder blue")
        width.grid(row=1, column=0)
        height_label = Label(top, padx=16, pady=8, bd=10, fg="black", font=(
            'ariel', 12, 'bold'), width=20, text=_("Height"), bg="powder blue")
        height_label.grid(row=0, column=1)
        height = Text(top, padx=16, pady=8, bd=10, fg="black", font=(
            'ariel', 12, 'bold'), width=20, bg="powder blue")
        height.grid(row=1, column=1)

        width.insert(tk.END, resolution[0])
        height.insert(tk.END, resolution[1])

        def ok():
            width_val, height_val = int(
                width.get("1.0", 'end-1c')), int(height.get("1.0", 'end-1c'))
            current_agent.resize([width_val, height_val])
            current_status.set(
                _('Set new solution to {}x{}').format(str(width), str(height)))
            top.destroy()

        button = Button(top, padx=16, pady=8, bd=10, fg="black", font=(
            'ariel', 12, 'bold'), width=20, text=_("OK"), bg="powder blue", command=ok)
        button.grid(row=1, column=3)


def change_settings():
    global current_agent
    if not current_agent:
        showinfo(
            title=_('Error'),
            message=_('No active agent found')
        )
    else:
        current_status.set(_('Changing Settings...\npress DEL to stop'))
        root.update()
        root1 = Toplevel(root)
        root1.geometry(app_size)
        root1.title(_("Change Settings"))
        text = ScrolledText.ScrolledText(root1, state='disable')
        text.pack(fill='both', expand=True)

        top = tk.Frame(text)
        text.window_create('1.0', window=top)

        row_ind = 0
        routine_dict = {}
        settings_dict = {}

        for rkey, routine in current_agent.routine.items():
            routine_name = Label(top, padx=16, pady=8, bd=10, fg="black", font=(
                'ariel', 12, 'bold'), width=20, text=routine.get(f'display_name_{lang}'), bg="powder blue")
            routine_name.grid(row=row_ind, column=0, columnspan=2)
            row_ind += 1
            routine_dict[rkey] = {}
            for skey, setting in routine.get('settings').items():
                setting_name = Label(top, padx=16, pady=8, bd=10, fg="black", font=(
                    'ariel', 12, 'bold'), width=20, text=setting.get(f'display_name_{lang}'), bg="powder blue")
                if isinstance(setting.get('value'), bool):
                    checkbox_var = IntVar(value=int(setting.get('value')))
                    setting_value = Checkbutton(top, padx=16, pady=8, bd=10, fg="black", font=(
                        'ariel', 12, 'bold'), variable=checkbox_var, onvalue=1, offvalue=0, width=20, height=2, bg="powder blue")
                    routine_dict[rkey][skey] = checkbox_var
                else:
                    setting_value = Text(top, padx=16, pady=8, bd=10, fg="black", font=(
                        'ariel', 12, 'bold'), width=20, height=2, bg="powder blue")
                    setting_value.insert(tk.END, setting.get('value'))
                    routine_dict[rkey][skey] = setting_value
                setting_name.grid(row=row_ind, column=0)
                setting_value.grid(row=row_ind, column=1)
                if setting.get('tooltip_{lang}'):
                    myTip = Hovertip(setting_name, setting.get(
                        'tooltip_{lang}'), hover_delay=1000)
                row_ind += 1

        routine_name = Label(top, padx=16, pady=8, bd=10, fg="black", font=(
            'ariel', 12, 'bold'), width=20, text=_("Settings"), bg="powder blue")
        routine_name.grid(row=row_ind, column=0, columnspan=2)
        row_ind += 1
        for skey, setting in current_agent.settings.items():
            setting_name = Label(top, padx=16, pady=8, bd=10, fg="black", font=(
                'ariel', 12, 'bold'), width=20, text=setting.get(f'display_name_{lang}'), bg="powder blue")
            if isinstance(setting.get('value'), bool):
                checkbox_var = IntVar(value=int(setting.get('value')))
                setting_value = Checkbutton(top, padx=16, pady=8, bd=10, fg="black", font=(
                    'ariel', 12, 'bold'), variable=checkbox_var, onvalue=1, offvalue=0, width=20, height=2, bg="powder blue")
                settings_dict[skey] = checkbox_var
            else:
                setting_value = Text(top, padx=16, pady=8, bd=10, fg="black", font=(
                    'ariel', 12, 'bold'), width=20, height=2, bg="powder blue")
                setting_value.insert(tk.END, setting.get('value'))
                settings_dict[skey] = setting_value
            setting_name.grid(row=row_ind, column=0)
            setting_value.grid(row=row_ind, column=1)
            if setting.get('tooltip_{lang}'):
                myTip = Hovertip(setting_name, setting.get(
                    'tooltip_{lang}'), hover_delay=1000)
            row_ind += 1

        def ok():
            for rkey, routine in routine_dict.items():
                for skey, setting_value in routine.items():
                    if isinstance(current_agent.routine[rkey]['settings'][skey]['value'], bool):
                        current_agent.routine[rkey]['settings'][skey]['value'] = bool(
                            setting_value.get())
                    else:
                        current_agent.routine[rkey]['settings'][skey]['value'] = type(
                            current_agent.routine[rkey]['settings'][skey]['value'])(setting_value.get("1.0", 'end-1c'))

            for skey, setting_value in settings_dict.items():
                if isinstance(current_agent.settings[skey]['value'], bool):
                    current_agent.settings[skey]['value'] = bool(
                        setting_value.get())
                else:
                    current_agent.settings[skey]['value'] = type(
                        current_agent.settings[skey]['value'])(setting_value.get("1.0", 'end-1c'))

            current_status.set(
                _('Settings Changed'))
            root1.destroy()

        button = Button(top, padx=16, pady=8, bd=10, fg="black", font=(
            'ariel', 12, 'bold'), width=20, text=_("OK"), bg="powder blue", command=ok)
        button.grid(row=row_ind, column=3)


def no_action():
    showinfo(
        title=_('No yet released'),
        message=_('The function is not yet released')
    )
    return True


root = Tk()
root.iconbitmap("./images/nikke_icon.ico")
app_size = get_size()
root.geometry(app_size)
root.title(_("Nikke Assistant"))
# root.resizable(False, False)
root.bind("<Configure>", save_size)

Tops = Frame(root, bg="white", width=960, height=100, relief=SUNKEN)
Tops.pack(side=TOP)

f1 = Frame(root, width=960, height=100, relief=SUNKEN)
f1.pack(side=LEFT)

f2 = Frame(root, width=960, height=200, relief=SUNKEN)
f2.pack(side=RIGHT)
# ------------------TIME--------------
localtime = time.asctime(time.localtime(time.time()))
# -----------------INFO TOP------------
lblinfo = Label(Tops, font=('aria', 30, 'bold'),
                text=_("Nikke Assistant"), fg="steel blue", bd=10, anchor='w')
lblinfo.grid(row=0, column=0)

lblinfo = Label(Tops, font=('aria', 20, ),
                text=localtime, fg="steel blue", anchor=W)
lblinfo.grid(row=1, column=0)

# --------------------INFO Mid--------------
lbltip = Label(Tops, font=('aria', 10, 'bold'),
               text=_("Tip: Press Control-C to stop a running task"), fg="steel blue", anchor='w')
lbltip.grid(row=2, column=0)

current_status = tk.StringVar()
current_status.set('status')

lblProfile = Label(Tops, font=('aria', 10, 'bold'), text=_("Current Profile Loaded \n") +
                   (current_agent.profile_name if current_agent else ""), fg="steel blue", anchor='w')
lblProfile.grid(row=3, column=0)

lblStatus = Label(Tops, font=('aria', 10, 'bold'),
                  textvariable=current_status, fg="steel blue")
lblStatus.grid(row=4, column=0)

# -----------------------------------------buttons------------------------------------------
lblTotal = Label(f1, text="---------------------", fg="white")
lblTotal.grid(row=5, columnspan=3)


btnLoadProfile = Button(f1, padx=16, pady=8, bd=10, fg="black", font=(
    'ariel', 12, 'bold'), width=20, text=_("Load Profile"), bg="powder blue", command=select_file)
btnLoadProfile.grid(row=6, column=0)

btnLoadSkill = Button(f1, padx=16, pady=8, bd=10, fg="black", font=(
    'ariel', 12, 'bold'), width=20, text=_("Reload Game"), bg="powder blue", command=reload_game)
btnLoadSkill.grid(row=6, column=1)

btnInfChaos = Button(f1, padx=16, pady=8, bd=10, fg="black", font=(
    'ariel', 12, 'bold'), width=20, text=_("Auto Daily"), bg="powder blue", command=auto_daily)
btnInfChaos.grid(row=6, column=2)

btnx1 = Button(f1, padx=16, pady=8, bd=10, fg="black", font=('ariel', 12, 'bold'),
               width=20, text=_("Select Game Window"), bg="powder blue", command=select_game_window)
btnx1.grid(row=6, column=3)

btnLoadProfile = Button(f1, padx=16, pady=8, bd=10, fg="black", font=(
    'ariel', 12, 'bold'), width=20, text=_("Claim Outpost Reward"), bg="powder blue", command=claim_outpost_reward)
btnLoadProfile.grid(row=7, column=0)

btnLoadSkill = Button(f1, padx=16, pady=8, bd=10, fg="black", font=('ariel', 12, 'bold'),
                      width=20, text=_("Claim Friendship Points"), bg="powder blue", command=claim_friend_points)
btnLoadSkill.grid(row=7, column=1)

btnInfChaos = Button(f1, padx=16, pady=8, bd=10, fg="black", font=(
    'ariel', 12, 'bold'), width=20, text=_("Advise Nikke"), bg="powder blue", command=advise_nikke)
btnInfChaos.grid(row=7, column=2)

btnx1 = Button(f1, padx=16, pady=8, bd=10, fg="black", font=('ariel', 12, 'bold'),
               width=20, text=_("Rookie arena"), bg="powder blue", command=rookie_arena)
btnx1.grid(row=7, column=3)

btnLoadProfile = Button(f1, padx=16, pady=8, bd=10, fg="black", font=(
    'ariel', 12, 'bold'), width=20, text=_("Normal Shop Free"), bg="powder blue", command=normal_shop)
btnLoadProfile.grid(row=8, column=0)

btnLoadSkill = Button(f1, padx=16, pady=8, bd=10, fg="black", font=('ariel', 12, 'bold'),
                      width=20, text=_("Claim Rehab Reward"), bg="powder blue", command=claim_nikke_rehab_reward)
btnLoadSkill.grid(row=8, column=1)

btnInfChaos = Button(f1, padx=16, pady=8, bd=10, fg="black", font=(
    'ariel', 12, 'bold'), width=20, text=_("Simulation Room"), bg="powder blue", command=simulation_room)
btnInfChaos.grid(row=8, column=2)

btnx1 = Button(f1, padx=16, pady=8, bd=10, fg="black", font=(
    'ariel', 12, 'bold'), width=20, text=_("Dispatch"), bg="powder blue", command=dispatch)
btnx1.grid(row=8, column=3)


btnLoadProfile = Button(f1, padx=16, pady=8, bd=10, fg="black", font=(
    'ariel', 12, 'bold'), width=20, text=_("Repeat Event Level"), bg="powder blue", command=repeat_event_level)
btnLoadProfile.grid(row=9, column=0)

btnLoadSkill = Button(f1, padx=16, pady=8, bd=10, fg="black", font=('ariel', 12, 'bold'),
                      width=20, text=_("Daily Mission Reward"), bg="powder blue", command=claim_daily_mission_reward)
btnLoadSkill.grid(row=9, column=1)

btnInfChaos = Button(f1, padx=16, pady=8, bd=10, fg="black", font=(
    'ariel', 12, 'bold'), width=20, text=_("Tower"), bg="powder blue", command=tower)
btnInfChaos.grid(row=9, column=2)

btnx1 = Button(f1, padx=16, pady=8, bd=10, fg="black", font=(
    'ariel', 12, 'bold'), width=20, text=_("???"), bg="powder blue", command=no_action)
btnx1.grid(row=9, column=3)


btnSaveSetting = Button(f1, padx=16, pady=8, bd=10, fg="black", font=(
    'ariel', 12, 'bold'), width=20, text=_("End Journey"), bg="powder blue", command=qexit)
btnSaveSetting.grid(row=10, column=0)

btnx2 = Button(f1, padx=16, pady=8, bd=10, fg="black", font=(
    'ariel', 12, 'bold'), width=20, text=_("Select Resolution"), bg="powder blue", command=select_resolution)
btnx2.grid(row=10, column=1)

btnx3 = Button(f1, padx=16, pady=8, bd=10, fg="black", font=(
    'ariel', 12, 'bold'), width=20, text=_("Change Settings"), bg="powder blue", command=change_settings)
btnx3.grid(row=10, column=2)

btnprice = Button(f1, padx=16, pady=8, bd=10, fg="black", font=(
    'ariel', 12, 'bold'), width=20, text=_("Save Settings"), bg="powder blue", command=save_settings)
btnprice.grid(row=10, column=3)

console = ScrolledText.ScrolledText(f1, width=40, state='disabled')
console.configure(font='TkFixedFont')
console.grid(row=6, column=4, rowspan=5, columnspan=2, sticky='w')

text_handler = TextHandler(console)
logging.basicConfig(filename='app_log.txt',
                    level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
# Add the handler to logger
logger = logging.getLogger('Nikke Assistant')
logger.addHandler(text_handler)

initialize_agent(logger)

if __name__ == "__main__":
    root.lift()
    root.attributes('-topmost', True)
    root.after_idle(root.attributes, '-topmost', False)
    root.mainloop()


# %%
