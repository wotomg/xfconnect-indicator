#!/usr/bin/env python3

'''
---------------------------------------------------------------
Xfconnect-indicator is an AppIndicator for Kdeconnect in xfce environment.
version 0.4.1
---------------------------------------------------------------
'''

import gi
import dbus
import os
import signal
import time
import datetime

from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
try:
    gi.require_version('AppIndicator3', '0.1')
    from gi.repository import AppIndicator3 as appindicator
except ImportError:
    gi.require_version('AyatanaAppIndicator3', '0.1')
    from gi.repository import AyatanaAppIndicator3 as appindicator

gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")

from gi.repository import Gdk as gdk
from gi.repository import Gtk as gtk

# Set to True to get console output control
DEBUG=False

APPINDICATOR_NAME = 'Xfceconnect-indicator'

class indicatorObject:
    def __init__(self, icon_base):
        self.indicator = appindicator.Indicator.new(APPINDICATOR_NAME, os.path.abspath(icon_base), appindicator.IndicatorCategory.APPLICATION_STATUS)
        if DEBUG : print(self.indicator.get_id()) # Debug
        self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
        self.indicator.set_title('Xfconnect')
        get_menu = build_menu_indicator()
        self.main_menu = get_menu[0]
        self.configureItem = get_menu[1]
        self.devices = {}
        self.indicator.set_menu(self.main_menu)
        
        kdecon_get_devices(self)

    def set_icon(self,icon):
        self.indicator.set_icon_full(icon,'')


class signalCatcher():
    def __init__(self):
        bus.add_signal_receiver(handler_function=echoSignal, dbus_interface = 'org.kde.kdeconnect.device', signal_name = 'reachableChanged')
        bus.add_signal_receiver(handler_function=echoSignal, dbus_interface = 'org.kde.kdeconnect.daemon', signal_name = 'deviceListChanged')
        bus.add_signal_receiver(handler_function=echoSignal, dbus_interface = 'org.kde.kdeconnect.device', signal_name = 'nameChanged')
        bus.add_signal_receiver(handler_function=echoSignal, dbus_interface = 'org.kde.kdeconnect.device.battery', signal_name = 'refreshed')
        bus.add_signal_receiver(handler_function=echoSignal, dbus_interface = 'org.kde.kdeconnect.device', signal_name = 'pluginsChanged')
        bus.add_signal_receiver(handler_function=echoSignal, dbus_interface = 'org.kde.kdeconnect.device.photo', signal_name = 'photoReceived')
        bus.add_signal_receiver(handler_function=echoSignal, dbus_interface = 'org.kde.kdeconnect.device.sftp', signal_name = 'mounted')
        bus.add_signal_receiver(handler_function=echoSignal, dbus_interface = 'org.kde.kdeconnect.device.sftp', signal_name = 'unmounted')


def build_menu_indicator():
    menu = gtk.Menu()
    img_configure = gtk.Image.new_from_icon_name('preferences-other', gtk.IconSize.MENU)
    item_configure = gtk.ImageMenuItem(image=img_configure, label='Configure')
    item_configure.connect('activate', kdecon_configure)
    img_quit = gtk.Image.new_from_icon_name('gtk-quit', gtk.IconSize.MENU)
    item_quit = gtk.ImageMenuItem(image=img_quit, label='Quit')
    item_quit.connect('activate', quit)
    menu.append(item_configure)
    menu.append(gtk.SeparatorMenuItem())
    menu.append(item_quit)
    return [menu,item_configure]


def kdecon_get_devices(indicator):
    # DBus to get devices
    obj = 'org.kde.kdeconnect.daemon'
    path = '/modules/kdeconnect'
    iface = 'org.kde.kdeconnect.daemon'
    dbus_object = bus.get_object(obj,path)
    dbus_interface = dbus.Interface(dbus_object, iface)
    dev = dbus_interface.deviceNames()
    
    are_devices_connected = False

    for key in list(indicator.devices.keys()):
        if not key in dev.keys() or not device_get_property(key,'isTrusted'):
            indicator.devices[key]['item'].destroy()
            del indicator.devices[key]
    
    for key in dev.keys():
        percent=' '
        chrg = '(disabled)'
        charging = None
        charge = ''
        mounted = False
        
        name = dev[key]
        connected = device_get_property(key,'isReachable')
        trusted = device_get_property(key,'isTrusted')
 
        if trusted:
            are_devices_connected = are_devices_connected or connected
            if key in indicator.devices:
                item_device = indicator.devices[key]['item']
                device_menu = indicator.devices[key]['submenu']
                item_battery = indicator.devices[key]['item_battery']
                item_browse = indicator.devices[key]['item_browse']
                item_unmount = indicator.devices[key]['item_unmount']
                item_browse_menu = indicator.devices[key]['item_browse_menu']
                item_ring = indicator.devices[key]['item_ring']
                item_send_file = indicator.devices[key]['item_send_file']
                item_share_text = indicator.devices[key]['item_share_text']
                item_photo = indicator.devices[key]['item_photo']
            else:
                indicator.devices[key] = {}
                device_type = device_get_property(key, 'type')
                if device_type == 'tablet':
                    img_device = gtk.Image.new_from_icon_name('tablet', gtk.IconSize.MENU)
                elif device_type == 'desktop':
                    img_device = gtk.Image.new_from_icon_name('computer', gtk.IconSize.MENU)
                else :
                    img_device = gtk.Image.new_from_icon_name('stock_cell-phone', gtk.IconSize.MENU)
                item_device = gtk.ImageMenuItem(image=img_device, label=name)
                device_menu = gtk.Menu()
                item_device.set_submenu(device_menu)
                # Battery submenu item
                img_battery = gtk.Image.new_from_icon_name('battery', gtk.IconSize.MENU)
                item_battery = gtk.ImageMenuItem(image=img_battery, label='Battery: ')
                
                # Browse submenu item #######
                img_browse = gtk.Image.new_from_icon_name('folder', gtk.IconSize.MENU)
                item_browse = gtk.ImageMenuItem(image=img_browse, label='Browse')
                item_browse.connect('activate', browse, key)
                
                img_unmount = gtk.Image.new_from_icon_name('emblem-unmounted', gtk.IconSize.MENU)
                item_unmount = gtk.ImageMenuItem(image=img_unmount, label='unmount')
                item_unmount.connect('activate', unmount, key)
                
                img_browse_menu = gtk.Image.new_from_icon_name('folder', gtk.IconSize.MENU)
                item_browse_menu = gtk.ImageMenuItem(image=img_browse_menu, label='Browse')
                browse_menu = gtk.Menu()
                item_browse_menu.set_submenu(browse_menu)

                # Ring submenu item
                img_ring = gtk.Image.new_from_icon_name('stock_volume', gtk.IconSize.MENU)
                item_ring = gtk.ImageMenuItem(image=img_ring, label='Ring device')
                item_ring.connect('activate', ring, key)
                # Send file submenu item
                img_send_file = gtk.Image.new_from_icon_name('text-x-generic', gtk.IconSize.MENU)
                item_send_file = gtk.ImageMenuItem(image=img_send_file, label='Send file')
                item_send_file.connect('activate', file_chooser, key)
                # Share text submenu item
                img_share_text = gtk.Image.new_from_icon_name('gtk-paste', gtk.IconSize.MENU)
                item_share_text = gtk.ImageMenuItem(image=img_share_text, label='Share clipboard')
                item_share_text.connect('activate', share_text, key)
                # Photo submenu item
                img_photo = gtk.Image.new_from_icon_name('camera-photo', gtk.IconSize.MENU)
                item_photo = gtk.ImageMenuItem(image=img_photo, label='Take photo')
                item_photo.connect('activate', take_foto_dialog, key, name)
                # SMS submenu
                img_sms = gtk.Image.new_from_icon_name('dialog-messages', gtk.IconSize.MENU)
                item_sms = gtk.ImageMenuItem(image=img_sms, label='SMS Messages...')
                item_sms.connect('activate', kdecon_sms)
                
                indicator.main_menu.insert(item_device, 1)
                device_menu.append(item_battery)
                device_menu.append(item_browse_menu)
                browse_menu.append(item_browse)
                browse_menu.append(item_unmount)
                device_menu.append(item_ring)
                device_menu.append(item_send_file)
                device_menu.append(item_share_text)
                device_menu.append(item_photo)
                device_menu.append(item_sms)
   
            if connected :
                mod_battery = device_get_method(key, 'hasPlugin', None, 'kdeconnect_battery') and  device_get_method(key, 'isPluginEnabled', None, 'kdeconnect_battery')
                mod_sftp = device_get_method(key, 'hasPlugin', None, 'kdeconnect_sftp') and device_get_method(key, 'isPluginEnabled',None, 'kdeconnect_sftp')
                mod_ring =  device_get_method(key, 'hasPlugin', None, 'kdeconnect_findmyphone') and device_get_method(key, 'isPluginEnabled',None, 'kdeconnect_findmyphone')
                mod_share =  device_get_method(key, 'hasPlugin', None, 'kdeconnect_share') and device_get_method(key, 'isPluginEnabled',None, 'kdeconnect_share')
                mod_clipboard =  device_get_method(key, 'hasPlugin', None, 'kdeconnect_clipboard') and device_get_method(key, 'isPluginEnabled',None, 'kdeconnect_clipboard')
                mod_photo =  device_get_method(key, 'hasPlugin', None, 'kdeconnect_photo') and device_get_method(key, 'isPluginEnabled',None, 'kdeconnect_photo')

                # if battery module is loaded...
                if mod_battery :
                    charge = device_get_property(key, 'charge', 'battery')
                    charging = device_get_property(key, 'isCharging', 'battery')
                    
                    if charging :
                        chrg = '(charging)'
                    else:
                        chrg = '(wasting)'
                        
                    if charge < 0:
                        mod_battery = False
                        chrg = ''
                        charge = ''
                # if sftp module is loaded and check if device filesystem is mounted or not
                if mod_sftp:
                    mounted = device_get_method(key, 'isMounted' , 'sftp')

                item_battery.set_label('Battery: '+str(charge)+percent+chrg) # Sets the label of battery submenu item 

                item_battery.set_sensitive(False)
                item_sensitive(item_browse_menu, mod_sftp)
                item_sensitive(item_browse, mod_sftp)
                item_sensitive(item_unmount, mounted)
                item_sensitive(item_ring, mod_ring)
                item_sensitive(item_send_file, mod_share)
                item_sensitive(item_share_text, mod_clipboard)
                item_sensitive(item_photo, mod_photo)
                
            indicator.main_menu.show_all()
            item_sensitive(item_device,connected) # State of clickabilty of device menu item
            indicator.devices[key]['name'] = name 
            indicator.devices[key]['item'] = item_device
            indicator.devices[key]['active'] = connected
            indicator.devices[key]['submenu'] = device_menu
            indicator.devices[key]['item_battery'] = item_battery
            indicator.devices[key]['item_browse_menu'] = item_browse_menu
            indicator.devices[key]['item_browse'] = item_browse
            indicator.devices[key]['item_unmount'] = item_unmount
            indicator.devices[key]['item_ring'] = item_ring
            indicator.devices[key]['item_send_file'] = item_send_file
            indicator.devices[key]['item_share_text'] = item_share_text
            indicator.devices[key]['item_photo'] = item_photo

            

    if are_devices_connected :
        indicator.set_icon('smartphoneconnected')
    else:
        indicator.set_icon('smartphone-disconnected')


def device_get_property (dev, prop, part=None):
    obj = 'org.kde.kdeconnect.daemon'
    path = '/modules/kdeconnect/devices/'+dev
    iface = 'org.kde.kdeconnect.device'
    if part:
        path = path+'/'+part
        iface = iface+'.'+part
        
    dbus_object = bus.get_object(obj, path) 
    dbus_interface = dbus.Interface(dbus_object, 'org.freedesktop.DBus.Properties')
    prop_value = dbus_interface.Get(iface, prop)
    return prop_value

## Get methods dinamically. meth is the method, part is the part of path and iface, val
def device_get_method(dev, meth, part=None, val=None):
    obj = 'org.kde.kdeconnect.daemon'
    path = '/modules/kdeconnect/devices/'+dev
    iface = 'org.kde.kdeconnect.device'
    if  part :
        iface = iface+'.'+part
        path = path+"/"+part

    dbus_object = bus.get_object(obj,path)
    method = dbus_object.get_dbus_method(meth,iface)
    return method(val)



# Function for browse device file system
def browse(item, dev): 
    obj = 'org.kde.kdeconnect'
    path = '/modules/kdeconnect/devices/'+dev+'/sftp'
    try: # Mounting sftp using DBus
        dbus_object = bus.get_object(obj, path) 
        if not dbus_object.isMounted():
            dbus_object.mountAndWait() 
            time.sleep(0.15)
        mountpoint = dbus_object.mountPoint()
    except Exception as Argument:
        timestamp = str(datetime.datetime.now())+" "
        f = open("/tmp/xfconnect.log", "a") 
        f.write(timestamp+str(Argument)+'\n') 
        f.close()
        
    browser_obj = 'org.xfce.Thunar'
    browser_path = '/org/xfce/FileManager'
    browser_iface = 'org.xfce.FileManager'
    try: # opening mount point in Thunar using DBus
        browser_object = bus.get_object(browser_obj, browser_path)
        browser_interface = dbus.Interface(browser_object, browser_iface)
        browser_interface.DisplayFolder(mountpoint, '', '')
    except Exception as Argument:
        timestamp = str(datetime.datetime.now())+" "
        f = open("/tmp/xfconnect.log", "a") 
        f.write(timestamp+str(Argument)+'\n') 
        f.close()

def unmount(item, dev):
    obj = 'org.kde.kdeconnect'
    path = '/modules/kdeconnect/devices/'+dev+'/sftp'
    try: # Mounting sftp using DBus
        dbus_object = bus.get_object(obj, path) 
        if dbus_object.isMounted():
            dbus_object.unmount() 
            time.sleep(0.15)
    except Exception as Argument:
        timestamp = str(datetime.datetime.now())+" "
        f = open("/tmp/xfconnect.log", "a") 
        f.write(timestamp+str(Argument)+'\n') 
        f.close()

# Function ring remote device
def ring(item, dev):
    obj = 'org.kde.kdeconnect.daemon'
    path = '/modules/kdeconnect/devices/'+dev+'/findmyphone'
    try: # Ring the remote device with DBus
        dbus_object = bus.get_object(obj, path) 
        dbus_object.ring()
    except Exception as Argument:
        timestamp = str(datetime.datetime.now())+" "
        f = open("/tmp/xfconnect.log", "a") 
        f.write(timestamp+str(Argument)+'\n') 
        f.close()


# Function to open file select dialog
def file_chooser(item, dev):
    chooser = gtk.FileChooserDialog(title="Select files to send", parent=None, action=gtk.FileChooserAction.OPEN)
    # Changing directory to $HOME
    chooser.set_current_folder(os.environ['HOME'])
    chooser.set_select_multiple(True)
    chooser.add_button("_Open", gtk.ResponseType.OK)
    chooser.add_button("_Cancel", gtk.ResponseType.CANCEL)
    chooser.set_default_response(gtk.ResponseType.OK)

    if chooser.run() == gtk.ResponseType.OK:
        file_names = chooser.get_uris()
        chooser.destroy()
        for f in file_names:
            send_file(dev,f)
    else:
        chooser.destroy()


# Function for send files to remote device
def send_file(dev, file_to_send):
    if DEBUG : print(file_to_send) # Debug
    obj = 'org.kde.kdeconnect.daemon'
    path = '/modules/kdeconnect/devices/'+dev+'/share'
    try: # Sending files with DBus
        dbus_object = bus.get_object(obj, path) 
        dbus_object.shareUrl(file_to_send)
    except Exception as Argument:
        timestamp = str(datetime.datetime.now())+" "
        f = open("/tmp/xfconnect.log", "a") 
        f.write(timestamp+str(Argument)+'\n') 
        f.close()


# Function for send text (clipboard) to device
def share_text(item, dev):
    cb = gtk.Clipboard.get(gdk.SELECTION_CLIPBOARD)
    obj = 'org.kde.kdeconnect.daemon'
    path = '/modules/kdeconnect/devices/'+dev+'/share'
    try: # Sharing text with DBus
        dbus_object = bus.get_object(obj, path) 
        dbus_object.shareText(cb.wait_for_text())
    except Exception as Argument:
        timestamp = str(datetime.datetime.now())+" "
        f = open("/tmp/xfconnect.log", "a") 
        f.write(timestamp+str(Argument)+'\n') 
        f.close()


def take_foto_dialog(item, dev, name):
    
    file_photo=""
    obj = 'org.kde.kdeconnect.daemon'
    path = '/modules/kdeconnect/devices/'+dev+'/photo'

    download_directory=GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD)
    n=0
    first=("picture_%03i" % n)
    while os.path.exists(download_directory+"/"+first+"-"+name+".jpg"):
        n += 1
        first=("picture_%03i" % n)
    file_photo=(first+"-"+name+".jpg")
    whole_path=download_directory+"/"+file_photo
    
    chooser = gtk.FileChooserDialog(title="Select files to send", parent=None, action=gtk.FileChooserAction.SAVE)
    chooser.set_do_overwrite_confirmation(True)
    chooser.add_button("_Save", gtk.ResponseType.ACCEPT)
    chooser.add_button("_Cancel", gtk.ResponseType.CANCEL)
    chooser.set_default_response(gtk.ResponseType.ACCEPT)
    chooser.set_current_folder(download_directory)
    chooser.set_current_name(file_photo)

    if chooser.run() == gtk.ResponseType.ACCEPT:
        file_photo=chooser.get_uris()[0].replace('file://','') 
        try: # Sending files with DBus
            print(file_photo)
            dbus_object = bus.get_object(obj, path) 
            dbus_object.requestPhoto(whole_path)
            chooser.destroy()
            if DEBUG: print ("Taking picture from  "+dev+": "+name)
        except Exception as Argument:
            print("error")
            timestamp = str(datetime.datetime.now())+" "
            f = open("/tmp/xfconnect.log", "a") 
            f.write(timestamp+str(Argument)+'\n') 
            f.close()
    else:
        if DEBUG: print ("Canceled...  "+name)
        chooser.destroy()


def item_sensitive(item, connected):
    if connected :
        item.set_sensitive(True)
    else:
        item.set_sensitive(False)


def kdecon_configure(self):
    os.system("kdeconnect-settings")

def kdecon_sms(self):
    os.system("kdeconnect-sms")
            
def echoSignal(*args, **kwargs):
    #if args[0] : print(args[0])
    kdecon_get_devices(indicatorApp)


def quit(source):
    gtk.main_quit()


if __name__ == "__main__":
    # Changing directory to the Script root
    PATH_SCRIPT= os.path.dirname(os.path.realpath(__file__))
    os.chdir(PATH_SCRIPT)
    
    # Stting to catch signals and DBus signals
    DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    mysignals = signalCatcher()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    indicatorApp = indicatorObject('smartphone-disconnected') # Creating indicator object
    gtk.main() # Gtk mainloop





