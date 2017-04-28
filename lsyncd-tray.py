#!/usr/bin/env python2.7

import argparse
import subprocess
import wx
import sys
import os


here = os.path.dirname(os.path.realpath(sys.argv[0]))
TRAY_TOOLTIP = 'lsync daemon'
TRAY_ICON_RUNNING = 'lsyncd-tray.png'
TRAY_ICON_STOPPED = 'no-lsyncd-tray.png'


class LsyncDaemon(object):
    def __init__(self, config_file, working_directory=None):
        self.config_file = config_file
        self.working_directory = working_directory \
            or os.path.dirname(config_file)

        self.p = None

    def start(self):
        self.p = subprocess.Popen(
            ['lsyncd', '-nodaemon', self.config_file],
            cwd=self.working_directory)

    def stop(self):
        self.running() and self.p.terminate()
        self.p = None

    def running(self):
        return bool(self.p and (self.p.poll() is None))


class TaskBarIcon(wx.TaskBarIcon):
    def __init__(self, frame, lsyncd):
        self.frame = frame
        self.lsyncd = lsyncd
        super(TaskBarIcon, self).__init__()

        self.icon_running = wx.IconFromBitmap(wx.Bitmap(
            '{}/{}'.format(here, TRAY_ICON_RUNNING)))
        self.icon_stopped = wx.IconFromBitmap(wx.Bitmap(
            '{}/{}'.format(here, TRAY_ICON_STOPPED)))

        self.SetIcon(self.icon_stopped, TRAY_TOOLTIP)
        self.Bind(wx.EVT_TASKBAR_LEFT_DOWN, self.on_left_down)
        self.update_state()

    def get_status(self):
        if self.lsyncd.running():
            status = 'Running'
        else:
            status = 'Stopped'

        return 'Status: {}'.format(status)

    def CreatePopupMenu(self):
        menu = wx.Menu()

        status_item = wx.MenuItem(menu, -1, self.get_status())
        menu.AppendItem(status_item)

        exit_item = wx.MenuItem(menu, -1, 'Exit')
        menu.Bind(wx.EVT_MENU, self.on_exit, id=exit_item.GetId())
        menu.AppendItem(exit_item)

        return menu

    def update_state(self):
        if self.lsyncd.running():
            self.SetIcon(self.icon_running, TRAY_TOOLTIP)
        else:
            self.SetIcon(self.icon_stopped, TRAY_TOOLTIP)

    def on_left_down(self, event):
        if self.lsyncd.running():
            self.lsyncd.stop()
        else:
            self.lsyncd.start()

        self.update_state()

    def on_exit(self, event):
        wx.CallAfter(self.Destroy)
        self.lsyncd.stop()
        self.frame.Close()


class App(wx.App):
    def __init__(self, lsyncd):
        self.lsyncd = lsyncd
        super(App, self).__init__(False)

    def OnInit(self):
        frame = wx.Frame(None)
        self.SetTopWindow(frame)
        TaskBarIcon(frame, self.lsyncd)
        return True


def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        'config_file', metavar='LSYNCD_CONFIG',
        help='Configuration file used to run lsyncd daemon.'
    )
    p.add_argument(
        '--start', dest='start', default=False, action='store_true',
        help='Start daemon immediately.'
    )
    p.add_argument(
        '--wd', dest='working_directory',
        help='Run lsyncd in specified directory. '
        'Otherwise it uses directory with configuration file.'
    )

    args = p.parse_args()

    lsyncd = LsyncDaemon(args.config_file, args.working_directory)
    if args.start:
        lsyncd.start()

    app = App(lsyncd)
    app.MainLoop()


if __name__ == '__main__':
    main()
