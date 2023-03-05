from tkinter import *
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter.messagebox import showinfo
import tkinter.scrolledtext as ScrolledText
import time
import os
import json
import sys
from threading import *
import logging
from nikke_agent import Agent
from game_interaction_io import GameInteractionIO as gio
import admin

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
        title='Choose Your Skill Profile',
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
        title='Profile Loaded!',
        message=(current_agent.profile_name if (current_agent is not None)
                 else "incorrect format, please check again")
    )


def save_settings():
    save_user_profile()
    showinfo(
        title='Profile Saved',
        message='Profile saved successfully!'
    )


def qexit():
    root.destroy()


def update_profile_label(text):
    lblProfile.configure(text="Current Profile Loaded \n"+text)


def update_status_label(text):
    lblStatus.configure(text='Status - ' + text)


def reload_game():
    global current_agent
    if not current_agent:
        showinfo(
            title='Error',
            message='No active agent found'
        )
    else:
        game_found = current_agent.initialize_game()
        if not game_found:
            showinfo(
                title='Error',
                message='No valid game screen found. Make sure nothing is blocking the game screen.'
            )
            return False
        current_status.set('Game Loaded!')


def auto_daily():
    global current_agent
    if not current_agent:
        showinfo(
            title='Error',
            message='No active agent found'
        )
    else:
        current_status.set('Doing dailies...\npress DEL to stop')
        root.update()
        current_agent.auto_daily()
        current_status.set('Stopped doing dailies.')


def claim_outpost_reward():
    global current_agent
    if not current_agent:
        showinfo(
            title='Error',
            message='No active agent found'
        )
    else:
        current_status.set('Claiming outpost rewards...\npress DEL to stop')
        root.update()
        current_agent.claim_outpost_reward()
        current_status.set('Stopped claiming outpost rewards.')


def claim_friend_points():
    global current_agent
    if not current_agent:
        showinfo(
            title='Error',
            message='No active agent found'
        )
    else:
        current_status.set('claiming friendship points...\npress DEL to stop')
        root.update()
        current_agent.claim_friend_points()
        current_status.set('Stopped claiming friendship points')


def advise_nikke():
    global current_agent
    if not current_agent:
        showinfo(
            title='Error',
            message='No active agent found'
        )
    else:
        current_status.set('Advising Nikkes...\npress DEL to stop')
        root.update()
        current_agent.advise_nikke()
        current_status.set('Stopped advising Nikkes.')


def rookie_arena():
    global current_agent
    if not current_agent:
        showinfo(
            title='Error',
            message='No active agent found'
        )
    else:
        current_status.set('Battling rookie arena...\npress DEL to stop')
        root.update()
        current_agent.rookie_arena()
        current_status.set('Stopped battling rookie arena.')


def normal_shop():
    global current_agent
    if not current_agent:
        showinfo(
            title='Error',
            message='No active agent found'
        )
    else:
        current_status.set('Shopping in normal shop...\npress DEL to stop')
        root.update()
        current_agent.normal_shop()
        current_status.set('Stopped shopping in normal shop.')


def claim_nikke_rehab_reward():
    global current_agent
    if not current_agent:
        showinfo(
            title='Error',
            message='No active agent found'
        )
    else:
        current_status.set('Claiming Nikke rehab reward...\npress DEL to stop')
        root.update()
        current_agent.claim_nikke_rehab_reward()
        current_status.set('Stopped claiming Nikke rehab reward.')


def simulation_room():
    global current_agent
    if not current_agent:
        showinfo(
            title='Error',
            message='No active agent found'
        )
    else:
        current_status.set('Running simulation room...\npress DEL to stop')
        root.update()
        current_agent.simulation_room()
        current_status.set('Stopped running simulation room.')


def dispatch():
    global current_agent
    if not current_agent:
        showinfo(
            title='Error',
            message='No active agent found'
        )
    else:
        current_status.set('Dispatching...\npress DEL to stop')
        root.update()
        current_agent.dispatch()
        current_status.set('Stopped Dispatching.')


def claim_daily_mission_reward():
    global current_agent
    if not current_agent:
        showinfo(
            title='Error',
            message='No active agent found'
        )
    else:
        current_status.set(
            'Claiming daily mission rewards...\npress DEL to stop')
        root.update()
        current_agent.claim_daily_mission_reward()
        current_status.set('Stopped claiming daily mission rewards.')


def repeat_event_level():
    global current_agent
    if not current_agent:
        showinfo(
            title='Error',
            message='No active agent found'
        )
    else:
        current_status.set('Repeating event levels...\npress DEL to stop')
        root.update()
        current_agent.repeat_event_level()
        current_status.set('Stopped repeating event levels.')


def select_game_window():
    global current_agent
    if not current_agent:
        showinfo(
            title='Error',
            message='No active agent found'
        )
    else:
        current_status.set('Selecting active window...\npress DEL to stop')
        root.update()
        top = Toplevel(root)
        top.geometry(app_size)
        top.title("Select your Nikke application window")
        Label(top, font=('aria', 10, 'bold'), text="Click on the name below",
              fg="steel blue", bd=10, anchor='w').pack()
        Label(top, font=('aria', 10, 'bold'), text="To select your Nikke game window",
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
                f'Selected {active_window_name} as the game window')
            top.destroy()

        button = Button(top, text="OK", command=ok)
        button.pack()


def select_resolution():
    global current_agent
    if not current_agent:
        showinfo(
            title='Error',
            message='No active agent found'
        )
    else:
        current_status.set('Selecting resolution...\npress DEL to stop')
        root.update()
        top = Toplevel(root)
        top.geometry(app_size)
        top.title("Select your Nikke resolution")
        resolution = current_agent.default_real_resolution

        width_label = Label(top, padx=16, pady=8, bd=10, fg="black", font=(
            'ariel', 12, 'bold'), width=20, text="Width", bg="powder blue")
        width_label.grid(row=0, column=0)
        width = Text(top, padx=16, pady=8, bd=10, fg="black", font=(
            'ariel', 12, 'bold'), width=20, bg="powder blue")
        width.grid(row=1, column=0)
        height_label = Label(top, padx=16, pady=8, bd=10, fg="black", font=(
            'ariel', 12, 'bold'), width=20, text="Height", bg="powder blue")
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
                f'Set new solution to {width}x{height}')
            top.destroy()

        button = Button(top, padx=16, pady=8, bd=10, fg="black", font=(
            'ariel', 12, 'bold'), width=20, text="OK", bg="powder blue", command=ok)
        button.grid(row=1, column=3)


root = Tk()
app_size = get_size()
root.geometry(app_size)
root.title("Nikke Helper")
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
                text="Nikke Helper", fg="steel blue", bd=10, anchor='w')
lblinfo.grid(row=0, column=0)

lblinfo = Label(Tops, font=('aria', 20, ),
                text=localtime, fg="steel blue", anchor=W)
lblinfo.grid(row=1, column=0)

# --------------------INFO Mid--------------
lbltip = Label(Tops, font=('aria', 10, 'bold'),
               text="Tip: Press DEL to stop a running task", fg="steel blue", anchor='w')
lbltip.grid(row=2, column=0)

current_status = tk.StringVar()
current_status.set('status')

lblProfile = Label(Tops, font=('aria', 10, 'bold'), text="Current Profile Loaded \n" +
                   (current_agent.profile_name if current_agent else ""), fg="steel blue", anchor='w')
lblProfile.grid(row=3, column=0)

lblStatus = Label(Tops, font=('aria', 10, 'bold'),
                  textvariable=current_status, fg="steel blue")
lblStatus.grid(row=4, column=0)

# -----------------------------------------buttons------------------------------------------
lblTotal = Label(f1, text="---------------------", fg="white")
lblTotal.grid(row=5, columnspan=3)


btnLoadProfile = Button(f1, padx=16, pady=8, bd=10, fg="black", font=(
    'ariel', 12, 'bold'), width=20, text="Load Profile", bg="powder blue", command=select_file)
btnLoadProfile.grid(row=6, column=0)

btnLoadSkill = Button(f1, padx=16, pady=8, bd=10, fg="black", font=(
    'ariel', 12, 'bold'), width=20, text="Reload Game", bg="powder blue", command=reload_game)
btnLoadSkill.grid(row=6, column=1)

btnInfChaos = Button(f1, padx=16, pady=8, bd=10, fg="black", font=(
    'ariel', 12, 'bold'), width=20, text="Auto Daily", bg="powder blue", command=auto_daily)
btnInfChaos.grid(row=6, column=2)

btnx1 = Button(f1, padx=16, pady=8, bd=10, fg="black", font=('ariel', 12, 'bold'),
               width=20, text="Select Game Window", bg="powder blue", command=select_game_window)
btnx1.grid(row=6, column=3)

btnLoadProfile = Button(f1, padx=16, pady=8, bd=10, fg="black", font=(
    'ariel', 12, 'bold'), width=20, text="Claim Outpost Reward", bg="powder blue", command=claim_outpost_reward)
btnLoadProfile.grid(row=7, column=0)

btnLoadSkill = Button(f1, padx=16, pady=8, bd=10, fg="black", font=('ariel', 12, 'bold'),
                      width=20, text="Claim Friendship Points", bg="powder blue", command=claim_friend_points)
btnLoadSkill.grid(row=7, column=1)

btnInfChaos = Button(f1, padx=16, pady=8, bd=10, fg="black", font=(
    'ariel', 12, 'bold'), width=20, text="Advise Nikke", bg="powder blue", command=advise_nikke)
btnInfChaos.grid(row=7, column=2)

btnx1 = Button(f1, padx=16, pady=8, bd=10, fg="black", font=('ariel', 12, 'bold'),
               width=20, text="Rookie arena", bg="powder blue", command=rookie_arena)
btnx1.grid(row=7, column=3)

btnLoadProfile = Button(f1, padx=16, pady=8, bd=10, fg="black", font=(
    'ariel', 12, 'bold'), width=20, text="Normal Shop Free", bg="powder blue", command=normal_shop)
btnLoadProfile.grid(row=8, column=0)

btnLoadSkill = Button(f1, padx=16, pady=8, bd=10, fg="black", font=('ariel', 12, 'bold'),
                      width=20, text="Claim Rehab Reward", bg="powder blue", command=claim_nikke_rehab_reward)
btnLoadSkill.grid(row=8, column=1)

btnInfChaos = Button(f1, padx=16, pady=8, bd=10, fg="black", font=(
    'ariel', 12, 'bold'), width=20, text="Simulation Room", bg="powder blue", command=simulation_room)
btnInfChaos.grid(row=8, column=2)

btnx1 = Button(f1, padx=16, pady=8, bd=10, fg="black", font=(
    'ariel', 12, 'bold'), width=20, text="Dispatch", bg="powder blue", command=dispatch)
btnx1.grid(row=8, column=3)


btnLoadProfile = Button(f1, padx=16, pady=8, bd=10, fg="black", font=(
    'ariel', 12, 'bold'), width=20, text="Repeat Event Level", bg="powder blue", command=repeat_event_level)
btnLoadProfile.grid(row=9, column=0)

btnLoadSkill = Button(f1, padx=16, pady=8, bd=10, fg="black", font=('ariel', 12, 'bold'),
                      width=20, text="Daily Mission Reward", bg="powder blue", command=claim_daily_mission_reward)
btnLoadSkill.grid(row=9, column=1)

btnInfChaos = Button(f1, padx=16, pady=8, bd=10, fg="black", font=(
    'ariel', 12, 'bold'), width=20, text="???", bg="powder blue", command=qexit)
btnInfChaos.grid(row=9, column=2)

btnx1 = Button(f1, padx=16, pady=8, bd=10, fg="black", font=(
    'ariel', 12, 'bold'), width=20, text="???", bg="powder blue", command=qexit)
btnx1.grid(row=9, column=3)


btnSaveSetting = Button(f1, padx=16, pady=8, bd=10, fg="black", font=(
    'ariel', 12, 'bold'), width=20, text="End Journey", bg="powder blue", command=qexit)
btnSaveSetting.grid(row=10, column=0)

btnx2 = Button(f1, padx=16, pady=8, bd=10, fg="black", font=(
    'ariel', 12, 'bold'), width=20, text="Select Resolution", bg="powder blue", command=select_resolution)
btnx2.grid(row=10, column=1)

btnx3 = Button(f1, padx=16, pady=8, bd=10, fg="black", font=(
    'ariel', 12, 'bold'), width=20, text="???", bg="powder blue", command=qexit)
btnx3.grid(row=10, column=2)

btnprice = Button(f1, padx=16, pady=8, bd=10, fg="black", font=(
    'ariel', 12, 'bold'), width=20, text="Save Settings", bg="powder blue", command=save_settings)
btnprice.grid(row=10, column=3)

console = ScrolledText.ScrolledText(f1, width=40, state='disabled')
console.configure(font='TkFixedFont')
console.grid(row=6, column=4, rowspan=5, columnspan=2, sticky='w')

text_handler = TextHandler(console)
logging.basicConfig(filename='app_log.txt',
                    level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
# Add the handler to logger
logger = logging.getLogger()
logger.addHandler(text_handler)

initialize_agent(logger)


if __name__ == "__main__":
    root.lift()
    root.mainloop()


# %%
