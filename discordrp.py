import os
import sys
if os.name == "nt" or sys.platform == "darwin":
    from quodlibet.plugins import PluginNotSupportedError
    raise PluginNotSupportedError

import time

from quodlibet import _
from quodlibet import config, qltk, app
from quodlibet.pattern import Pattern
from quodlibet.plugins import PluginConfigMixin
from quodlibet.plugins.events import EventPlugin

from gi.repository import GLib, Gio, Gtk

from pypresence import Presence, PyPresenceException

## QUODLIBET PLUGIN INFO
class DRPC(EventPlugin, PluginConfigMixin):
    PLUGIN_ID = "DiscordNowPlaying"
    PLUGIN_NAME = _("Discord Now Playing")
    REQUIRES_ACTION = True

    DEFAULT_CLIENTID = ""
    DEFAULT_CID      = -1
    DEFAULT_TCURRENT = ""
    DEFAULT_BCURRENT = ""
    DEFAULT_TPATTERN = "<title>"
    DEFAULT_BPATTERN = "<artist><album| - <album>>"

    c_clientid = __name__ + '_clientid'
    c_cid      = __name__ + '_cid'
    c_tcurrent = __name__ + '_tcurrent'
    c_bcurrent = __name__ + '_bcurrent'
    c_tpattern = __name__ + '_tpattern'
    c_bpattern = __name__ + '_bpattern'

    c_enabled  = __name__ + '_enabled'

    c_error    = __name__ + '.error'

    # clientid = 0

    def __init__(self):
        # try:
        #     self.clientid = config.get('plugins', self.c_clientid)
        # except:
        #     self.clientid = DEFAULT_CLIENTID
        #     config.set('plugins', c_clientid, DEFAULT_CLIENTID)

        print("initializing"+__name__)

        self.song = None
        self.pause = "pause_gr"
        self.play = "play_gr"
        self.playing = self.pause
        
        try:
            self._cid = config.get('plugins', self.c_cid)
        except:
            print("Error: "+_cid)
            self._cid = self.DEFAULT_CID
            config.set('plugins', self.c_cid, self._cid)
        
        try:
            self.tpattern = config.get('plugins', self.c_tpattern)
        except:
            print("Error: "+tpattern)
            self.tpattern = self.DEFAULT_TPATTERN
            config.set('plugins', self.c_tpattern, self.tpattern)

        try:
            self.bpattern = config.get('plugins', self.c_bpattern)
        except:
            print("Error: "+bpattern)
            self.bpattern = self.DEFAULT_BPATTERN
            config.set('plugins', self.c_bpattern, self.bpattern)

        try:
            self._enabled = config.getint('plugins', self.c_enabled)
        except:
            print("Error: "+_enabled)
            self._enabled = 0
            config.set('plugins', self.c_enabled, self._enabled)
            config.set('plugins', self.c_error, "not enabled")

        # try:
        #     self.tcurrent = int(config.get('plugins', self.c_tcurrent))
        # except:
        #     self.tcurrent = self.DEFAULT_TCURRENT
        #     config.set('plugins', self.c_tcurrent, self.tcurrent)

        # try:
        #     self.bcurrent = int(config.get('plugins', self.c_bcurrent))
        # except:
        #     self.bcurrent = self.DEFAULT_BCURRENT
        #     config.set('plugins', self.c_bcurrent, self.bcurrent)

        if(self._enabled):
            config.set('plugins', self.c_error, "enabled")
            self.RPC = Presence(int(self._cid))
            try:
                self.RPC.connect()
                print("RPC connected")
            except PyPresenceException:
                self._cid = 0
                config.set('plugins', self.c_cid, self._cid)
                self.RPC = None
                print("RPC not connected: PyPresenceException")
        else:
            self.RPC = None
            print("RPC not connected: not enabled")

    def enabled(self):
        print("enabled")
        self._enabled = 1
        config.set('plugins', self.c_enabled, 1)
        self.RPC = Presence(int(self._cid))
        try:
            self.RPC.connect()
            print("successfully enabled")
        except PyPresenceException:
            self._cid = 0
            config.set('plugins', self.c_cid, self._cid)
            self.RPC = None            
            print("unsuccessfully enabled: ppe")
        except:
            print("unsuccessfully enabled: other")
            self.RPC = None          
            
    def disabled(self):
        print("enabled")
        self._enabled = 0
        config.set('plugins', self.c_enabled, 0)
        # try:
        #     self.RPC.close()
        # except PyPresenceException:
        #     self.RPC = None

    def plugin_on_song_started(self, song):
        # if song and self.RPC:
        # self._enabled = config.get('plugins', self.c_enabled)
        # config.set('plugins', self.c_error, self._enabled)
        # config.set('plugins', self.c_error, "Update")
        print("on_song_started")
        if self._enabled == 1 and song:
            if not self.RPC:
                print("song started, RPC null")
                self.enabled()
            if self.RPC:
                self.song = song
                
                self.tpattern = config.get('plugins', self.c_tpattern)
                self.tcurrent = Pattern(self.tpattern) % song
                config.set('plugins', self.c_tcurrent, self.tcurrent)
                
                self.bpattern = config.get('plugins', self.c_bpattern)
                self.bcurrent = Pattern(self.bpattern) % song
                config.set('plugins', self.c_bcurrent, self.bcurrent)
                
                start = time.time()
                end = float(Pattern("<~#length>") % song)
                end = end + start
                start = int(start)
                end = int(end)
                
                print("enabled=="+str(self._enabled))
                try:
                    self.RPC.update(state=self.bcurrent,
                                    details=self.tcurrent,
                                    large_image="main",
                                    small_image=self.playing)
                except PyPresenceException:
                    # config.set('plugins', self.c_error, "Cannot Update")
                    print("error, cannot update [start]")
            
        
    def plugin_on_paused(self):
        print("on_paused")
        self.playing = self.pause
        
        try:
            if self.RPC:
                self.RPC.update(state=self.bcurrent,
                                details=self.tcurrent,
                                large_image="main",
                                small_image=self.playing)
        except PyPresenceException:
            print("error, cannot update [pause]")

    def plugin_on_unpaused(self):
        
        print("on_unpaused")
        self.playing = self.play

        # start = time.time()
        # end = float(Pattern("<~#length>") % self.song)
        # end = end + start
        # start = int(start)
        # end = int(end)
        
        try:
            if self.RPC:
                self.RPC.update(state=self.bcurrent,
                                details=self.tcurrent,
                                large_image="main",
                                small_image=self.playing)
        except PyPresenceException:
            # config.set('plugins', self.c_error, "Cannot Update")
            print("Cannot update: PyPresenceException")
        except:
            print("Cannot update")
            
    @classmethod
    def PluginPreferences(self, window):
        vb = Gtk.VBox(spacing=6)
        vb.set_border_width(6)

        table = Gtk.Table(n_rows=3, n_columns=3)
        table.props.expand = False
        table.set_col_spacings(6)
        table.set_row_spacings(6)

        lbl = Gtk.Label(label=_("Client ID:"))
        lbl.set_alignment(xalign=1.0, yalign=0.5)
        table.attach(lbl, 0, 1, 0, 1, xoptions=Gtk.AttachOptions.FILL)

        idbox = Gtk.Entry()
        idtext = config.get('plugins', self.c_cid)
        idbox.set_text(idtext)
        table.attach(idbox, 1, 3, 0, 1, xoptions=Gtk.AttachOptions.FILL)
        def _clientid_changed(entry):
            self._cid = entry.get_text()
            try:
                temp = int(self._cid)
                config.set('plugins', self.c_cid, self._cid)
            except ValueError:
                # self._cid = self.DEFAULT_CID
                config.set('plugins', self.c_cid, self.DEFAULT_CID)
        idbox.connect('changed', _clientid_changed)

        lbl = Gtk.Label(label=_("Top Pattern"))
        lbl.set_alignment(xalign=1.0, yalign=0.5)
        table.attach(lbl, 0, 1, 1, 2, xoptions=Gtk.AttachOptions.FILL)

        tpbox = Gtk.Entry()
        tpbox.set_text(config.get('plugins', self.c_tpattern))
        table.attach(tpbox, 1, 3, 1, 2, xoptions=Gtk.AttachOptions.FILL)
        def _tpattern_changed(entry):
            text = entry.get_text()
            config.set('plugins', self.c_tpattern, text)
        tpbox.connect('changed', _tpattern_changed)

        lbl = Gtk.Label(label=_("Bottom Pattern"))
        lbl.set_alignment(xalign=1.0, yalign=0.5)
        table.attach(lbl, 0, 1, 2, 3, xoptions=Gtk.AttachOptions.FILL)\

        bpbox = Gtk.Entry()     
        bpbox.set_text(config.get('plugins', self.c_bpattern))
        table.attach(bpbox, 1, 3, 2, 3, xoptions=Gtk.AttachOptions.FILL)
        def _bpattern_changed(entry):
            text = entry.get_text()
            config.set('plugins', self.c_bpattern, text)
        bpbox.connect('changed', _bpattern_changed)

        vb.pack_start(table, True, True, 2)
        return vb
