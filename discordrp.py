import os
import sys
if os.name == "nt" or sys.platform == "darwin":
    from quodlibet.plugins import PluginNotSupportedError
    raise PluginNotSupportedError

import time

from quodlibet import _
from quodlibet import config, qltk, app
from quodlibet.pattern import Pattern
from quodlibet.plugins import PluginConfigMixin,PluginConfig
from quodlibet.plugins.events import EventPlugin

from gi.repository import GLib, Gio, Gtk

from pypresence import Presence, PyPresenceException


DEFAULT_CLIENTID = -1
# DEFAULT_CID      = -1
DEFAULT_TCURRENT = ""
DEFAULT_BCURRENT = ""
DEFAULT_TPATTERN = "<title>"
DEFAULT_BPATTERN = "<artist><album| - <album>>"

plugin_config = PluginConfig("discordrp")
defaults = plugin_config.defaults
defaults.set("clientid",DEFAULT_CLIENTID)
# defaults.set("cid",DEFAULT_CID)
defaults.set("topcurrent","")
defaults.set("botcurrent","")
defaults.set("toppattern",DEFAULT_TPATTERN)
defaults.set("botpattern",DEFAULT_BPATTERN)
# defaults.set("enabled",0)
# defaults.set("error","disabled")
    

## QUODLIBET PLUGIN INFO
class DRPC(EventPlugin, PluginConfigMixin):
    PLUGIN_ID = "DiscordNowPlaying"
    PLUGIN_NAME = _("Discord Now Playing")
    REQUIRES_ACTION = True
    
    def __init__(self):
        print("initializing "+__name__)

        self.__enabled = False

        self.song = None
        self.pause = "pause_gr"
        self.play = "play_gr"
        self.playing = self.pause

        self._clientid = plugin_config.get("clientid") or DEFAULT_CLIENTID
        self.tpattern = plugin_config.get("toppattern") or DEFAULT_TPATTERN
        self.bpattern = plugin_config.get("botpattern") or DEFAULT_BPATTERN
        self.tcurrent = plugin_config.get("topcurrent") or DEFAULT_TCURRENT
        self.bcurrent = plugin_config.get("botcurrent") or DEFAULT_BCURRENT
        if(self.__enabled):
            plugin_config.set("error","enabled")
            self.RPC = Presence(int(self._clientid))
            try:
                self.RPC.connect()
                print("RPC connected")
            except PyPresenceException:
                self._clientid = 0
                plugin_config.set("clientid",self._clientid)
                self.RPC = None
                print("RPC not connected: PyPresenceException")
        else:
            self.RPC = None
            print("RPC not connected: not enabled")

    def enabled(self):
        print("enabled")
        self.__enabled = True
        self.RPC = Presence(int(self._clientid))
        try:
            self.RPC.connect()
            print("successfully enabled")
        except PyPresenceException:
            self._clientid = 0
            plugin_config.set("clientid",self._clientid)
            self.RPC = None            
            print("unsuccessfully enabled: ppe")
        except:
            print("unsuccessfully enabled: other")
            self.RPC = None          
            
    def disabled(self):
        print("disabled")
        self.__enabled = False

    def plugin_on_song_started(self, song):
        print("on_song_started")
        if self.__enabled and song:
            if not self.RPC:
                print("song started, RPC null")
                self.__enabled()
            if self.RPC:
                self.song = song
    
                self.tpattern = plugin_config.get("toppattern")
                self.tcurrent = Pattern(self.tpattern) % song
                plugin_config.set("topcurrent",self.tcurrent)
                
                self.bpattern = plugin_config.get("botpattern")
                self.bcurrent = Pattern(self.bpattern) % song
                plugin_config.set("botcurrent",self.bcurrent)
                
                start = time.time()
                end = float(Pattern("<~#length>") % song)
                end = end + start
                start = int(start)
                end = int(end)
                
                print("enabled=="+str(self.__enabled))
                try:
                    self.RPC.update(state=self.bcurrent,
                                    details=self.tcurrent,
                                    large_image="main",
                                    small_image=self.playing)
                except PyPresenceException:
                    print("error, cannot update [start]")
        else:
            print("not enabled, nothing to send")
           
            
        
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
        idtext = plugin_config.get("clientid")
        idbox.set_text(idtext)
        table.attach(idbox, 1, 3, 0, 1, xoptions=Gtk.AttachOptions.FILL)
        def _clientid_changed(entry):
            self._clientid = entry.get_text()
            try:
                temp = int(self._clientid)
                plugin_config.set("clientid",self._clientid)
            except ValueError:
                plugin_config.set("clientid",DEFAULT_CLIENTID)
        idbox.connect('changed', _clientid_changed)

        lbl = Gtk.Label(label=_("Top Pattern"))
        lbl.set_alignment(xalign=1.0, yalign=0.5)
        table.attach(lbl, 0, 1, 1, 2, xoptions=Gtk.AttachOptions.FILL)

        tpbox = Gtk.Entry()
        tpbox.set_text(plugin_config.get("toppattern"))
        table.attach(tpbox, 1, 3, 1, 2, xoptions=Gtk.AttachOptions.FILL)
        def _tpattern_changed(entry):
            text = entry.get_text()
            plugin_config.set("toppattern",text)
        tpbox.connect('changed', _tpattern_changed)

        lbl = Gtk.Label(label=_("Bottom Pattern"))
        lbl.set_alignment(xalign=1.0, yalign=0.5)
        table.attach(lbl, 0, 1, 2, 3, xoptions=Gtk.AttachOptions.FILL)\

        bpbox = Gtk.Entry()
        bpbox.set_text(plugin_config.get("botpattern"))
        table.attach(bpbox, 1, 3, 2, 3, xoptions=Gtk.AttachOptions.FILL)
        def _bpattern_changed(entry):
            text = entry.get_text()
            plugin_config.set("botpattern",text)
        bpbox.connect('changed', _bpattern_changed)

        vb.pack_start(table, True, True, 2)
        return vb
