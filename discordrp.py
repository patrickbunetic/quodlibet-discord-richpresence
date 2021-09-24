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
DEFAULT_TCURRENT = ""
DEFAULT_BCURRENT = ""
DEFAULT_TPATTERN = "<title>"
DEFAULT_BPATTERN = "<artist><album| - <album>>"

plugin_config = PluginConfig("discordrp")
defaults = plugin_config.defaults
defaults.set("clientid",DEFAULT_CLIENTID)
defaults.set("topcurrent","")
defaults.set("botcurrent","")
defaults.set("toppattern",DEFAULT_TPATTERN)
defaults.set("botpattern",DEFAULT_BPATTERN)
    

## QUODLIBET PLUGIN INFO
class DRPC(EventPlugin, PluginConfigMixin):
    PLUGIN_ID = "DiscordNowPlaying"
    PLUGIN_NAME = _("Discord Now Playing")
    REQUIRES_ACTION = True
    
    def __init__(self):
        myprint("initializing "+__name__)

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
        self.RPC = None
        if(self.__enabled):
            self.connect_rpc()

    def connect_rpc(self):
        myprint("Attempting RPC connection")
        if self.__enabled:
            self.RPC = Presence(int(self._clientid))
            try:
                self.RPC.connect()
                myprint("RPC connected")
            except PyPresenceException:
                self.RPC = None
                myprint("RPC not connected (PyPresenceException)")
            except:
                self.RPC = None
                myprint("RPC not connected (General. Connection refused?)")

    def disconnect_rpc(self):
        myprint("Disconnecting RPC")
        # self.RPC.clear()
        self.RPC.close()
        self.RPC = None

    def enabled(self):
        myprint("enabled")
        self.__enabled = True
        self.connect_rpc()
            
            
    def disabled(self):
        myprint("disabled")
        self.__enabled = False
        if self.RPC:
            # self.RPC.clear()
            self.RPC.close()
        self.RPC = None

    def plugin_on_song_started(self, song):
        myprint("on_song_started")
        if self.__enabled and song:
            self.song = song
            self.playing = self.play
            if self.__enabled and self.song:
                if not self.RPC:
                    self.connect_rpc()
                if self.RPC:
            
                    # Get patterns again in case they have changed since last update
                    self.tpattern = plugin_config.get("toppattern")
                    self.bpattern = plugin_config.get("botpattern")
                    
                    self.tcurrent = Pattern(self.tpattern) % song
                    plugin_config.set("topcurrent",self.tcurrent)
                    self.bcurrent = Pattern(self.bpattern) % song
                    plugin_config.set("botcurrent",self.bcurrent)
                
                    start = time.time()
                    end = float(Pattern("<~#length>") % song)
                    end = end + start
                    start = int(start)
                    end = int(end)
                
                    myprint("enabled=="+str(self.__enabled))
                    try:
                        self.RPC.update(state=self.bcurrent,
                                        details=self.tcurrent,
                                        large_image="main",
                                        small_image=self.playing)
                    except PyPresenceException:
                        myprint("Cannot update: PyPresenceException [started]")
                        self.disconnect_rpc()
                    except:
                        myprint("Cannot update [started]")
                        self.disconnect_rpc()
           
            
        
    def plugin_on_paused(self):
        myprint("on_paused")
        self.playing = self.pause
        if self.__enabled and self.song:
            if not self.RPC:
                self.connect_rpc()
            if self.RPC:
                try:
                    self.RPC.update(state=self.bcurrent,
                                    details=self.tcurrent,
                                    large_image="main",
                                    small_image=self.playing)
                except PyPresenceException:
                    myprint("Cannot update: PyPresenceException [paused]")
                    self.disconnect_rpc()
                except:
                    myprint("Cannot update [paused]")
                    self.disconnect_rpc()

    def plugin_on_unpaused(self): 
        myprint("on_unpaused")
        self.playing = self.play
        if self.__enabled and self.song:
            if not self.RPC:
                self.connect_rpc()
            if self.RPC:
                # start = time.time()
                # end = float(Pattern("<~#length>") % self.song)
                # end = end + start
                # start = int(start)
                # end = int(end)
                try:
                    self.RPC.update(state=self.bcurrent,
                                    details=self.tcurrent,
                                    large_image="main",
                                    small_image=self.playing)
                except PyPresenceException:
                    myprint("Cannot update: PyPresenceException [unpaused]")
                    self.disconnect_rpc()
                except:
                    myprint("Cannot update [unpaused]")
                    self.disconnect_rpc()
            
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


    

def myprint(string):
    print("::DiscordRP:: "+string)
