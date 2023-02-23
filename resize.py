import sys
import pygetwindow as gw

def resize(app_name='NIKKE', size=[2560, 1000]):
    app = [app for app in gw.getWindowsWithTitle(app_name) if app.title == app_name][0]
    app.resizeTo(*size)

if __name__ == "__main__":
    args = sys.argv
    default_size = [2560, 1000]
    size = default_size
    if len(args)==1:
        print(f'No arguments provided, using default size of {size[0]}x{size[1]}')
    elif len(args)==3:
        size = [int(args[1]), int(args[2])]
        print(f'Resizing to size of {size[0]}x{size[1]}')
    else:
        print(f'Please use the format of py resize.py [X] [Y], e.g. py resize.py 2560 1000')
        print(f'Invalid arguments provided, using default size of {size[0]}x{size[1]}')
    resize(size=size)