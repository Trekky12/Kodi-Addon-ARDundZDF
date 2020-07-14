# -*- coding: utf-8 -*-
###################################################################################################
#							 util.py - Hilfsfunktionen Kodiversion
#	Modulnutzung: 
#					import resources.lib.util as util
#					PLog=util.PLog;  home=util.home; ...  (manuell od.. script-generiert)
#
#	convert_util_imports.py generiert aus util.py die Zuordnungen PLog=util.PLog; ...
####################################################################################################
# 
#	02.11.2019 Migration Python3 Modul future
#	17.11.2019 Migration Python3 Modul kodi_six + manuelle Anpassungen
# 	
#	Stand 14.07.2020

# Python3-Kompatibilität:
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from kodi_six import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs
# o. Auswirkung auf die unicode-Strings in PYTHON3:
from kodi_six.utils import py2_encode, py2_decode

# Standard:
import os, sys, subprocess
PYTHON2 = sys.version_info.major == 2
PYTHON3 = sys.version_info.major == 3
if PYTHON2:					
	from urllib import quote, unquote, quote_plus, unquote_plus, urlencode, urlretrieve 
	from urllib2 import Request, urlopen, URLError 
	from urlparse import urljoin, urlparse, urlunparse , urlsplit, parse_qs 
elif PYTHON3:				
	from urllib.parse import quote, unquote, quote_plus, unquote_plus, urlencode, urljoin, urlparse, urlunparse, urlsplit, parse_qs  
	from urllib.request import Request, urlopen, urlretrieve
	from urllib.error import URLError
	
# import requests		# kein Python-built-in-Modul, urllib2 verwenden
import datetime as dt	# für xml2srt
import time, datetime
from time import sleep  # PlayVideo

import glob, shutil
from io import BytesIO	# Python2+3 -> get_page (compressed Content), Ersatz für StringIO
import gzip, zipfile
import base64 			# url-Kodierung für Kontextmenüs
import json				# json -> Textstrings
import pickle			# persistente Variablen/Objekte
import re				# u.a. Reguläre Ausdrücke, z.B. in CalculateDuration
import string, textwrap

import shlex			# Parameter-Expansion für subprocess.Popen (os != windows)
	
# Globals
PYTHON2 = sys.version_info.major == 2	# Stammhalter Pythonversion 
PYTHON3 = sys.version_info.major == 3

NAME			= 'ARD und ZDF'
KODI_VERSION 	= xbmc.getInfoLabel('System.BuildVersion')

ADDON_ID      	= 'plugin.video.ardundzdf'
SETTINGS 		= xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME    	= SETTINGS.getAddonInfo('name')
SETTINGS_LOC  	= SETTINGS.getAddonInfo('profile')
ADDON_PATH    	= SETTINGS.getAddonInfo('path')	# Basis-Pfad Addon
ADDON_VERSION 	= SETTINGS.getAddonInfo('version')
PLUGIN_URL 		= sys.argv[0]				# plugin://plugin.video.ardundzdf/
HANDLE			= int(sys.argv[1])

DEBUG			= SETTINGS.getSetting('pref_info_debug')

FANART = xbmc.translatePath('special://home/addons/' + ADDON_ID + '/fanart.jpg')
ICON = xbmc.translatePath('special://home/addons/' + ADDON_ID + '/icon.png')
# Github-Icons zum Nachladen aus Platzgründen
ICON_MAINXL 	= 'https://github.com/rols1/PluginPictures/blob/master/ARDundZDF/TagesschauXL/tagesschau.png?raw=true'

ARDStartCacheTime = 300						# 5 Min.

#---------------------------------------------------------------- 
# prüft addon.xml auf mark - Rückgabe True, False
#	benötigt u.a. für Check der python-Version - falls
#	3.0.0 wird global ADDON_DATA (Modul-Kopf) neu
#	gesetzt - s. check_DataStores
# ADDON_DATA 3.0.0 (Kodi 19 Matrix):
#	../.kodi/userdata/addon_data/plugin.video.ardundzdf
# ADDON_DATA 2.25.0 (Kodi 18 Leia):
#	../.kodi/userdata/ardundzdf_data
# Aufruf von allen Modulen.Köpfen einschl. Haupt-PRG
# 15.05.2020 Codec-Error beim Einlesen in Matrix - Austausch
#	open/read gegen xbmcvfs.File/read
# 
def check_AddonXml(mark):
	ADDON_XML		= os.path.join(ADDON_PATH, "addon.xml")
	xbmc.log("%s --> %s" % ('ARDundZDF', 'check_AddonXml:'), xbmc.LOGNOTICE)
	f = xbmcvfs.File(ADDON_XML)		# Byte-Puffer
	xml_content	= f.readBytes()
	f.close()
	if mark in str(xml_content):
		ADDON_DATA	= os.path.join("%s", "%s", "%s") % (USERDATA, "addon_data", ADDON_ID)
		return True
	else:
		return False

#---------------------------------------------------------------- 
	
USERDATA		= xbmc.translatePath("special://userdata")
ADDON_DATA		= os.path.join("%sardundzdf_data") % USERDATA

if 	check_AddonXml('"xbmc.python" version="3.0.0"'):
	ADDON_DATA	= os.path.join("%s", "%s", "%s") % (USERDATA, "addon_data", ADDON_ID)

M3U8STORE 		= os.path.join("%s/m3u8") % ADDON_DATA
DICTSTORE 		= os.path.join("%s/Dict") % ADDON_DATA
SLIDESTORE 		= os.path.join("%s/slides") % ADDON_DATA
SUBTITLESTORE 	= os.path.join("%s/subtitles") % ADDON_DATA
TEXTSTORE 		= os.path.join("%s/Inhaltstexte") % ADDON_DATA
WATCHFILE		= os.path.join("%s/merkliste.xml") % ADDON_DATA
TEMP_ADDON		= xbmc.translatePath("special://temp")			# Backups

PLAYLIST 		= 'livesenderTV.xml'		# TV-Sender-Logos erstellt von: Arauco (Plex-Forum). 											
ICON_MAIN_POD	= 'radio-podcasts.png'
ICON_MAIN_AUDIO	= 'ard-audiothek.png'
ICON_MAIN_ZDFMOBILE	= 'zdf-mobile.png'
ICON_PHOENIX	= 'phoenix.png'			
ICON_ARTE		= 'icon-arte_kat.png'			

# Github-Icons zum Nachladen aus Platzgründen
ICON_MAINXL 	= 'https://github.com/rols1/PluginPictures/blob/master/ARDundZDF/TagesschauXL/tagesschau.png?raw=true'
BASE_URL 		= 'https://classic.ardmediathek.de'

#----------------------------------------------------------------
# Kodi Matrix: Wechsel   xbmc.LOGNOTICE -> xbmc.LOGINFO - siehe
#	https://forum.kodi.tv/showthread.php?tid=353818&pid=2943669#pid2943669,
#	https://github.com/xbmc/xbmc/compare/master@%7B1day%7D...master
#	https://github.com/i96751414/script.logviewer/blob/matrix/resources/lib/utils.py
# 10.05.2020 Rückwechsel zu LOGNOTICE - LOGINFO klappt nicht mit akt. 
#			Matrix-Build 
# 14.05.2020 dummy = fehlerhafter PLog-Call z.B. pytube-Modul (helpers.py, mixins.py,
#			gefixt). dummy-Ausgabe vorerst belassen (Debug)
# Bei Änderungen check_AddonXml berücksichtigen (xbmc.log direkt)
#
def PLog(msg, dummy=''):
	if DEBUG == 'false':
		return
	
#	if PYTHON3:
#		xbmc.log("%s --> %s" % ('ARDundZDF', msg), xbmc.LOGINFO)	
#	else:
	xbmc.log("%s --> %s" % ('ARDundZDF', msg), xbmc.LOGNOTICE)
	if dummy:		# Debug (s.o.)
		xbmc.log("%s --> %s" % ('PLog_dummy', dummy), xbmc.LOGNOTICE)
		
#---------------------------------------------------------------- 
# 08.04.2020 Konvertierung 3-zeiliger Dialoge in message (Multiline)
#  	Anlass: 23-03-2020 Removal of deprecated features (PR) - siehe:
#	https://forum.kodi.tv/showthread.php?tid=344263&pid=2933596#pid2933596
#	https://github.com/xbmc/xbmc/blob/master/xbmc/interfaces/legacy/Dialog.h
# ok triggert Modus: Dialog().ok, Dialog().yesno()
#
def MyDialog(msg1, msg2='', msg3='', ok=True, cancel='Abbruch', yes='JA', heading=''):
	PLog('MyDialog:')
	
	msg = msg1
	if msg2:							# 3 Zeilen -> Multiline
		msg = "%s\n%s" % (msg, msg2)
	if msg3:
		msg = "%s\n%s" % (msg, msg3)
	if heading == '':
		heading = ADDON_NAME
	
	if ok:								# ok-Dialog
		if PYTHON2:
			return xbmcgui.Dialog().ok(heading=heading, line1=msg)
		else:							# Matrix: line1 -> message
			return xbmcgui.Dialog().ok(heading=heading, message=msg)

	else:								# yesno-Dialog
		if PYTHON2:
			ret = xbmcgui.Dialog().yesno(heading=heading, line1=msg, nolabel=cancel, yeslabel=yes)
		else:							# Matrix: line1 -> message
			ret = xbmcgui.Dialog().yesno(heading=heading, message=msg, nolabel=cancel, yeslabel=yes)
		return ret

#----------------------------------------------------------------
# get_list_indices: Umkehrung von get_items_from_list
#	gleicht die Elemente my_items mit my_list ab
#	und speichert den jew. Index in index_list
#	Rückgabe: Liste der Indices od. []
# Bsp. dialog.multiselect in FilterToolsWork
#
def get_list_indices(my_items, my_list):
	PLog('get_list_indices:')
	
	index_list = []
	for item in my_items:
		if item in my_list:
			index_list.append(my_list.index(item))
	return index_list	
#----------------------------------------------------------------
# get_items_from_list: Umkehrung von get_list_indices
#	ermittelt die items in my_list passend zum
#	jew. Index
#	Rückgabe: Liste der items od. []
# Bsp. dialog.multiselect in FilterToolsWork
#
def get_items_from_list(my_indices, my_list):
	PLog('get_items_from_list:')
	
	item_list = []
	for i in my_indices:
		try:
			if my_list[i]:
				item_list.append(my_list[i])
		except:
			pass
	return item_list	
#---------------------------------------------------------------- 
# Home-Button, Aufruf: item = home(item=item, ID=NAME)
#	Liste item von Aufrufer erzeugt
# 	filterstatus='set' steuert Eintrag im Kontext-Menü
def home(li, ID):												
	PLog('home: ' + ID)	
	if SETTINGS.getSetting('pref_nohome') == 'true':	# keine Homebuttons
		return li
		
	title = u'Zurück zum Hauptmenü %s' % ID
	summary = title										# z.Z. n.w.
	tag =  "Status Ausschluss-Filter: AUS"				# nur ARD und ZDF, nicht Module
	if SETTINGS.getSetting('pref_usefilter') == 'true':	
		tag = tag.replace('AUS','[COLOR blue]EIN[/COLOR]')										
	
	CurSender = Dict("load", 'CurSender')		
	PLog(CurSender)	

	if ID == NAME:		# 'ARD und ZDF'
		name = 'Home : ' + NAME
		fparams="&fparams={}"
		img = R('icon.png') 
		addDir(li=li, label=name, action="dirList", dirID="Main", fanart=img, 
			thumb=img, tagline=tag, filterstatus='set', fparams=fparams)
			
	if ID == 'ARD':
		if SETTINGS.getSetting('pref_use_classic') == 'false':	# Umlabeln für ARD-Suche (Classic)
			ID ='ARD Neu'
					
	if ID == 'ARD':
		img = R('home-ard-classic.png')
		name = 'Home: ' + "ARD Mediathek Classic"
		# CurSender = Dict("load", "CurSender")	# entf.  bei Classic
		fparams="&fparams={'name': '%s', 'sender': '%s'}"	% (quote(name), '')
		addDir(li=li, label=title, action="dirList", dirID="Main_ARD", fanart=img, 
			thumb=img, tagline=tag, filterstatus='set', fparams=fparams)
		
	if ID == 'ARD Neu':			
		img = R('ard-mediathek.png') 
		name = 'Home: ' + "ARD Mediathek"
		CurSender = Dict("load", "CurSender")
		fparams="&fparams={'name': '%s', 'CurSender': '%s'}"	% (quote(name), quote(CurSender))
		addDir(li=li, label=title, action="dirList", dirID="resources.lib.ARDnew.Main_NEW", 
			fanart=img, thumb=img, tagline=tag, filterstatus='', fparams=fparams)
			
	if ID == 'ZDF':
		img = R('zdf-mediathek.png')
		name = 'Home: ' + "ZDF Mediathek"
		fparams="&fparams={'name': '%s'}" % quote(name)
		addDir(li=li, label=title, action="dirList", dirID="Main_ZDF", fanart=img, 
			thumb=img, tagline=tag, filterstatus='', fparams=fparams)
		
	if ID == 'ZDFmobile':
		img = R('zdf-mobile.png')
		name = 'Home :' + "ZDFmobile"
		fparams="&fparams={}"
		addDir(li=li, label=title, action="dirList", dirID="resources.lib.zdfmobile.Main_ZDFmobile", 
			fanart=img, thumb=img, filterstatus='', fparams=fparams)
			
	if ID == 'PODCAST':
		img = R(ICON_MAIN_POD)
		name = 'Home :' + "Radio-Podcasts"
		fparams="&fparams={'name': '%s'}" % quote(name)
		addDir(li=li, label=title, action="dirList", dirID="Main_POD", fanart=img, 
			thumb=img, filterstatus='set', fparams=fparams)
			
	if ID == 'ARD Audiothek':
		img = R(ICON_MAIN_AUDIO)
		name = 'Home :' + "ARD Audiothek"
		fparams="&fparams={'title': '%s'}" % quote(name)
		addDir(li=li, label=title, action="dirList", dirID="AudioStart", fanart=img, 
			thumb=img, tagline=tag, filterstatus='', fparams=fparams)
			
	if ID == '3Sat':
		img = R('3sat.png')
		name = 'Home :' + "3Sat"
		fparams="&fparams={'name': '%s'}" % quote(name)
		addDir(li=li, label=title, action="dirList", dirID="resources.lib.my3Sat.Main_3Sat", fanart=img, 
			thumb=img, filterstatus='', fparams=fparams)
			
	if ID == 'FUNK':
		img = R('funk.png')
		name = 'Home :' + "FUNK"
		fparams="&fparams={}"
		addDir(li=li, label=title, action="dirList", dirID="resources.lib.funk.Main_funk", fanart=img, 
			thumb=img, filterstatus='set', fparams=fparams)
			
	if ID == 'Kinderprogramme':
		img = R('childs.png')
		name = 'Home :' + ID
		fparams="&fparams={}"
		addDir(li=li, label=title, action="dirList", dirID="resources.lib.childs.Main_childs", fanart=img, 
			thumb=img, filterstatus='', fparams=fparams)

	if ID == 'TagesschauXL':
		img = ICON_MAINXL		# github
		name = 'Home :' + ID
		fparams="&fparams={}"
		addDir(li=li, label=title, action="dirList", dirID="resources.lib.TagesschauXL.Main_XL", fanart=img, 
			thumb=img, filterstatus='', fparams=fparams)
			
	if ID == 'phoenix':
		img = R(ICON_PHOENIX)
		name = 'Home :' + ID
		fparams="&fparams={}"
		addDir(li=li, label=title, action="dirList", dirID="resources.lib.phoenix.Main_phoenix", fanart=img, 
			thumb=img, filterstatus='', fparams=fparams)

	if ID == 'arte':
		img = R(ICON_ARTE)
		name = 'Home :' + ID
		fparams="&fparams={}"
		addDir(li=li, label=title, action="dirList", dirID="resources.lib.arte.Main_arte", fanart=img, 
			thumb=img, filterstatus='', fparams=fparams)

	return li
	 
#---------------------------------------------------------------- 
#   data-Verzeichnis liegt 2 Ebenen zu hoch, funktioniert aber.
#	03.04.2019 data-Verzeichnis des Addons:
#  		Check /Initialisierung / Migration
# 	27.05.2019 nur noch Check (s. Forum:
#		www.kodinerds.net/index.php/Thread/64244-RELEASE-Kodi-Addon-ARDundZDF/?pageNo=23#post528768
#	Die Funktion checkt bei jedem Aufruf des Addons data-Verzeichnis einschl. Unterverzeichnisse 
#		auf Existenz und bei Bedarf neu an. User-Info nur noch bei Fehlern (Anzeige beschnittener 
#		Verzeichnispfade im Kodi-Dialog nur verwirend).
#	13.03.2020 abhängig von check_AddonXml wird bei der Matrix-Version des Addons
#		das data-Verzeichnis für Kodi korrekt angelegt im Verz.:
#		../.kodi/userdata/addon_data/plugin.video.ardundzdf/
#	05.05.2020 zusätzlich wird die Filterliste angelegt falls noch nicht existent 
#				(mit den beiden bisher verwendeten Begriffen) - korresp. Datei:
#				filter_set (FILTER_SET).  
#
def check_DataStores():
	PLog('check_DataStores:')
	store_Dirs = ["Dict", "slides", "subtitles", "Inhaltstexte", 
				"m3u8"]
	filterfile = os.path.join("%s/filter.txt") % ADDON_DATA
	filter_pat =  "<filter>\nhörfassung\naudiodeskription\nuntertitel\ngebärdensprache\n</filter>\n"
				
	# Check 
	#	falls ein Unterverz. fehlt, erzeugt make_newDataDir alle
	#	Datenverz. oder einzelne fehlende Verz. neu.
	ok=True	
	for Dir in store_Dirs:						# Check Unterverzeichnisse
		Dir_path = os.path.join("%s/%s") % (ADDON_DATA, Dir)
		if os.path.isdir(Dir_path) == False:	
			PLog('Datenverzeichnis fehlt: %s' % Dir_path)
			ok = False
			break
	
	if ok and os.path.isfile(filterfile):
		return 'OK %s '	% ADDON_DATA			# Verz. + Filterdatei existieren - OK
	else:
		# neues leeres Verz. mit Unterverz. anlegen / einzelnes fehlendes 
		#	Unterverz. anlegen / Filterdatei anlegen
		ret = make_newDataDir(store_Dirs, filterfile, filter_pat)	
		if ret == True:						# ohne Dialog
			msg1 = 'Datenverzeichnis angelegt - Details siehe Log'
			msg2=''; msg3=''
			PLog(msg1)
			# MyDialog(msg1, msg2, msg3)  # OK ohne User-Info
			return 	'OK - %s' % msg1
		else:
			msg1 = "Fehler beim Anlegen des Datenverzeichnisses:" 
			msg2 = ret
			msg3 = 'Bitte Kontakt zum Entwickler aufnehmen'
			PLog("%s\n%s" % (msg2, msg3))	# Ausgabe msg1 als exception in make_newDataDir
			MyDialog(msg1, msg2, msg3)
			return 	'Fehler: Datenverzeichnis konnte nicht angelegt werden'
				
#---------------------------
# ab Version 1.5.6
# 	erzeugt neues leeres Datenverzeichnis oder fehlende Unterverzeichnisse
def  make_newDataDir(store_Dirs, filterfile, filter_pat):
	PLog('make_newDataDir:')
				
	if os.path.isdir(ADDON_DATA) == False:		# erzeugen, falls noch nicht vorh.
		try:  
			os.mkdir(ADDON_DATA)
		except Exception as exception:
			ok=False
			PLog(str(exception))
			return str(exception)		
				
	ok=True
	for Dir in store_Dirs:						# Unterverz. erzeugen
		Dir_path = os.path.join("%s/%s") % (ADDON_DATA, Dir)	
		if os.path.isdir(Dir_path) == False:	
			try:  
				os.mkdir(Dir_path)
			except Exception as exception:
				ok=False
				PLog(str(exception))
				break
	if ok:										# Abschluss: Filterliste speichern
		if os.path.isfile(filterfile) == False:
			err_msg = RSave(filterfile, filter_pat)
			if err_msg == '':
				PLog("Fehler beim Anlegen der Filterliste") # ohne Dialog	
		return True
	else:
		return str(exception)
		
#---------------------------
# sichert Verz. für check_DataStores
def getDirZipped(path, zipf):
	PLog('getDirZipped:')	
	for root, dirs, files in os.walk(path):
		for file in files:
			zipf.write(os.path.join(root, file)) 
#----------------------------------------------------------------  
# Die Funktion Dict speichert + lädt Python-Objekte mittels Pickle.
#	Um uns das Handling mit keys zu ersparen, erzeugt die Funktion
#	trotz des Namens keine dicts. Aufgabe ist ein einfacher
#	persistenter Speicher. Der Name Dict lehnt sich an die
#	allerdings wesentlich komfortablere Dict-Funktion in Plex an.
#
#	Falls (außerhalb von Dict) nötig, kann mit der Zusatzfunktion 
#	name() ein Variablenname als String zurück gegeben werden.
#	
#	Um die Persistenz-Variablen von den übrigen zu unterscheiden,
#	kennzeichnen wir diese mit vorangestelltem Dict_ (ist aber
#	keine Bedingung).
#
# Zuweisungen: 
#	Bsp. für Speichern:
#		 Dict('store', "Dict_name", value)
#			Dateiname: 		"Dict_name"
#			Wert in:		value
#	Bsp. für Laden:
#		CurSender = Dict("load", "CurSender")
#
#   Bsp. für CacheTime: 5*60 (5min) - Verwendung bei "load", Prüfung mtime 
#	ev. ergänzen: OS-Verträglichkeit des Dateinamens

def Dict(mode, Dict_name='', value='', CacheTime=None):
	PLog('Dict: ' + mode)
	PLog('Dict: ' + str(Dict_name))
	PLog('Dict: ' + str(type(value)))
	dictfile = "%s/%s" % (DICTSTORE, Dict_name)
	PLog("dictfile: " + dictfile)
	
	if mode == 'store':	
		with open(dictfile, 'wb') as f: pickle.dump(value, f, protocol=pickle.HIGHEST_PROTOCOL)
		f.close
		return True
	if mode == 'remove':		# einzelne Datei löschen
		try:
			 os.remove(dictfile)
			 return True
		except:	
			return False
			
	if mode == 'ClearUp':			# Files im Dictstore älter als maxdays löschen
		maxdays = int(Dict_name)
		return ClearUp(DICTSTORE, maxdays*86400) # 1 Tag=86400 sec
			
	if mode == 'load':	
		if os.path.exists(dictfile) == False:
			PLog('Dict: %s nicht gefunden' % dictfile)
			return False
		if CacheTime:
			mtime = os.path.getmtime(dictfile)	# modified-time
			now	= time.time()
			CacheLimit = now - CacheTime		# 
			PLog("now %d, mtime %d, CacheLimit: %d, CacheTime: %d" % (now, mtime, CacheLimit, CacheTime))
			if CacheLimit > mtime:
				PLog('Cache miss: CacheLimit > mtime')
				return False
			else:
				PLog('Cache hit: load')	
		try:			
			with open(dictfile, 'rb')  as f: data = pickle.load(f)
			f.close
			PLog('load from Cache')
			return data
		# Exception  ausführlicher: s.o.
		except Exception as e:	
			PLog('UnpicklingError' + str(e))
			return False

#-------------------------
# Zusatzfunktion für Dict - gibt Variablennamen als String zurück
# Aufruf: name(var=var) - z.Z. nicht genutzt
def name(**variables):				
	s = [x for x in variables]
	return s[0]
#----------------------------------------------------------------
# Dateien löschen älter als seconds
#		directory 	= os.path.join(path)
#		seconds		= int (1 Tag=86400, 1 Std.=3600)
# leere Ordner werden entfernt
def ClearUp(directory, seconds):	
	PLog('ClearUp: %s, sec: %s' % (directory, seconds))	
	PLog('älter als: ' + seconds_translate(seconds, days=True))
	now = time.time()
	cnt_files=0; cnt_dirs=0
	try:
		globFiles = '%s/*' % directory
		files = glob.glob(globFiles) 
		PLog("ClearUp: globFiles " + str(len(files)))
		# PLog(" globFiles: " + str(files))
		for f in files:
			#PLog(os.stat(f).st_mtime)
			#PLog(now - seconds)
			if os.stat(f).st_mtime < (now - seconds):
				if os.path.isfile(f):	
					PLog('entfernte Datei: ' + f)
					os.remove(f)
					cnt_files = cnt_files + 1
				if os.path.isdir(f):		# Verz. ohne Leertest entf.
					PLog('entferntes Verz.: ' + f)
					shutil.rmtree(f, ignore_errors=True)
					cnt_dirs = cnt_dirs + 1
		PLog("ClearUp: entfernte Dateien %s, entfernte Ordner %s" % (str(cnt_files), str(cnt_dirs)))	
		return True
	except Exception as exception:	
		PLog(str(exception))
		return False

#---------------------------------------------------------------- 
# u.a. für AddonInfos
def get_dir_size(directory):
	PLog('get_dir_size:')
	size=0

	for dirpath, dirnames, filenames in os.walk(directory):
		for f in filenames:
			fp = os.path.join(dirpath, f)
			# skip symbolic link
			if not os.path.islink(fp):
				size += os.path.getsize(fp)

	return humanbytes(size)	
#---------------------------------------------------------------- 
# checkt Existenz + Größe Datei fpath
# Rückgabe True falls > 2 Byte
def check_file(fpath):
	PLog('check_file:')
	if os.path.exists(fpath):
		s = os.path.getsize(fpath)
		PLog(u"Länge: %d" % s)
		if s > 2:				# min: \n\r
			return True
			
	return False
#---------------------------------------------------------------- 
# liest Setting direkt aus setting.xml 
# hier: .kodi/userdata/addon_data/plugin.video.ardundzdf/settings.xml
# für Problemfälle (z.Z. Monitor in epgRecord)
def get_Setting(ID):
	PLog('get_Setting:')
	USERDATA	= xbmc.translatePath("special://userdata")
	SETTINGS_XML= os.path.join(USERDATA, "addon_data", ADDON_ID, "settings.xml")
	
	page = RLoad(SETTINGS_XML, abs_path=True)
	lines = page.splitlines()
	for line in lines:
		if ID in line:
			val = stringextract('>', '<', line)
			return val
			
	return ''
#----------------------------------------------------------------  
# Listitems verlangen encodierte Strings auch bei Umlauten. Einige Quellen liegen in unicode 
#	vor (s. json-Auswertung in get_page) und müssen rückkonvertiert  werden.
# Hinw.: Teilstrings in unicode machen str-Strings zu unicode-Strings.
# für Python2	
# 19.11.2019 abgelöst durch py2_encode aus Kodi-six
def UtfToStr(line):
	PLog('UtfToStr:')
	return py2_encode(line)			# wirkt nur in Python2: Unicode -> str
		
# def BytesToUnicode(line) - ersetzt durch py2_decode
	
def up_low(line, mode='up'):
	try:
		if PYTHON2:	
			if isinstance(line, unicode):
				line = line.encode('utf-8')
		if mode == 'up':
			return line.upper()
		else:
			return line.lower()
	except Exception as exception:	
		PLog('up_low: ' + str(exception))
	return up_low

#----------------------------------------------------------------  
# In Kodi fehlen die summary- und tagline-Zeilen der Plexversion. Diese ersetzen wir
#	hier einfach durch infoLabels['Plot'], wobei summary und tagline durch 
#	2 Leerzeilen getrennt werden (Anzeige links unter icon).
#
#	Sofortstart + Resumefunktion, einschl. Anzeige der Medieninfo:
#		nur problemlos, wenn das gewählte Listitem als Video (Playable) gekennzeichnet ist.
# 		mediatype steuert die Videokennz. im Listing - abhängig von Settings (Sofortstart /
#		Einzelauflösungen) - hier erfolgt die Umsetzung li.setInfo(type="video").
#		Die Kontextmenü-Einträge zum Video (z.B.: bei .. fortsetzen) übernimmt dann Kodi mit
#		Eintrag in die Datenbank MyVideos116.db (Tabs u.a. bookmark, files).s
#		Mehr s. PlayVideo
#
#	Kontextmenüs (Par. cmenu): base64-Kodierung wurde 2019 benötigt für url-Parameter (nötig für
#		router) und als Prophylaxe gegen durch doppelte utf-8-Kodierung erzeugte Sonderzeichen.
#		Dekodierung erfolgt in Watch + ShowFavs. Nicht mehr benötigt, falls nochmal: s. Commit
#		9137781 on 16 Oct 2019.
#		cmenu triggert Kontextmenü, weitere Param. dessen Eigenschaften (Bsp. start_end für 
#			K-Menü "Sendung aufnehmen" <- EPG_ShowSingle).
#
#	Sortierung: i.d.R. unsortiert (Reihenfolge wie Web), erford. für A-Z-Seiten (api/podcasts)
#		Hinw.: bei Sortierung auf Homebutton verzichten 
#
#	21.03.2020 Coding-Phänomen Merkliste: Param action + dirID mutieren zu unicode, wenn in thumb-url 
#		ein unbekanntes Zeichen auftritt - Bsp. persÃ¶nlich, Ursache: fehlerhaftes unquote_plus
#		unter python2. Workaround: py2_encode für action + dirID (addDir OK, aber falsche thumb-url)
#		und Erweiterung von decode_url
#
# 	31.03.2020 merkname ersetzt label im Kontextmenü Merkliste (label kann Filter-Prefix enthalten). 
#	30.06.2020 Hinw.: im Kontextmenü für fparam verwendete Params müssen identisch encodiert sein,
#		sonst schlägt die json-Dekodierung in router fehl.
#
# 	04.07.2020 Erweiterung Kontextmenüs "Sendung aufnehmen" (EPG_ShowSingle)
# 	08.07.2020 Erweiterung Kontextmenüs "Recording TV-Live" (EPG_ShowAll)  
#
def addDir(li, label, action, dirID, fanart, thumb, fparams, summary='', tagline='', mediatype='',\
		cmenu=True, sortlabel='', merkname='', filterstatus='', start_end=''):
	PLog('addDir:');
	PLog(type(label))
	label_org=label				# s. 'Job löschen' in K-Menüs
	label=py2_encode(label)
	PLog('addDir_label: {0}, action: {1}, dirID: {2}'.format(label[:100], action, dirID))
	PLog(mediatype);
	action=py2_encode(action); dirID=py2_encode(dirID); 
	summary=py2_encode(summary); tagline=py2_encode(tagline); 
	fparams=py2_encode(fparams); fanart=py2_encode(fanart); thumb=py2_encode(thumb);
	merkname=py2_encode(merkname); start_end=py2_encode(start_end);
	PLog('addDir_summary: {0}, tagline: {1}, mediatype: {2}, cmenu: {3}'.format(summary[:80], tagline[:80], mediatype, cmenu))

		
	li.setLabel(label)			# Kodi Benutzeroberfläche: Arial-basiert für arabic-Font erf.
	# PLog('summary, tagline: {0}, {1}'.format(summary, tagline))
	Plot = ''
	if tagline:								
		Plot = tagline
	if summary:	
		Plot = Plot +"\n\n" + summary
		
	if mediatype == 'video': 	# "video", "music" setzen: List- statt Dir-Symbol
		li.setInfo(type="video", infoLabels={"Title": label, "Plot": Plot, "mediatype": "video"})	
		isFolder = False		# nicht bei direktem Player-Aufruf - OK mit setResolvedUrl
		li.setProperty('IsPlayable', 'true')					
	else:
		li.setInfo(type="video", infoLabels={"Title": label, "Plot": Plot})	
		li.setProperty('IsPlayable', 'false')
		isFolder = True	
	
	li.setArt({'thumb':thumb, 'icon':thumb, 'fanart':fanart})
	if sortlabel:
		# kein Unterschied zw. SORT_METHOD_LABEL / SORT_METHOD_LABEL_IGNORE_THE
		xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL)
	else:
		xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_UNSORTED)
	PLog('PLUGIN_URL: ' + PLUGIN_URL)	# plugin://plugin.video.ardundzdf/
	PLog('HANDLE: %s' % HANDLE)
	
	PLog("fparams: " + unquote(fparams)[:200] + "..")
	if thumb == None:
		thumb = ''
		
	add_url = PLUGIN_URL+"?action="+action+"&dirID="+dirID+"&fanart="+fanart+"&thumb="+thumb+quote(fparams)
	PLog("addDir_url: " + unquote(add_url)[:200])		
	
	# todo: Ausschluss-Filter 
	if cmenu:														# Kontextmenüs Merkliste hinzufügen
		Plot = Plot.replace('\n', '||')								# || Code für LF (\n scheitert in router)
		# PLog('Plot: ' + Plot)
		fparams_folder=''; fparams_filter=''; fparams_delete=''; 
		fparams_change=''; fparams_record=''; fparams_recordLive='';
		if merkname:												# Aufrufer ShowFavs (Settings: Ordner)
			if SETTINGS.getSetting('pref_watchlist') ==  'true':	# Merkliste verwenden 
				# Param name reicht für folder + filter				# Ordner ändern / Filtern
				label = merkname
				fp = {'action': 'folder', 'name': quote_plus(label),'thumb': quote_plus(thumb),\
					'Plot': quote_plus(Plot),'url': quote_plus(add_url)}	
				fparams_folder = "&fparams={0}".format(fp)
				PLog("fparams_folder: " + fparams_folder[:100])
				fparams_folder = quote_plus(fparams_folder)			#  Ordner ändern
				
				fp = {'action': 'filter', 'name': quote_plus(label)} 
				fparams_filter = "&fparams={0}".format(fp)
				fparams_filter = quote_plus(fparams_filter)			# Filtern

				fp = {'action': 'filter_delete', 'name': quote_plus('label')} 
				fparams_delete = "&fparams={0}".format(fp)
				fparams_delete = quote_plus(fparams_delete) 		# Filter entfernen
				
		if filterstatus:											# Ausschluss-Filter EIN/AUS
			fp = {'action': 'state_change'} 
			fparams_change = "&fparams={0}".format(fp)
			fparams_change = quote_plus(fparams_change)				# Filtern
			
		# unterschiedl. Parameterquellen: EPG_ShowSingle, EPG_ShowAll - bei
		#	title + descr sind hier die Codier.-Behandl. zu wiederholen:
		if start_end:												# Unix-Time-Format od. "Recording.."
			PLog("start_end: " + start_end)
			f = unquote(fparams)									# Param. extrahieren 
			f = f.replace("': '", "':'")
			# PLog(f)		# Debug
			Sender = stringextract("Sender':'", "'", f) 			# Bsp. 'ARTE'
			url = stringextract("path':'", "'", f) 					# Stream-Url
			# title mit Markierung übernehmen
			title = stringextract("title':'", "'", f) 				# Bsp. 'Mi | 01:45 | Dick und nun?'
			title = py2_decode(title)
			title = repl_json_chars(title)
			PLog("title: " + title)
			descr = "%s\n\n%s" % (tagline, summary)
			descr = descr.replace('\n','||')
			descr = py2_decode(descr)
			descr = repl_json_chars(descr)
			
			if "Recording TV-Live" in start_end:				# K-Menü in EPG_ShowAll -> LiveRecord
				Sender = cleanmark(title)
				Sender = Sender.split("|")[0]						# "Sender | EPG"
				duration = SETTINGS.getSetting('pref_LiveRecord_duration')
				duration, laenge = duration.split('=')
				duration = duration.strip()
				if SETTINGS.getSetting('pref_LiveRecord_input') == 'true':
					laenge = "wird manuell eingegeben"
				duration=py2_encode(duration); laenge=py2_encode(laenge);
				Sender=py2_encode(Sender); url=py2_encode(url);
				fp = {'url': quote_plus(url), 'title': quote_plus(Sender),\
					'duration': quote_plus(duration), 'laenge': quote_plus(laenge)} 
				fparams_recordLive = "&fparams={0}".format(fp)
				PLog("fparams_recordLive: " + fparams_recordLive[:100])
				fparams_recordLive = quote_plus(fparams_recordLive)			
			else:													# K-Menü in EPG_ShowSingle	
				title=py2_encode(title); descr=py2_encode(descr)
				fp = {'url': quote_plus(url), 'sender': quote_plus(Sender),\
					'title': quote_plus(title), 'descr': quote_plus(descr), 'start_end': start_end} 
				fparams_record = "&fparams={0}".format(fp)
				PLog("fparams_record: " + fparams_record[:100])
				fparams_record = quote_plus(fparams_record)						
			
		fp = {'action': 'add', 'name': quote_plus(label),'thumb': quote_plus(thumb),\
			'Plot': quote_plus(Plot),'url': quote_plus(add_url)}	
		fparams_add = "&fparams={0}".format(fp)
		PLog("fparams_add: " + fparams_add[:100])
		fparams_add = quote_plus(fparams_add)

		fp = {'action': 'del', 'name': quote_plus(label)}			# name reicht für del
		fparams_del = "&fparams={0}".format(fp)
		PLog("fparams_del: " + fparams_del[:100])
		fparams_del = quote_plus(fparams_del)
		
		# Script: This behaviour will be removed - siehe https://forum.kodi.tv/showthread.php?tid=283014
		MY_SCRIPT=xbmc.translatePath('special://home/addons/%s/resources/lib/merkliste.py' % (ADDON_ID))
		commands = []
		commands.append(('Zur Merkliste hinzufügen', 'RunScript(%s, %s, ?action=dirList&dirID=Watch%s)' \
				% (MY_SCRIPT, HANDLE, fparams_add)))
		commands.append(('Aus Merkliste entfernen', 'RunScript(%s, %s, ?action=dirList&dirID=Watch%s)' \
				% (MY_SCRIPT, HANDLE, fparams_del)))
	
		if fparams_folder:											# Aufrufer ShowFavs s.o.
			PLog('set_folder_context: ' + merkname)
			commands.append(('Merklisten-Eintrag zuordnen', 'RunScript(%s, %s, ?action=dirList&dirID=Watch%s)' \
				% (MY_SCRIPT, HANDLE, fparams_folder)))
			commands.append(('Merkliste filtern', 'RunScript(%s, %s, ?action=dirList&dirID=Watch%s)' \
				% (MY_SCRIPT, HANDLE, fparams_filter)))
			commands.append(('Filter der  Merkliste entfernen', 'RunScript(%s, %s, ?action=dirList&dirID=Watch%s)' \
				% (MY_SCRIPT, HANDLE, fparams_delete)))
				
		if fparams_change or fparams_record or fparams_recordLive:	# Ausschluss-Filter EIN/AUS, ProgramRecord
			MY_SCRIPT=xbmc.translatePath('special://home/addons/%s/ardundzdf.py' % (ADDON_ID))
			if fparams_change:										# Aufrufer home s.o. -> FilterToolsWork
				commands.append(('Ausschluss-Filter EIN/AUS', 'RunScript(%s, %s, ?action=dirList&dirID=FilterToolsWork%s)' \
					% (MY_SCRIPT, HANDLE, fparams_change)))
			if fparams_record:										# Aufrufer EPG_ShowSingle -> ProgramRecord
				commands.append(('diese Sendung aufnehmen', 'RunScript(%s, %s, ?action=dirList&dirID=ProgramRecord%s)' \
					% (MY_SCRIPT, HANDLE, fparams_record)))
			if fparams_recordLive:										# Aufrufer EPG_ShowAll -> LiveRecord
				commands.append(('Recording TV-Live', 'RunScript(%s, %s, ?action=dirList&dirID=LiveRecord%s)' \
					% (MY_SCRIPT, HANDLE, fparams_recordLive)))

		li.addContextMenuItems(commands)				
		
	xbmcplugin.addDirectoryItem(handle=HANDLE,url=add_url,listitem=li,isFolder=isFolder)
	
	PLog('addDir_End')		
	return	

#---------------------------------------------------------------- 
# holt kontrolliert raw-Content, cTimeout für cacheTime
# 02.09.2018	erweitert um 2. Alternative mit urllib2.Request +  ssl.SSLContext
#	s.a. loadPage in Modul zdfmobile.
# 11.10.2018 HTTP.Request (Plex) ersetzt durch urllib2.Request
# 	03.11.2018 requests-call vorangestellt wg. Kodi-Problem: 
#	bei urllib2.Requests manchmal errno(0) (https) - Verwend. installierter Zertifikate erfolglos
# 07.11.2018 erweitert um Header-Anfrage GetOnlyRedirect zur Auswertung von Redirects (http error 302).
# Format header dict im String: "{'key': 'value'}" - Bsp. Search(), get_formitaeten()
# 23.12.2018 requests-call vorübergehend auskommentiert, da kein Python-built-in-Modul (bemerkt beim 
#	Test in Windows7
# 13.01.2019 erweitert für compressed-content (get_page2)
# 25.01.2019 Rückgabe Redirect-Url (get_page2) in msg
# 21.06.2020 urlencoding mit Param. safe für franz. Zeichen, Berücksicht. m3u8-Links,
#	transl_umlaute(path) entfällt damit
#
def get_page(path, header='', cTimeout=None, JsonPage=False, GetOnlyRedirect=False):
	PLog('get_page:'); PLog("path: " + path); PLog("JsonPage: " + str(JsonPage)); 

	if header:									# dict auspacken
		header = unquote(header);  
		header = header.replace("'", "\"")		# json.loads-kompatible string-Rahmen
		header = json.loads(header)
		PLog("header: " + str(header)[:80]);

	# path = transl_umlaute(path)				# Umlaute z.B. in Podcast "Bäckerei Fleischmann"
	# path = unquote(path)						# scheitert bei quotierten Umlauten, Ersatz replace				
	path = path.replace('https%3A//','https://')# z.B. https%3A//classic.ardmediathek.de
	
	path = py2_encode(path)
	path = quote(path, safe="@:?.,-_&=/")		# s.o. ('-_' in m3u8-Links)			
	PLog("safe_path: " + path)		
	 
	msg = ''; page = ''	
	UrlopenTimeout = 10
	
	'''
	try:
		import requests							# 1. Versuch mit requests - s.o.
		PLog("get_page1:")
		...
	'''
	
	if page == '':
		try:															# 2. Versuch ohne SSLContext 
			PLog("get_page2:")
			if GetOnlyRedirect:											# nur Redirect anfordern
				# Alt. hier : new_url = r.geturl()
				# bei Bedarf HttpLib2 mit follow_all_redirects=True verwenden
				PLog('GetOnlyRedirect: ' + str(GetOnlyRedirect))
				r = urlopen(path)
				page = r.geturl()
				PLog(page)			# Url
				return page, msg					

			if header:
				req = Request(path, headers=header)	
			else:
				req = Request(path)
								
			r = urlopen(req)	
			new_url = r.geturl()										# follow redirects
			PLog("new_url: " + new_url)									# -> msg s.u.
			# PLog("headers: " + str(r.headers))
			
			compressed = r.info().get('Content-Encoding') == 'gzip'
			PLog("compressed: " + str(compressed))
			page = r.read()
			PLog(len(page))
			if compressed:
				buf = BytesIO(page)
				f = gzip.GzipFile(fileobj=buf)
				page = f.read()
				PLog(len(page))
			r.close()
			PLog(page[:100])
			msg = new_url
		except URLError as exception:
			msg = str(exception)
			PLog(msg)
				
	
	if page == '':
		import ssl
		try:
			PLog("get_page3:")											# 3. Versuch mit SSLContext
			if header:
				req = Request(path, headers=header)	
			else:
				req = Request(path)														
			# gcontext = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
			gcontext = ssl.create_default_context()
			gcontext.check_hostname = False
			# gcontext.verify_mode = ssl.CERT_REQUIRED
			r = urlopen(req, context=gcontext, timeout=UrlopenTimeout)
			# r = urllib2.urlopen(req)
			# PLog("headers: " + str(r.headers))
			page = r.read()
			r.close()
			PLog(len(page))
		except URLError as exception:
			msg = str(exception)
			PLog(msg)						

			
	if page == '':
		# Abschalthinweis verfrüht - fehlende Beiträge in Classic-
		#	Version immer noch möglich (02.03.2020)
		error_txt = 'Seite nicht erreichbar oder nicht mehr vorhanden'
		#error_txt = msg
		#if 'classic.ardmediathek.de' in path:
		#	msg1 = 'Die ARD-Classic-Mediathek ist vermutlich nicht mehr verfügbar.'	
		#	msg2 = 'Bitte in den Einstellungen abschalten, um das Modul'
		#	msg3 = 'ARD-Neu zu aktivieren.'
		#	MyDialog(msg1, msg2, msg3)		 			 	 
		msg = error_txt + ' | %s' % msg
		PLog(msg)
		return page, msg
		
	if page:				
		page = page.decode('utf-8')	
	if JsonPage:
		PLog('json_load: ' + str(JsonPage))
		PLog(len(page))
		page = page.replace('\\/', '/')									# für Python3 erf.
		try:
			request = json.loads(page)
			# 23.11.2019: Blank hinter separator : entfernt - wird in Python nicht beachtet.
			#	Auswirkung in get_formitaeten (extract videodat_url)
			request = json.dumps(request, sort_keys=True, indent=2, separators=(',', ':'))  # sortierte Ausgabe
			page = (page.replace('" : "', '":"').replace('" :', '":'))	# für Python3 erf.
			PLog("jsonpage: " + page[:100]);
		except Exception as exception:
			msg = str(exception)
			PLog(msg)

	return page, msg	
#---------------------------------------------------------------- 
# img_urlScheme: img-Url ermitteln für get_sendungen, ARDRubriken. text = string, dim = Dimension
def img_urlScheme(text, dim, ID=''):
	PLog('img_urlScheme: ' + text[0:60])
	PLog(dim)
	
	pos = 	text.find('class="mediaCon">')			# img erst danach
	if pos >= 0:
		text = text[pos:]
	img_src = stringextract('img.ardmediathek.de', '##width', text)
		
	img_alt = stringextract('title="', '"', text)
	if img_alt == '':
		img_alt = stringextract('alt="', '"', text)
	img_alt = img_alt.replace('- Standbild', '')
	img_alt = 'Bild: ' + img_alt
	
		
	if img_src and img_alt:
		if img_src.startswith('http') == False:			#
			img_src = 'https://img.ardmediathek.de' + img_src 
		img_src = img_src + str(dim)					# dim getestet: 160,265,320,640
		if ID == 'PODCAST':								# Format Quadrat klappt nur bei PODCAST,
			img_src = img_src.replace('16x9', '16x16')	# Sender liefert Ersatz, falls n.v.
		if '?mandant=ard' in text:						# Anhang bei manchen Bildern
			img_src =img_src + '?mandant=ard' 
		PLog('img_urlScheme: ' + img_src)
		img_alt = py2_encode(img_alt)
		PLog('img_urlScheme: ' + img_alt[0:40])
		return img_src, img_alt
	else:
		PLog('img_urlScheme: leer')
		return '', ''		
	
#---------------------------------------------------------------- 

# Ersetzt R-Funktion von Plex (Pfad zum Verz. Resources, hier zusätzl. Unterordner möglich) 
# Falls abs_path nicht gesetzt, wird der Pluginpfad zurückgegeben, sonst der absolute Pfad
# für lokale Icons üblicherweise PluginAbsPath.
def R(fname, abs_path=False):	
	PLog('R(fname): %s' % fname); # PLog(abs_path)
	# PLog("ADDON_PATH: " + ADDON_PATH)
	if abs_path:
		try:
			# fname = '%s/resources/%s' % (PluginAbsPath, fname)
			path = os.path.join(ADDON_PATH,fname)
			return path
		except Exception as exception:
			PLog(str(exception))
	else:
		if fname.endswith('png'):	# Icons im Unterordner images
			fname = '%s/resources/images/%s' % (ADDON_PATH, fname)
			fname = os.path.abspath(fname)
			# PLog("fname: " + fname)
			return os.path.join(fname)
		else:
			fname = "%s/resources/%s" % (ADDON_PATH, fname)
			fname = os.path.abspath(fname)
			return fname 
#----------------------------------------------------------------  
# ersetzt Resource.Load von Plex 
# abs_path s.o.	R()	
def RLoad(fname, abs_path=False): # ersetzt Resource.Load von Plex 
	if abs_path == False:
		fname = '%s/resources/%s' % (ADDON_PATH, fname)
	path = os.path.join(fname) # abs. Pfad
	PLog('RLoad: %s' % str(fname))
	try:
		if PYTHON2:
			with open(path,'r') as f:
				page = f.read()		
		else:
			with open(path,'r', encoding="utf8") as f:
				page = f.read()		
	except Exception as exception:
		PLog(str(exception))
		page = ''
	return page
#----------------------------------------------------------------
# Gegenstück zu RLoad - speichert Inhalt page in Datei fname im  
#	Dateisystem. PluginAbsPath muss in fname enthalten sein,
#	falls im Pluginverz. gespeichert werden soll 
#  Migration Python3: immer utf8 - Alt.: xbmcvfs.File mit
#		Bytearray (s. merkliste.py)
#  05.07.2020 erweitert für Lock-Nutzung (für Monitor in epgRecord).
#
def RSave(fname, page, withcodec=False): 
	PLog('RSave: %s' % str(fname))
	PLog(withcodec)
	path = os.path.join(fname) # abs. Pfad
	msg = ''					# Rückgabe leer falls OK
	maxLockloops	= 10		# 1 sec bei 10 x xbmc.sleep(100)	
	
	LOCK = fname + ".lck"
	i=0
	while os.path.exists(LOCK):	
		i=i+1
		if i >= maxLockloops:		# Lock brechen, vermutl. Ruine
			os.remove(LOCK)
			PLog("break " + LOCK)
			break
		xbmc.sleep(100)		
	
	try:
		if PYTHON2:
			if withcodec:		# 14.11.0219 Kompat.-Maßnahme
				import codecs	#	für DownloadExtern
				with codecs.open(path,'w', encoding='utf-8') as f:
					f.write(page)	
			else:
				with open(path,'w') as f:
					f.write(page)		
		else:
			with open(path,'w', encoding="utf8") as f:
				f.write(page)
		
	except Exception as exception:
		msg = str(exception)
		PLog('RSave_Exception: ' + msg)
	return msg
#----------------------------------------------------------------  
# Holt Bandwith, Codecs + Resolution aus m3u8-Datei
# Bsp.: #EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=61000,CODECS="mp4a.40.2"
def GetAttribute(text, attribute, delimiter1 = '=', delimiter2 = ','):
	PLog('GetAttribute:')
	if attribute == 'CODECS':	# Trenner = Komma, nur bei CODEC ist Inhalt 'umrahmt' 
		delimiter1 = '="'
		delimiter2 = '"'
	x = text.find(attribute)
	if x > -1:
		y = text.find(delimiter1, x + len(attribute)) + len(delimiter1)
		z = text.find(delimiter2, y)
		if z == -1:
			z = len(text)
		return text[y:z].strip()
	else:
		return ''
#----------------------------------------------------------------  
def repl_dop(liste):	# Doppler entfernen, im Python-Script OK, Problem in Plex - s. PageControl
	mylist=liste
	myset=set(mylist)
	mylist=list(myset)
	mylist.sort()
	return mylist
#----------------------------------------------------------------  
def repl_char(cut_char, line):	# problematische Zeichen in Text entfernen, wenn replace nicht funktioniert
	line_ret = line				# return line bei Fehlschlag
	pos = line_ret.find(cut_char)
	while pos >= 0:
		line_l = line_ret[0:pos]
		line_r = line_ret[pos+len(cut_char):]
		line_ret = line_l + line_r
		pos = line_ret.find(cut_char)
		#PLog(cut_char); PLog(pos); PLog(line_l); PLog(line_r); PLog(line_ret)	# bei Bedarf	
	return line_ret
#----------------------------------------------------------------
#	doppelte utf-8-Enkodierung führt an manchen Stellen zu Sonderzeichen
#  	14.04.2019 entfernt: (':', ' ')
# 	todo: decode('utf-8') hier  wie unescape ff.
def repl_json_chars(line):	# für json.loads (z.B.. in router) json-Zeichen in line entfernen
	line_ret = line
	#PLog(type(line_ret))
	for r in	((u'"', u''), (u'\\', u''), (u'\'', u'')
		, (u'&', u'und'), ('(u', u'<'), (u'(', u'<'),  (u')', u'>'), (u'∙', u'|')
		, (u'„', u'>'), (u'“', u'<'), (u'”', u'>'),(u'°', u' Grad')
		, (u'\r', u''), (u'#', u'*')):			
		line_ret = line_ret.replace(*r)
	
	return line_ret
#---------------------------------------------------------------- 
# strip-Funktion, die auch Zeilenumbrüche innerhalb des Strings entfernt
#	\s [ \t\n\r\f\v - s. https://docs.python.org/3/library/re.html
def mystrip(line):	
	line_ret = line	
	line_ret = re.sub(r"\s+", " ", line)	# Alternative für strip + replace
	# PLog(line_ret)		# bei Bedarf
	return line_ret
#----------------------------------------------------------------  	
# DirectoryNavigator - Nutzung des Kodi-builtin, der Code der PMS-Version kann entfallen
# S. http://mirrors.kodi.tv/docs/python-docs/13.0-gotham/xbmcgui.html
# mytype: 	0 : ShowAndGetDirectory, 1 : ShowAndGetFile, 2
# mask: 	nicht brauchbar bei endungslosen Dateien, Bsp. curl
def DirectoryNavigator(settingKey, mytype, heading, shares='files', useThumbs=False, \
	treatAsFolder=False, path=''):
	PLog('DirectoryNavigator:')
	PLog(settingKey); PLog(mytype); PLog(heading); PLog(path);
	
	dialog = xbmcgui.Dialog()
	d_ret = dialog.browseSingle(int(mytype), heading, shares, '', False, False, path)	
	PLog('d_ret: ' + d_ret)
	
	SETTINGS.setSetting(settingKey, d_ret)	
	return 
#----------------------------------------------------------------  
def stringextract(mFirstChar, mSecondChar, mString):  	# extrahiert Zeichenkette zwischen 1. + 2. Zeichenkette
	pos1 = mString.find(mFirstChar)						# return '' bei Fehlschlag
	ind = len(mFirstChar)
	#pos2 = mString.find(mSecondChar, pos1 + ind+1)		
	pos2 = mString.find(mSecondChar, pos1 + ind)		# ind+1 beginnt bei Leerstring um 1 Pos. zu weit
	rString = ''

	if pos1 >= 0 and pos2 >= 0:
		rString = mString[pos1+ind:pos2]	# extrahieren 
		
	#PLog(mString); PLog(mFirstChar); PLog(mSecondChar); 	# bei Bedarf
	#PLog(pos1); PLog(ind); PLog(pos2);  PLog(rString); 
	return rString
#---------------------------------------------------------------- 
# extrahiert Blöcke aus mString: Startmarke=blockmark, Endmarke=blockendmark 
def blockextract(blockmark, mString, blockendmark=''):  	
	#	blockmark bleibt Bestandteil der Rückgabe - im Unterschied zu split()
	#	Block wird durch blockendmark begrenzt, falls belegt, sonst reicht 
	#		 letzter Block reicht bis Ende mString (undefinierte Länge). 
	#	Rückgabe in Liste.
	#	Verwendung, wenn xpath nicht funktioniert 
	rlist = []				
	if 	blockmark == '' or 	mString == '':
		PLog('blockextract: blockmark or mString leer')
		return rlist
	
	pos = mString.find(blockmark)
	if 	mString.find(blockmark) == -1:
		PLog('blockextract: blockmark <%s> nicht in mString enthalten' % blockmark)
		# PLog(pos); PLog(blockmark);PLog(len(mString));PLog(len(blockmark));
		return rlist
		
	pos2 = 1
	while pos2 > 0:
		pos1 = mString.find(blockmark)						
		ind = len(blockmark)
		pos2 = mString.find(blockmark, pos1 + ind)		
		
		if blockendmark:
			pos3 = mString.find(blockendmark, pos1 + ind)
			ind_end = len(blockendmark)
			block = mString[pos1:pos3+ind_end]	# extrahieren einschl.  blockmark + blockendmark
			# PLog(block)			
		else:
			block = mString[pos1:pos2]			# extrahieren einschl.  blockmark
			# PLog(block)		
		mString = mString[pos2:]	# Rest von mString, Block entfernt
		rlist.append(block)
	return rlist  
#----------------------------------------------------------------  
def teilstring(zeile, startmarker, endmarker):  		# rfind: endmarker=letzte Fundstelle, return '' bei Fehlschlag
  # die übergebenen Marker bleiben Bestandteile der Rückgabe (werden nicht abgeschnitten)
  pos2 = zeile.find(endmarker, 0)
  pos1 = zeile.rfind(startmarker, 0, pos2)
  if pos1 & pos2:
    teils = zeile[pos1:pos2+len(endmarker)]	# 
  else:
    teils = ''
  #PLog(pos1) PLog(pos2) 
  return teils 
# ----------------------------------------------------------------------
def my_rfind(left_pattern, start_pattern, line):  # sucht ab start_pattern rückwärts + erweitert 
#	start_pattern nach links bis left_pattern.
#	Rückgabe: Position von left_pattern und String ab left_pattern bis einschl. start_pattern	
#	Mit Python's rfind-Funktion nicht möglich

	# PLog(left_pattern); PLog(start_pattern); 
	if left_pattern == '' or start_pattern == '' or line.find(start_pattern) == -1:
		return -1, ''
	startpos = line.find(start_pattern)
	# Log(startpos); Log(line[startpos-10:startpos+len(start_pattern)]); 
	i = 1; pos = startpos
	while pos >= 0:
		newline = line[pos-i:startpos+len(start_pattern)]	# newline um 1 Zeichen nach links erweitern
		# Log(newline)
		if newline.find(left_pattern) >= 0:
			leftpos = pos						# Position left_pattern in line
			leftstring = newline
			# Log(leftpos);Log(newline)
			return leftpos, leftstring
		i = i+1				
	return -1, ''								# Fehler, wenn Anfang line erreicht
#----------------------------------------------------------------  	
# make_mark: farbige Markierung plus fett (optional	
# Groß-/Kleinschreibung egal
# bei Fehlschlag mString unverändert zurück
#
# title=' Aussteiger: *Identitäre* wollen Bürgerkrieg gegen'
def make_mark(mark, mString, color='red', bold=''):	
	PLog("make_mark:")	
	mark=py2_decode(mark); mString=py2_decode(mString)
	mS = up_low(mString); ma = up_low(mark)
	if ma in mS or mark == mString:
		pos1 = mS.find(ma)
		pos2 = pos1 + len(ma)		
		ms = mString[pos1:pos2]		# Mittelstück mark unverändert
		s1 = mString[:pos1]; s2 = mString[pos2:];
		if bold:
			rString= u"%s[COLOR %s][B]%s[/B][/COLOR]%s"	% (s1, color, ms, s2)
		else:
			rString= u"%s[COLOR %s]%s[/COLOR]%s"	% (s1, color, ms, s2)
		return rString
	else:
		return mString		# Markierung fehlt, mString unverändert zurück
#----------------------------------------------------------------  
def cleanmark(line): # entfernt Farb-/Fett-Markierungen
	# PLog(type(line))
	cleantext = py2_decode(line)
	cleantext = re.sub(r"\[/?[BI]\]", '', cleantext, flags=re.I)
	cleantext = re.sub(r"\[/?COLOR.*?\]", '', cleantext, flags=re.I)
	return cleantext
#----------------------------------------------------------------  
# Migration PY2/PY3: py2_decode aus kodi-six
def cleanhtml(line): # ersetzt alle HTML-Tags zwischen < und >  mit 1 Leerzeichen
	# PLog(type(line))
	cleantext = py2_decode(line)
	cleanre = re.compile('<.*?>')
	cleantext = re.sub(cleanre, ' ', line)
	return cleantext
#---------------------------------------------------------------- 
# in URL kodierte Umlaute und & wandeln, Bsp. f%C3%BCr -> für, 	&amp; -> & 	
# Migration PY2/PY3: py2_decode aus kodi-six
# Einzelersetzung deutsche Umlaute unter python2
#	Bsp. python2:  unquote('%C3%BC') -> '\xc3\x9f' statt 'ü'
def decode_url(line):	
	line = py2_decode(line)
	unquote_plus(line)
	line = line.replace(u'&amp;', u'&')
	if PYTHON2:	
		line = line.replace(u'%C3%BC', u'ü')
		line = line.replace(u'%C3%B6', u'ö')
		line = line.replace(u'%C3%A4', u'ä')
		line = line.replace(u'%C3%9F', u'ß')
		line = line.replace(u'%C3%9C', u'Ü')
		line = line.replace(u'%C3%96', u'Ö')
		line = line.replace(u'%C3%84', u'Ä')
	return line
#----------------------------------------------------------------  	
# Migration PY2/PY3: py2_decode aus kodi-six
def unescape(line):
# HTML-Escapezeichen in Text entfernen, bei Bedarf erweitern. ARD auch &#039; statt richtig &#39;	
#					# s.a.  ../Framework/api/utilkit.py
#					# Ev. erforderliches Encoding vorher durchführen - Achtung in Kodis 
#					#	Python-Version v2.26.0 'ascii'-codec-Error bei mehrfachem decode
#
	# PLog(type(line))
	if line == None or line == '':
		return ''	
	line = py2_decode(line)
	for r in	((u"&amp;", u"&"), (u"&lt;", u"<"), (u"&gt;", u">")
		, (u"&#39;", u"'"), (u"&#039;", u"'"), (u"&quot;", u'"'), (u"&#x27;", u"'")
		, (u"&ouml;", u"ö"), (u"&auml;", u"ä"), (u"&uuml;", u"ü"), (u"&szlig;", u"ß")
		, (u"&Ouml;", u"Ö"), (u"&Auml;", u"Ä"), (u"&Uuml;", u"Ü"), (u"&apos;", u"'")
		, (u"&nbsp;|&nbsp;", u""), (u"&nbsp;", u" "), (u"&bdquo;", u""), (u"&ldquo;", u""),
		# Spezialfälle:
		#	https://stackoverflow.com/questions/20329896/python-2-7-character-u2013
		#	"sächsischer Genetiv", Bsp. Scott's
		#	Carriage Return (Cr)
		(u"–", u"-"), (u"&#x27;", u"'"), (u"&#xD;", u""), (u"\xc2\xb7", u"-"),
		(u'undoacute;', u'o'), (u'&eacute;', u'e'), (u'&egrave;', u'e'),
		(u'&atilde;', u'a'), (u'quot;', u' '), (u'&#10;', u'\n'),
		(u'&#8222;', u' '), (u'&#8220;', u' '), (u'&#034;', u' '),
		(u'&copy;', u' | ')):
		line = line.replace(*r)
	return line
#----------------------------------------------------------------  
# Migration PY2/PY3: py2_decode aus kodi-six
def transl_doubleUTF8(line):	# rückgängig: doppelt kodiertes UTF-8 
	# Vorkommen: Merkliste (Plot)
	# bisher nicht benötigt: ('Ã<U+009F>', 'ß'), ('ÃŸ', 'ß')

	line = py2_decode(line)
	for r in ((u'Ã¤', u"ä"), (u'Ã„', u"Ä"), (u'Ã¶', u"ö")		# Umlaute + ß
		, (u'Ã–', u"Ö"), (u'Ã¼', u"ü"), (u'Ãœ', u'Ü')
		, (u'Ã', u'ß')
		, (u'\xc3\xa2', u'*')):	# a mit Circumflex:  â<U+0088><U+0099> bzw. \xc3\xa2

		line = line.replace(*r)
	return line	
#---------------------------------------------------------------- 
# Dateinamen für Downloads + Bilderserien 
# erzeugt - hoffentlich - sichere Dateinamen (ohne Extension)
# zugeschnitten auf Titelerzeugung in meinen Plugins 
# Migration PY2/PY3: py2_decode aus kodi-six
# 24.04.2020 Entf. von Farb- und Fettmarkierungen (z.B. 
#	Downloads aus Suchbeiträgen) - ähnlich clean_Plot (merkliste)
# 
def make_filenames(title, max_length=255):
	PLog('make_filenames:')
	
	title = py2_decode(title)
	title = cleanmark(title)

	title = title.replace(u'|', ' ') 
	title = title.replace(u':', ' ')
	
	fname = transl_umlaute(title)						# Umlaute	
	
	valid_chars = "-_ %s%s" % (string.ascii_letters, string.digits)
	fname = ''.join(c for c in fname if c in valid_chars)
	fname = fname.replace(u' ', u'_')
	fname = fname.replace(u'___', u'_')
	return fname[:max_length]
#----------------------------------------------------------------  
# Umlaute übersetzen, wenn decode nicht funktioniert
# Migration PY2/PY3: py2_decode aus kodi-six
def transl_umlaute(line):	
	line= py2_decode(line)	
	line_ret = line
	line_ret = line_ret.replace(u"Ä", u"Ae", len(line_ret))
	line_ret = line_ret.replace(u"ä", u"ae", len(line_ret))
	line_ret = line_ret.replace(u"Ü", u"Ue", len(line_ret))
	line_ret = line_ret.replace(u'ü', u'ue', len(line_ret))
	line_ret = line_ret.replace(u"Ö", u"Oe", len(line_ret))
	line_ret = line_ret.replace(u"ö", u"oe", len(line_ret))
	line_ret = line_ret.replace(u"ß", u"ss", len(line_ret))	
	return line_ret
#---------------------------------------------------------------- 
# Zeilenumbrüche bei Erhalt von Newlines
# Pythons textwrap kümmert sich nicht um \n
# http://code.activestate.com/recipes/148061-one-liner-word-wrap-function/
# reduce wurde in python3 nach functools verlagert
def wrap_old(text, width):		# 15.02.2020 abgelöst durch wrap s.u.
    return reduce(lambda line, word, width=width: '%s%s%s' %
                  (line,
                   ' \n'[(len(line)-line.rfind('\n')-1
                         + len(word.split('\n',1)[0]
                              ) >= width)],
                   word),
                  text.split(' ')
                 )
#  wrap-Funktion ohne reduce:                
def wrap(text, width):
	text = text.strip()
	lines = text.splitlines()
	newtxt = []
	for line in lines:
		newline = textwrap.fill(line, width)
		newline = newline.strip()
		newtxt.append(newline)
		
	return "\n".join(newtxt)

#----------------------------------------------------------------   
# Migration PY2/PY3: py2_decode aus kodi-six
def transl_json(line):	# json-Umlaute übersetzen
	# Vorkommen: Loader-Beiträge ZDF/3Sat (ausgewertet als Strings)
	# Recherche Bsp.: https://www.compart.com/de/unicode/U+00BA
	# 
	line=py2_decode(line)
	#PLog(line)
	for r in ((u'\\u00E4', u"ä"), (u'\\u00C4', u"Ä"), (u'\\u00F6', u"ö"), (u'u002F', u"/")		
		, (u'\\u00C6', u"Ö"), (u'\\u00D6', u"Ö"),(u'\\u00FC', u"ü"), (u'\\u00DC', u'Ü')
		, (u'\\u00e4', u"ä"), (u'\\u00c4', u"Ä"), (u'\\u00f6', u"ö"), (u'u002f', u"/")	
		, (u'\\u00c6', u"Ö"), (u'\\u00d6', u"Ö"),(u'\\u00fc', u"ü"), (u'\\u00dc', u'Ü')
		, (u'\\u00DF', u'ß'), (u'\\u00df', u'ß'), (u'\\u0026', u'&'), (u'\\u00AB', u'"')
		, (u'\\u00BB', u'"')
		, (u'\xc3\xa2', u'*')			# a mit Circumflex:  â<U+0088><U+0099> bzw. \xc3\xa2
		, (u'u00B0', u' Grad')		# u00BA -> Grad (3Sat, 37 Grad)	
		, (u'u00EA', u'e')			# 3Sat: Fête 
		, (u'u00E9', u'e')			# 3Sat: Fabergé
		, (u'u00E6', u'ae')):			# 3Sat: Kjaerstad

		line = line.replace(*r)
	#PLog(line)
	return line	
#----------------------------------------------------------------  
def humanbytes(B):
	'Return the given bytes as a human friendly KB, MB, GB, or TB string'
	# aus https://stackoverflow.com/questions/12523586/python-format-size-application-converting-b-to-kb-mb-gb-tb/37423778
	B = float(B)
	KB = float(1024)
	MB = float(KB ** 2) # 1,048,576
	GB = float(KB ** 3) # 1,073,741,824
	TB = float(KB ** 4) # 1,099,511,627,776

	if B < KB:
	  return '{0} {1}'.format(B,'Bytes' if 0 == B > 1 else 'Byte')
	elif KB <= B < MB:
	  return '{0:.2f} KB'.format(B/KB)
	elif MB <= B < GB:
	  return '{0:.2f} MB'.format(B/MB)
	elif GB <= B < TB:
	  return '{0:.2f} GB'.format(B/GB)
	elif TB <= B:
	  return '{0:.2f} TB'.format(B/TB)
#----------------------------------------------------------------  
def CalculateDuration(timecode):				# 3 verschiedene Formate (s.u.)
	PLog("CalculateDuration:")
	timecode = up_low(timecode)	# Min -> min
	milliseconds = 0
	hours        = 0
	minutes      = 0
	seconds      = 0

	if timecode.find('P0Y0M0D') >= 0:			# 1. Format: 'P0Y0M0DT5H50M0.000S', T=hours, H=min, M=sec
		d = re.search('T([0-9]{1,2})H([0-9]{1,2})M([0-9]{1,2}).([0-9]{1,3})S', timecode)
		if(None != d):
			hours = int ( d.group(1) )
			minutes = int ( d.group(2) )
			seconds = int ( d.group(3) )
			milliseconds = int ( d.group(4) )
					
	if len(timecode) == 9:						# Formate: '00:30 min'	
		d = re.search('([0-9]{1,2}):([0-9]{1,2}) MIN', timecode)	# 2. Format: '00:30 min' 	
		if(None != d):
			hours = int( d.group(1) )
			minutes = int( d.group(2) )
			Log(minutes)
						
	if len(timecode) == 11:											# 3. Format: '1:50:30.000'
		d = re.search('([0-9]{1,2}):([0-9]{1,2}):([0-9]{1,2}).([0-9]{1,3})', timecode)
		if(None != d):
			hours = int ( d.group(1) )
			minutes = int ( d.group(2) )
			seconds = int ( d.group(3) )
			milliseconds = int ( d.group(4) )
	
	milliseconds += hours * 60 * 60 * 1000
	milliseconds += minutes * 60 * 1000
	milliseconds += seconds * 1000
	
	return milliseconds
#---------------------------------------------------------------- 
# Format seconds	86400	(String, Int, Float)
# Rückgabe:  		1d, 0h, 0m, 0s	(days=True)
#		oder:		0h, 0d				
def seconds_translate(seconds, days=False):
	#PLog('seconds_translate:')
	#PLog(seconds)
	if seconds == '' or seconds == 0  or seconds == 'null':
		return ''
	if int(seconds) < 60:
		return "%s sec" % seconds
	seconds = float(seconds)
	day = seconds / (24 * 3600)	
	time = seconds % (24 * 3600)
	hour = time / 3600
	time %= 3600
	minutes = time / 60
	time %= 60
	seconds = time
	if days:
		#PLog("%dd, %dh, %dm, %ds" % (day,hour,minutes,seconds))
		return "%dd, %dh, %dm, %ds" % (day,hour,minutes,seconds)
	else:
		#PLog("%d:%02d" % (hour, minutes))
		return  "%d:%02d" % (hour, minutes)		
#----------------------------------------------------------------  	
# Format timecode 	2018-11-28T23:00:00Z (ARDNew, broadcastedOn)
#					y-m-dTh:m:sZ 	ISO8601 date
# Rückgabe:			28.11.2018, 23:00 Uhr   (Sekunden entfallen)
#					bzw. '' bei Fehlschlag
# funktioniert in Kodi nur 1 x nach Neustart - s. transl_pubDate
# 26.08.2019 OK mit Lösung von BJ1 aus
#		https://www.kodinerds.net/index.php/Thread/50284-Python-Problem-mit-strptime/?postID=284746#post284746
#
# stackoverflow.com/questions/214777/how-do-you-convert-yyyy-mm-ddthhmmss-000z-time-format-to-mm-dd-yyyy-time-format
# stackoverflow.com/questions/7999935/python-datetime-to-string-without-microsecond-component
# stackoverflow.com/questions/13685201/how-to-add-hours-to-current-time-in-python
#
# ARD-Zeit + 2 Stunden
# s.a. addHour (ARDnew) - Stringroutine für ARDVerpasstContent
# Rückgabe timecode im Fehlerfall
# 22.06.2020 Anpassung an 29-stel. ZDF-Format
#
def time_translate(timecode, add_hour=2):
	PLog("time_translate: " + timecode)

	if timecode.strip() == '' or len(timecode) < 19 or timecode[10] != 'T':
		return ''
	timecode = py2_encode(timecode)
		
	# Bsp.: Funk: 			2019-09-30T12:59:27.000+0000 mit sec/1000 	+ Korr.-Faktor 0
	# 		ARDNew Live: 	2019-12-12T06:16:04.413Z
	#		ZDF:			2021-03-03T17:20:00+01:00					+ Korr.-Faktor 1 Std.
	#		ZDF:			2020-06-15T22:51:28.328+02:00 mit sec/1000 	+ Korr.-Faktor 2 Std.

	# Zielformat 2018-11-28T23:00:00Z
	day, hour_info 	= timecode.split('T')			# Datum / Uhrzeit trennen
	hour	 		= hour_info[:8]
	
	add_hour=0
	if '+' in hour_info:							# mit Korr.-Faktor s.o.			
		mil_sec, add_hour = hour_info.split('+')	# ev. add-Faktor ermitteln
		try:
			add_hour = re.search('(\d+)',add_hour).group(1)
			add_hour = int(add_hour)
		except:
			add_hour = 0
	
	timecode = "%sT%sZ" % (day, hour)	
	PLog(timecode); PLog(add_hour);
	if timecode[10] == 'T' and timecode[-1] == 'Z':  # Format OK?
		try:
			date_format = "%Y-%m-%dT%H:%M:%SZ"
			# ts = datetime.strptime(timecode, date_format)  # None beim 2. Durchlauf       
			ts = datetime.datetime.fromtimestamp(time.mktime(time.strptime(timecode, date_format)))
			new_ts = ts + datetime.timedelta(hours=add_hour) # add-Faktor addieren
			ret_ts = new_ts.strftime("%d.%m.%Y %H:%M")
			PLog(ret_ts)
			return ret_ts
		except Exception as exception:
			PLog(str(exception))
			return timecode
	else:
		return timecode
		
#---------------------------------------------------------------- 
# Format timecode 	Fri, 06 Jul 2018 06:58:00 GMT (ARD Audiothek , xml-Ausgaben)
# Rückgabe:			06.07.2018, 06:58 Uhr   (Sekunden entfallen)
# funktioniert nicht in Kodi, auch nicht der Workaround in
#	https://forum.kodi.tv/showthread.php?tid=112916 bzw.
#	https://www.kodinerds.net/index.php/Thread/50284-Python-Problem-mit-strptime
def transl_pubDate(pubDate):
	PLog('transl_pubDate:')	
	pubDate_org = pubDate		
	if pubDate == '':
		return ''
		
	if ',' in pubDate:
		pubDate = pubDate.split(',')[1]		# W-Tag abschneiden
	pubDate = pubDate.replace('GMT', '')	# GMT entf.
	pubDate = pubDate.strip()
	PLog(pubDate)
	try:
		datetime_object = datetime.strptime(pubDate, '%d %b %Y %H:%M:%S')		
		PLog(datetime_object)
		new_date = datetime_object.strftime("%d.%m.%Y %H:%M")
		PLog(new_date)
	except Exception as exception:			# attribute of type 'NoneType' is not callable
		PLog(str(exception))
		new_date = pubDate_org				# unverändert zurück
	return new_date	
#---------------------------------------------------------------- 	
# Holt User-Eingabe für Suche ab
#	s.a. get_query (für Search , ZDF_Search)
def get_keyboard_input():
	kb = xbmc.Keyboard('', 'Bitte Suchwort(e) eingeben')
	kb.doModal() # Onscreen keyboard
	if kb.isConfirmed() == False:
		return ""
	inp = kb.getText() # User Eingabe
	return inp	
#----------------------------------------------------------------  
# Wochentage engl./deutsch wg. Problemen mit locale-Setting 
#	für VerpasstWoche, EPG	
def transl_wtag(tag):	
	wt_engl = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
	wt_deutsch = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
	
	wt_ret = tag
	for i in range (len(wt_engl)):
		el = wt_engl[i]
		if el == tag:
			wt_ret = wt_deutsch[i]
			break
	return wt_ret
#----------------------------------------------------------------  
# simpler XML-SRT-Konverter für ARD-Untertitel
#	pathname = os.path.abspath. 
#	vorh. Datei wird überschrieben
# 	Rückgabe outfile bei Erfolg, '' bei Fehlschlag
# https://knowledge.kaltura.com/troubleshooting-srt-files
# Wegen des strptime-Problems unter Kodi verzicht wir auf auf
#	korrekte Zeitübersetzung und ersetzen lediglich
#		1. den Zeitoffset 10 durch 00
#		2. das Sekundenformat 02.000 durch 02,00 (Verzicht auf die letzte Stelle)
# Problem mit dt.datetime.strptime (Kodi: attribute of type 'NoneType' is not callable):
# 	https://forum.kodi.tv/showthread.php?tid=112916
# Migration Python3: s. from __future__ import print_function
# 16.05.2020 Anpassung an Python3, try-except-Block für Einlesen der UT-Datei
#
def xml2srt(infile):
	PLog("xml2srt: " + infile)
	outfile = '%s.srt' % infile
		
	try:
		f = xbmcvfs.File(infile)
		page = f.readBytes()
		f.close()
		page = page.replace('-1:', '00:') 		# xml-Fehler
		# 10-Std.-Offset simpel beseitigen (2 Std. müssten reichen):
		page = (page.replace('"10:', '"00:').replace('"11:', '"01:').replace('"12:', '"02:'))
		ps = blockextract('<tt:p', page)					
	except Exception as exception:
		PLog(str(exception))
		return ''				
		
	try:
		with open(outfile, 'w') as fout:
			for i, p in enumerate(ps):
				begin 	= stringextract('begin="', '"', p)		# "10:00:07.400"
				end 	= stringextract('end="', '"', p)		# "10:00:10.920"			
				ptext	=  blockextract('tt:span style=', p)
				
				begin	= begin[:8] + ',' + begin[9:11]			# ""10:00:07,40"			
				end		= end[:8] + ',' + end[9:11]				# "10:00:10,92"

				print(i+1, file=fout)
				print('%s --> %s' % (begin, end), file=fout)
				# print >>fout, p.text
				for textline in ptext:
					text = stringextract('>', '<', textline) # style="S3">Willkommen zum großen</tt:span>
					print(text, file=fout)
				print(file=fout)
		os.remove(infile)									# Quelldatei entfernen
	except Exception as exception:
		PLog(str(exception))
		outfile = ''
			
	return outfile

#----------------------------------------------------------------
#	Favs / Merkliste dieses Addons einlesen
#	01.04.2020 Erweiterung ext. Merkliste (Netzwerk-Share).
#	18.04.2020 Erweiterung Ordner
#
def ReadFavourites(mode):	
	PLog('ReadFavourites:')
	if mode == 'Favs':
		fname = xbmc.translatePath('special://profile/favourites.xml')
	else:	# 'Merk'
		fname = WATCHFILE
		if SETTINGS.getSetting('pref_merkextern') == 'true':	# externe Merkliste gewählt?
			fname = SETTINGS.getSetting('pref_MerkDest_path')
			if fname == '' or xbmcvfs.exists(fname) == False:
				msg1 = u"externe Merkliste ist eingeschaltet, aber Dateipfad fehlt oder"
				msg2 = "Datei nicht gefunden"
				MyDialog(msg1, msg2, '')
				return []
			
	try:
		if '//' not in fname:
			page = RLoad(fname,abs_path=True)
		else:
			PLog("xbmcvfs_fname: " + fname)
			f = xbmcvfs.File(fname)		# extern - Share		
			page = f.read(); f.close()
			PLog(len(page))				
			page = py2_encode(page)		# für externe Datei erf.
	except Exception as exception:
		PLog(str(exception))
		return []
				
	if mode == 'Favs':
		favs = re.findall("<favourite.*?</favourite>", page)
	else:
		favs = re.findall("<merk.*?</merk>", page)
	# PLog(favs)
	my_favs = []
	for fav in favs:
		if mode ==  'Favs':
			if ADDON_ID not in fav: 	# skip fremde Addons, ID's in merk's wegen 	
				continue				# 	Base64-Kodierung nicht lesbar
		my_favs.append(fav) 
		
	my_ordner = []						# Ordner einlesen
	items = stringextract('<ordnerliste>', '</ordnerliste>', page)
	items =  items.split()
	for item in items:
		my_ordner.append(item.strip())
			
	PLog(len(my_favs)); PLog(len(my_ordner)); 
	return my_favs, my_ordner

#----------------------------------------------------------------
#	Jobliste für Modul epgRecord einlesen
#
def ReadJobs():	
	PLog('ReadJobs:')

	JOBFILE			= os.path.join("%s/jobliste.xml") % ADDON_DATA
	JOBFILE_LOCK	= os.path.join("%s/jobliste.lck") % ADDON_DATA		# Lockfile für Jobliste
	maxLockloops	= 10		# 1 sec bei 10 x xbmc.sleep(100)	
		
	i=0
	while os.path.exists(JOBFILE_LOCK):	
		i=i+1
		if i >= maxLockloops:		# Lock brechen, vermutl. Ruine
			os.remove(JOBFILE_LOCK)
			PLog("break " + JOBFILE_LOCK)
			break
		xbmc.sleep(100)		
			
	try:
		PLog("xbmcvfs_fname: " + JOBFILE)
		f = xbmcvfs.File(JOBFILE)				
		page = f.read(); f.close()
		PLog(len(page))				
		page = py2_encode(page)		# für externe Datei erf.
	except Exception as exception:
		PLog(str(exception))
		return []
				
	jobs = re.findall("<job>(.*?)</job>", page)
	PLog(len(jobs))		
	return jobs

#----------------------------------------------------------------
# holt summary (Inhaltstext) für eine Sendung, abhängig von SETTINGS('pref_load_summary')
#	- Inhaltstext zu Video im Voraus laden. 
#	SETTINGS durch Aufrufer geprüft
#	ID: ARD, ZDF - Podcasts entspr. ARD
# Es wird nur die Webseite ausgewertet, nicht die json-Inhalte der Ladekette.
# Cache: 
#		html-Seite wird in TEXTSTORE gespeichert, Dateiname aus path generiert.
#
# Aufrufer: ZDF: 	ZDF_get_content (für alle ZDF-Rubriken)
#			ARD: 	ARDStart	-> ARDStartRubrik 
#					SendungenAZ, ARDSearchnew, 	ARDStartRubrik,
#					ARDPagination -> get_page_content
#					ARDStartRubrik (Swiper) 
#					ARDVerpasstContent
#			
# Aufruf erfolgt, wenn für eine Sendung kein summary (teasertext, descr, ..) gefunden wird.
#
# Nicht benötigt in ARD-Suche (Search -> SinglePage -> get_sendungen): Ergebnisse 
#	enthalten einen 'teasertext' bzw. 'dachzeile'. Dto. Sendung Verpasst
# 
# Nicht benötigt in ZDF-Suche (ZDF_Search -> ZDF_get_content): Ergebnisse enthalten
#	einen verkürzten 'teaser-text'.
#
# 21.06.2020 zusätzl. Sendedatum pubDate
#	in TEXTSTORE gespeichert wird die ges. html-Seite (vorher nur Text summ)
#
def get_summary_pre(path, ID='ZDF', skip_verf=False, skip_pubDate=False):	
	PLog('get_summary_pre: ' + ID)
	PLog(skip_verf); PLog(skip_pubDate);
	
	if 'Video?bcastId' in path:					# ARDClassic
		fname = path.split('=')[-1]				# ../&documentId=31984002
		fname = "ID_%s" % fname
	else:	
		fname = path.split('/')[-1]
		fname.replace('.html', '')				# .html bei ZDF-Links abschneiden
		
	fpath = os.path.join(TEXTSTORE, fname)
	PLog('fpath: ' + fpath)
	
	summ=''; page=''; pubDate=''
	if os.path.exists(fpath):		# Text lokal laden + zurückgeben
		PLog('lade lokal:') 
		page =  RLoad(fpath, abs_path=True)

	save_new = False
	if page == '' or '<!DOCTYPE html>' not in page: # Format vor 21.06.2020 (nur summ)
		page, msg = get_page(path)	# extern laden
		save_new = True
	if page == '' or 'APOLLO_STATE__ = {}' in page:
		return '', pubDate
	
	# Decodierung plus bei Classic u-Kennz. vor Umlaut-strings (s.u.)
	page = py2_decode(page)
	verf='';
	if 	ID == 'ZDF' or ID == '3sat':
		summ = stringextract('description" content="', '"', page)
		summ = mystrip(summ)
		summ = unescape(summ)
		summ = repl_json_chars(summ)
		#if 'title="Untertitel">UT</abbr>' in page:	# stimmt nicht mit get_formitaeten überein
		#	summ = "UT | " + summ
		if skip_verf == False:
			if u'erfügbar bis' in page:										# enth. Uhrzeit									
				verf = stringextract(u'erfügbar bis ', '<', page)			# Blank bis <
			if verf == '':
				verf = stringextract('plusbar-end-date="', '"', page)
				verf = time_translate(verf, add_hour=0)
			if verf:														# Verfügbar voranstellen
				summ = u"[B]Verfügbar bis [COLOR darkgoldenrod]%s[/COLOR][/B]\n\n%s\n" % (verf, summ)
		PLog(skip_pubDate)
		if skip_pubDate == False:		
			pubDate = stringextract('publicationDate" content="', '"', page)# Bsp. 2020-06-15T22:51:28.328+02:00
			if pubDate == '':
				pubDate = stringextract('<time datetime="', '"', page)		# Alternative wie oben
			if pubDate:
				pubDate = time_translate(pubDate)
				pubDate = " | Sendedatum: [COLOR blue]%s Uhr[/COLOR]\n\n" % pubDate	
				if u'erfügbar bis' in summ:	
					summ = summ.replace('\n\n', pubDate)					# zwischen Verfügbar + summ  einsetzen
				else:
					summ = "%s%s" % (pubDate[3:], summ)
		
	if 	ID == 'ARDnew':
		page = page.replace('\\"', '*')									# Quotierung vor " entfernen, Bsp. \"query\"
		if '/ard/player/' in path or '/ard/live/' in path:				# json-Inhalt
			summ = stringextract('synopsis":"', '","', page)
		else:									# HTML-Inhalt
			summ = stringextract('synopsis":"', '"', page)
		summ = repl_json_chars(summ)
		if skip_verf == False:
			if 'verfügbar bis:' in page:								# html mit Uhrzeit									
				verf = stringextract('verfügbar bis:', '</p>', page)	# 
				verf = cleanhtml(verf)
			if verf:													# Verfügbar voranstellen
				summ = u"[B]Verfügbar bis [COLOR darkgoldenrod]%s[/COLOR][/B]\n\n%s" % (verf, summ)
		if skip_pubDate == False:		
			pubDate = stringextract('"broadcastedOn":"', '"', page)
			if pubDate:
				pubDate = " | Sendedatum: [COLOR blue]%s Uhr[/COLOR]\n\n" % pubDate	# 
				if 'erfügbar bis' in summ:	
					summ = summ.replace('\n\n', pubDate)					# zwischen Verfügbar + summ  einsetzen
				else:
					summ = "%s%s" % (pubDate[3:], summ)
			
	# für Classic ist u-Kennz. vor Umlaut-strings erforderlich
	if 	ID == 'ARDClassic':
		PLog('Mark2')
		# summ = stringextract('description" content="', '"', page)		# geändert 23.04.2019
		summ = stringextract('itemprop="description">', '<', page)
		summ = unescape(summ)			
		summ = cleanhtml(summ)	
		summ = repl_json_chars(summ)
		PLog('Mark3')
		if skip_verf == False:
			if u'verfügbar bis' in page:										
				verf = stringextract(u'verfügbar bis ', '</', page)		# Blank bis </p>
			if verf:													# Verfügbar voranstellen
				summ = u"[B]Verfügbar bis [COLOR darkgoldenrod]%s[/COLOR][/B]\n\n%s" % (verf, summ)
		PLog('Mark4')
		if skip_pubDate == False:		
			pubDate = stringextract('Video der Sendung vom', '</', page)# pageHeadline hidden
			if pubDate:
				pubDate = " | Sendedatum: [COLOR blue]%s[/COLOR]\n\n" % pubDate	# "Uhr" in Quelle
				if u'erfügbar bis' in summ:	
					summ = summ.replace('\n\n', pubDate)					# zwischen Verfügbar + summ  einsetzen
				else:
					summ = "%s%s" % (pubDate[3:], summ)
			PLog('Mark5')
				
		 	
	PLog('summ:' + summ); PLog(verf)
	if summ and save_new:
		msg = RSave(fpath, page)
	# PLog(msg)
	return summ
	
#-----------------------------------------------
# Aufrufer : SenderLiveListe, ZDFStartLive, get_live_data (Arte),
#			Live (3sat), Kika_Live.
# ermittelt master.m3u8 für die ZDF-Sender (Kennz. ZDFsource in
#	livesenderTV.xml). Rückgabe Liste (Zeile: Sender|Url) -
#	Reihenfolge wie Web (www.zdf.de/live-tv).
# Cache 24 Stunden, Datei: zdf_streamlinks im Dict-Ordner - nur
#	außerhalb der Cachezeit wird www.zdf.de/live-tv neu geladen.
#
# Beachte: Blank hinter title_sender zur Abgrenz. der ZDF-Sender.
#	Abgleich kompl. Titel nicht sicher (Bsp. 2 Blanks bei Arte)
# 26.06.2020 skip_log hinzugefügt (relevant für loop in 
#	get_sort_playlist)
#-----------------------------------------------
def get_ZDFstreamlinks(skip_log=False):
	PLog('get_ZDFstreamlinks:')
	ZDFlinks_CacheTime	= 86400					# 24 Std.: (60*60)*24
		
	page = Dict("load", 'zdf_streamlinks', CacheTime=ZDFlinks_CacheTime)
	if len(str(page)) > 1000:					# bei Error nicht leer od. False von Dict
		if skip_log == False:
			PLog(page)							# für IPTV-Interessenten
		return page.splitlines()

	page, msg = get_page(path='https://www.zdf.de/live-tv')			# Links neu holen
	if page == '':
		PLog('get_ZDFstreamlinks: leer')
		return []

	page = page.replace('content": "', '"content":"')
	page = page.replace('apiToken": "', '"apiToken":"')
	content = blockextract('js-livetv-scroller-cell', page)			# Playerdaten einschl. apiToken
	PLog("len_content: %d" % len(content))
	apiToken = stringextract('"apiToken":"', '"', page)				# für alle identisch
	PLog("apiToken: " + apiToken[:80] + "..")
	header = "{'Api-Auth': 'Bearer %s','Host': 'api.zdf.de'}" % apiToken
	
	zdf_streamlinks=[]
	for rec in content:												# Schleife  Web-Sätze		
		player2_url=''; assetid=''; videodat_url=''; apiToken=''; href=''
		title = stringextract('visuallyhidden">', '<', rec)
		PLog(title);
		# Bsp.: api.zdf.de/../zdfinfo-live-beitrag-100.json?profile=player2:
		player2_url = stringextract('"content":"', '"', rec)

		thumb 	= stringextract('data-src="', '"', rec)			# erstes img = größtes
		geo		= stringextract('geolocation="', '"', rec)
		if geo:
			geo = "Geoblock: %s" % geo
		fsk		= stringextract('-fsk="', '"', rec)
		if fsk:
			fsk = "FSK: %s" % fsk
			fsk = fsk.replace('none', 'ohne')
		tagline = "%s,  %s" % (geo, fsk)

		PLog("player2_url: " + player2_url)
		if player2_url:
			page, msg = get_page(path=player2_url, header=header, JsonPage=True)
			# Bsp.: 247onAir-203
			assetid = stringextract('assetid":"', '"', page)
			assetid = assetid.strip()
			
		PLog(assetid); 
		if assetid:
			videodat_url = "https://api.zdf.de/tmd/2/ngplayer_2_3/live/ptmd/%s" % assetid
			page, msg	= get_page(path=videodat_url, header=header, JsonPage=True)
			PLog("videodat: " + page[:40])
		
			href = stringextract('"https://',  'master.m3u8', page) 	# 1.: auto
			if href:
				href = 	"https://" + href + "master.m3u8"
				# Zeile: "title_sender|href|thumb|tagline"
				zdf_streamlinks.append("%s|%s|%s|%s" % (title, href,thumb,tagline))	
	
	PLog("zdf_streamlinks: %d" % len(zdf_streamlinks))
	page = "\n".join(zdf_streamlinks)									# Ablage Cache
	if skip_log == False:
		PLog(page)														# für IPTV-Interessenten
	Dict("store", 'zdf_streamlinks', page)
	return zdf_streamlinks	
#---------------------------------------------------------------------------------------------------
# Aufruf: 
# Icon aus livesenderTV.xml holen
# 24.01.2019 erweitert um link
# 25.06.2020 für SenderLiveResolution um EPG_ID erweitert 
# 26.06.2020 Anpassung für ZDF-Sender (bei Classic-Livestreams: 
#	Arte, KiKA, 3sat)
#
def get_playlist_img(hrefsender):
	PLog('get_playlist_img: ' + hrefsender); 
	playlist_img=''; link=''; EPG_ID=''
	playlist = RLoad(PLAYLIST)		
	playlist = blockextract('<item>', playlist)
	for p in playlist:
		title_sender = stringextract('hrefsender>', '</hrefsender', p) 
		s = stringextract('title>', '</title', p)	# Classic-Version
		if s:									# skip Leerstrings
			# PLog(s); PLog(hrefsender);		# Debug
			if up_low(s) in up_low(hrefsender):
				PLog("Treffer:"); PLog(s); PLog(hrefsender);
				playlist_img = stringextract('thumbnail>', '</thumbnail', p)
				playlist_img = R(playlist_img)
				link =  stringextract('link>', '</link', p)
				if "ZDFsource" in link:			# Anpassung für ZDF-Sender
					zdf_streamlinks = get_ZDFstreamlinks(skip_log=True)
					link=''	
					# Zeile zdf_streamlinks: "webtitle|href|thumb|tagline"
					for line in zdf_streamlinks:
						items = line.split('|')
						# Bsp.: "ZDFneo " in "ZDFneo Livestream":
						if up_low(title_sender) in up_low(items[0]): 
							link = items[1]
					if link == '':
						PLog('%s: Streamlink fehlt' % title_sender)			
					
				EPG_ID =  stringextract('EPG_ID>', '</EPG_ID', p)
				PLog("EPG_ID für %s: %s" % (s, EPG_ID))
				break
	if EPG_ID == '':
		PLog("%s: EPG_ID nicht gefunden/vorhanden" % s)
	PLog(playlist_img); PLog(link); 
	return playlist_img, link, EPG_ID

#---------------------------------------------------------------------------------------------------
# Link für TV-Livesender aus ARD-Start holen - z.Z. nur Classic
#	Aufrufer: ARDStartRubrik, SenderLiveResolution (Fallback für
#		 Link in livesenderTV.xml)
def get_startsender(hrefsender):
	PLog('get_startsender: ' + hrefsender); 
	page, msg = get_page(path=hrefsender)	
	config_id =  stringextract('/play/config/', '&', page)
	# Altern.: /play/media/35283076?devicetype=phone&features=hls (weniger Inhalt)
	json_url = BASE_URL + '/play/config/%s?devicetype=phone' % config_id
	
	page, msg = get_page(path=json_url)
	href = stringextract('clipUrl":"', '"', page)
	if href.startswith('http') == False:
		href = 'https:' + href	
	return href
	
####################################################################################################
def MakeDetailText(title, summary,tagline,quality,thumb,url):	# Textdatei für Download-Video / -Podcast
	PLog('MakeDetailText:')
	title=py2_encode(title); summary=py2_encode(summary);
	tagline=py2_encode(tagline); quality=py2_encode(quality);
	thumb=py2_encode(thumb); url=py2_encode(url);
	
	summary=summary.replace('||', '\n'); tagline=tagline.replace('||', '\n');
	PLog(type(title)); PLog(type(summary)); PLog(type(tagline));
	detailtxt = ''
	detailtxt = detailtxt + "%15s" % 'Titel: ' + "'"  + title + "'"  + '\r\n' 
	detailtxt = detailtxt + "%15s" % 'Beschreibung1: ' + "'" + tagline + "'" + '\r\n' 

	if summary != tagline: 
		detailtxt = detailtxt + "%15s" % 'Beschreibung2: ' + "'" + summary + "'"  + '\r\n' 	
	
	detailtxt = detailtxt + "%15s" % 'Qualitaet: ' + "'" + quality + "'"  + '\r\n' 
	detailtxt = detailtxt + "%15s" % 'Bildquelle: ' + "'" + thumb + "'"  + '\r\n' 
	detailtxt = detailtxt + "%15s" % 'Adresse: ' + "'" + url + "'"  + '\r\n' 
	
	return detailtxt
		
#---------------------------------------------------------------------------------------------------
# 30.08.2018 Start Recording TV-Live
#	Problem: autom. Wiedereintritt hier + erneuter Popen-call nach Rückkehr zu TVLiveRecordSender 
#		(Ergebnis-Button nach subprocess.Popen, bei PHT vor Ausführung des Buttons)
#		OS-übergreifender Abgleich der pid problematisch - siehe
#		https://stackoverflow.com/questions/4084322/killing-a-process-created-with-pythons-subprocess-popen
#		Der Wiedereintritt tritt sowohl unter Linux als auch Windows auf.
#		Ursach n.b. - tritt in DownloadExtern mit curl/wget nicht auf.
#	1. Lösung: Verwendung des psutil-Moduls (../Contents/Libraries/Shared/psutil ca. 400 KB)
#		und pid-Abgleich Dict['PID'] gegen psutil.pid_exists(pid) - s.u.
#		verworfen - Modul lässt sich unter Windows nicht laden. Linux OK
#	2. Lösung: Dict['PIDffmpeg'] wird nach subprocess.Popen belegt. Beim ungewollten Wiedereintritt
#		wird nach TVLiveRecordSender (Senderliste) zurück gesprungen und Dict['PIDffmpeg'] geleert.
#		Beim nächsten manuellen Aufruf wird LiveRecord wieder frei gegeben ("Türsteherfunktion").
#
#	PHT-Problem: wie in TuneIn2017 (streamripper-Aufruf) sprignt PHT bereits vor dem Ergebnis-Buttons (DirectoryObject)
#		in LiveRecord zurück.
#		Lösung: Ersatz des Ergebnis-Buttons durch return ObjectContainer. PHT steigt allerdings danach mit 
#			"GetDirectory failed" aus (keine Abhilfe bisher). Der ungewollte Wiedereintritt findet trotzdem
#			statt.
#
# 20.12.2018 Plex-Probleme "autom. Wiedereintritt" in Kodi nicht beobachtet (Plex-Sandbox Phänomen?) - Code
#	entfernt.
# 29.04.0219 Erweiterung manuelle Eingabe der Aufnahmedauer
#
# Aufrufer: TVLiveRecordSender, JobMonitor (epgRecord), EPG_ShowAll via Kontextmenü
# 	Check auf ffmpeg-Settings bereits in TVLiveRecordSender, Check auf LiveRecord-Setting
# 		bereits in SenderLiveListePre
# 04.07.2020 angepasst für epgRecord (Eingabe Dauer entf., Dateiname mit Datumformat 
#		geändert, Notification statt Dialog. epgJob enthält mydate (bereits für
#		detailtxt verwendet).
#		duration-Format: Sekunden (statt "00:00:00")
#  		verlagert nach util (import aus  ardundzdf klappt nicht in epgRecord).
#
def LiveRecord(url, title, duration, laenge, epgJob=''):
	PLog('LiveRecord:')
	PLog(url); PLog(title); 	
	PLog('duration: %s, laenge: %s' % (duration, laenge))

	li = xbmcgui.ListItem()
	li = home(li, ID=NAME)					# Home-Button
	
	
	if epgJob == '':								# epgRecord: o. Eingabe Dauer
		if SETTINGS.getSetting('pref_LiveRecord_input') == 'true':	# Aufnahmedauer manuell
			duration = duration[:5]									# 01:00:00, für Dialog kürzen
			dialog = xbmcgui.Dialog()
			duration = dialog.input('Aufnahmedauer eingeben (HH:MM)', duration, type=xbmcgui.INPUT_TIME)
			PLog(duration)
			if duration == '' or duration == ' 0:00':
				msg1 = "Aufnahmedauer fehlt - Abbruch"
				PLog(msg1)
				MyDialog(msg1, '', '')
				return li	
			duration = "%s:00" % duration							# für ffmpeg wieder auffüllen
			laenge = "%s (Stunden:Minuten)" % duration[:5]			# Info nach Start, s.u.
			PLog('manuell_duration: %s, laenge: %s' % (duration, laenge))
			
	dest_path = SETTINGS.getSetting('pref_download_path')
	dest_path = dest_path  							# Downloadverzeichnis fuer curl/wget verwenden
	now = datetime.datetime.now()
	mydate = now.strftime("%Y%m%d_%H%M%S")			# Zeitstempel
	dfname = make_filenames(title)					# Dateiname aus Sendername generieren
	if epgJob:
		dfname = "%s_%s.mp4" % (epgJob, dfname)
	else:
		dfname = "%s_%s.mp4" % (mydate, dfname) 	
	dest_file = os.path.join(dest_path, dfname)
	if url.startswith('http') == False:				# Pfad bilden für lokale m3u8-Datei
		if url.startswith('rtmp') == False:
			url 	= os.path.join(M3U8STORE, url)	# rtmp-Url's nicht lokal
			url 	= '"%s"' % url					# Pfad enthält Leerz. - für ffmpeg in "" kleiden						
	
	cmd = SETTINGS.getSetting('pref_LiveRecord_ffmpegCall')	% (url, duration, dest_file)
	PLog("cmd: " + cmd); 
	icon = R("icon-record.png")
	
	PLog(sys.platform)
	if sys.platform == 'win32':							
		args = cmd
	else:
		args = shlex.split(cmd)							
	
	try:
		PIDffmpeg = ''
		sp = subprocess.Popen(args, shell=False)
		PLog('sp: ' + str(sp))

		if str(sp).find('object at') > 0:  			# subprocess.Popen object OK
			PIDffmpeg = sp.pid					# PID speichern bei Bedarf
			PLog('PIDffmpeg neu: %s' % PIDffmpeg)
			Dict('store', 'PIDffmpeg', PIDffmpeg)
			msg1 = 'Aufnahme gestartet:'
			msg2 = dfname
			# msg3 = "Aufnahmedauer: %s" % laenge
			PLog('Aufnahme gestartet: %s' % dfname)	
			# MyDialog(msg1, msg2, msg3)
			xbmcgui.Dialog().notification(msg1, msg2,icon,3000)
			return PIDffmpeg			
				
	
	except Exception as exception:
		msg = str(exception)
		PLog(msg)		
		msg1 ='Aufnahme-Problem'
		msg2 = dfname
		# MyDialog(msg1, msg2, '')
		xbmcgui.Dialog().notification(msg1, msg2,icon,3000)
		return li	
		
####################################################################################################
# PlayVideo aktuell 23.03.2019: 
#	Sofortstart + Resumefunktion, einschl. Anzeige der Medieninfo:
#		nur problemlos, wenn das gewählte Listitem als Video (Playable) gekennzeichnet ist.
# 		mediatype steuert die Videokennz. im Listing - abhängig von Settings (Sofortstart /
#		Einzelauflösungen).
#		Dasselbe gilt für TV-Livestreams.
#		Param. Merk (added in Watch): True=Video aus Merkliste  
#
# 	Aufruf indirekt (Kennz. Playable): 	
#		ARDStartRubrik, ARDStartSingle, SinglePage (Ausnahme Podcasts),
#		SingleSendung (außer m3u8_master), SenderLiveListe, 
#		ZDF_get_content, 
#		Modul zdfMobile: PageMenu, SingleRubrik
#							
#	Aufruf direkt: 
#		ARDStartVideoStreams, ARDStartVideoMP4,
#		SingleSendung (m3u8_master), SenderLiveResolution 
#		show_formitaeten (ZDF),
#		Modul zdfMobile: ShowVideo
#
#	Format sub_path s. https://alwinesch.github.io/group__python__xbmcgui__listitem.html#ga24a6b65440083e83e67e5d0fb3379369
#	Die XML-Untertitel der ARD werden gespeichert + nach SRT konvertiert (einschl. minus 10-Std.-Offset)
#	Resume-Funktion Kodi-intern  DB MyVideos107.db, Tab files (idFile, playCount, lastPlayed) + (via key idFile),
#		bookmark (idFile, timelnSeconds, totalTimelnSeconds)
#
def PlayVideo(url, title, thumb, Plot, sub_path=None, Merk='false'):	
	PLog('PlayVideo:'); PLog(url); PLog(title);	 PLog(Plot[:100]); 
	PLog(sub_path);
	
	Plot=transl_doubleUTF8(Plot)
	Plot=(Plot.replace('[B]', '').replace('[/B]', ''))	# Kodi-Problem: [/B] wird am Info-Ende platziert
	url=url.replace('\\u002F', '/')						# json-Pfad noch unbehandelt
	
	li = xbmcgui.ListItem(path=url)		
	# li.setArt({'thumb': thumb, 'icon': thumb})
	li.setArt({'poster': thumb, 'banner': thumb, 'thumb': thumb, 'icon': thumb, 'fanart': thumb})	
	
	Plot=Plot.replace('||', '\n')				# || Code für LF (\n scheitert in router)
	# li.setProperty('IsPlayable', 'true')		# hier unwirksam
	# li.setInfo(type="video", infoLabels={"Title": title, "Plot": Plot, "mediatype": "video"}) # s.u.

	infoLabels = {}
	infoLabels['title'] = title
	infoLabels['sorttitle'] = title
	#infoLabels['genre'] = genre
	#infoLabels['plot'] = Plot
	#infoLabels['plotoutline'] = Plot
	infoLabels['tvshowtitle'] = Plot
	infoLabels['tagline'] = Plot
	infoLabels['mediatype'] = 'video'
	li.setInfo(type="Video", infoLabels=infoLabels)
	
	# Info aus GetZDFVideoSources hierher verlagert - wurde von Kodi nach Videostart 
	#	erneut gezeigt - dto. für ARD (parseLinks_Mp4_Rtmp, ARDStartSingle)
	if SETTINGS.getSetting('pref_UT_Info') == 'true' or SETTINGS.getSetting('pref_UT_ON') == 'true':
		if sub_path:							# Vorbehandlung ARD-Untertitel
			if 'ardmediathek.de' in sub_path:	# ARD-Untertitel speichern + Endung -> .sub
				local_path = "%s/%s" % (SUBTITLESTORE, sub_path.split('/')[-1])
				local_path = os.path.abspath(local_path)
				try:
					urlretrieve(sub_path, local_path)
				except Exception as exception:
					PLog(str(exception))
					local_path = ''
				if 	local_path:
					sub_path = xml2srt(local_path)	# Konvert. für Kodi leer bei Fehlschlag

	PLog('sub_path: ' + str(sub_path));		
	if sub_path:							# Untertitel aktivieren, falls vorh.	
		if SETTINGS.getSetting('pref_UT_Info') == 'true':
			msg1 = 'Info: für dieses Video stehen Untertitel zur Verfügung.' 
			MyDialog(msg1, '', '')
			
		if SETTINGS.getSetting('pref_UT_ON') == 'true':
			sub_path = 	sub_path.split('|')											
			li.setSubtitles(sub_path)
			xbmc.Player().showSubtitles(True)		
		
	# Abfrage: ist gewähltes ListItem als Video deklariert? - Falls ja,	
	#	erfolgt der Aufruf indirekt (setResolvedUrl). Falls nein,
	#	wird der Player direkt aufgerufen. Direkter Aufruf ohne IsPlayable-Eigenschaft 
	#	verhindert Resume-Funktion.
	# Mit xbmc.Player() ist  die Unterscheidung Kodi V18/V17 nicht mehr erforderlich,
	#	xbmc.Player().updateInfoTag bei Kodi V18 entfällt. 
	# Die Player-Varianten PlayMedia + XBMC.PlayMedia scheitern bei Kommas in Url.	
	# 29.01.2020 sleep verhindert selbständige Restarts nach Stop - Bsp. phoenix/
	#	Sendungen/"Armes Deutschland? Deine Kinder" 
	IsPlayable = xbmc.getInfoLabel('ListItem.Property(IsPlayable)') # 'true' / 'false'
	PLog("IsPlayable: %s, Merk: %s" % (IsPlayable, Merk))
	PLog("kodi_version: " + KODI_VERSION)							# Debug
	# kodi_version = re.search('(\d+)', KODI_VERSION).group(0) # Major-Version reicht hier - entfällt
	
	
	if url_check(url, caller='PlayVideo'):
		if IsPlayable == 'true':								# true - Call via listitem
			PLog('PlayVideo_Start: listitem')
			xbmcplugin.setResolvedUrl(HANDLE, True, li)			# indirekt
		else:													# false, None od. Blank
			PLog('PlayVideo_Start: direkt')
			xbmc.Player().play(url, li, windowed=False) 		# direkter Start
			sleep(50 / 100)
			return

#---------------------------------------------------------------- 
# SSL-Probleme in Kodi mit https-Code 302 (Adresse verlagert) - Lösung:
#	 Redirect-Abfrage vor Abgabe an Kodi-Player
# Kommt vor: Kodi kann lokale Audiodatei nicht laden - Kodi-Neustart ausreichend.
# 30.12.2018  Radio-Live-Sender: bei den SSL-Links kommt der Kodi-Audio-Player auch bei der 
#	weiter geleiteten Url lediglich mit  BR, Bremen, SR, Deutschlandfunk klar. Abhilfe:
#	Wir ersetzen den https-Anteil im Link durch den http-Anteil, der auch bei tunein 
#	verwendet wird. Der Link wird bei addradio.de getrennt und mit dem http-template
#	verbunden. Der Sendername wird aus dem abgetrennten Teil ermittelt und im template
#	eingefügt.
# 	Bsp. (Sender=ndr):
#		template: 		dg-%s-http-fra-dtag-cdn.cast.addradio.de'	# %s -> sender	
#		redirect-Url: 	dg-ndr-https-dus-dtag-cdn.sslcast.addradio.de/ndr/ndr1niedersachsen/..
#		replaced-Url: 	dg-ndr-http-dus-dtag-cdn.cast.addradio.de/ndr/ndr1niedersachsen/..
# url_template gesetzt von RadioAnstalten (Radio-Live-Sender)
# 18.06.2019 Kodi 17.6:  die template-Lösung funktioniert nicht mehr - dto. Redirect - 
#				Code für beides entfernt. Hilft ab er nur bei wenigen Sendern.
#				Neue Kodivers. ansch. nicht betroffen, Kodi 18.2. OK
#			
def PlayAudio(url, title, thumb, Plot, header=None, url_template=None, FavCall=''):
	PLog('PlayAudio:'); PLog(title); PLog(FavCall); 
	Plot=transl_doubleUTF8(Plot)
				
	if url.startswith('http') == False:			# lokale Datei
		if url.startswith('smb://') == False:	# keine Share
			url = os.path.abspath(url)
	
	PLog('Player_Url: ' + url)

	li = xbmcgui.ListItem(path=url)				# ListItem + Player reicht für BR
	li.setArt({'thumb': thumb, 'icon': thumb})
	ilabels = ({'Title': title})
	ilabels.update({'Comment': '%s' % Plot})	# Plot im MusicPlayer nicht verfügbar
	li.setInfo(type="music", infoLabels=ilabels)							
	li.setContentLookup(False)
	
	# optionale Slideshow starten 
	path = SETTINGS.getSetting('pref_slides_path')
	PLog(path)
	slide_mode = SETTINGS.getSetting('pref_musicslideshow') 
	if "Kodi" in slide_mode:
		slide_mode = "Kodi"
	if "Addon" in slide_mode:				
		slide_mode = "Addon"
		
	if slide_mode != "Keine":
		if xbmcvfs.exists(path) == False:
			msg1 = 'Slideshow: %s' % slide_mode
			msg2 = 'Slideshow-Verzeichnis fehlt'
			xbmcgui.Dialog().notification(msg1,msg2,R('icon-stream.png'),4000)
		else:	
			if slide_mode == "Kodi":								# Slideshow Kodi
				xbmc.executebuiltin('SlideShow(%s, "recursive")' % path)
				PLog('Starte_SlideShow1: %s' % path)
				# Konfig: Kodi Player-Einstellungen / Bilder
				xbmc.sleep(200)
				xbmc.Player().play(url, li, False)
				return
			if slide_mode == "Addon":								# Slideshow Addon
				# Absicherung gegen Rekursion nach GetDirectory_Error 
				#	nach exit in SlideShow2 - exit falls STOPFILE 
				#	jünger als 4 sec:
				STOPFILE = os.path.join(DICTSTORE, 'stop_slides')
				if os.path.exists(STOPFILE):							
					now = time.time()
					PLog(now - os.stat(STOPFILE).st_mtime)
					if now - os.stat(STOPFILE).st_mtime < 4:	
						PLog("GetDirectory_Error_Rekursion")
						xbmc.executebuiltin("PreviousMenu")
						return
					else:
						os.remove(STOPFILE)							# Stopdatei entfernen	
				xbmc.Player().play(url, li, False)					# Start vor modaler Slideshow			
				import resources.lib.slides as slides
				PLog('Starte_SlideShow2: %s' % path)
				CWD = SETTINGS.getAddonInfo('path') 					# working dir
				DialogSlides = slides.Slideshow('slides.xml', CWD, 'default')
				DialogSlides.doModal()
				xbmc.Player().stop()					
				del DialogSlides
				PLog("del_DialogSlides")
				return
	else:			
		xbmc.Player().play(url, li, False)						# ohne Slideshow 

#---------------------------------------------------------------- 
# Aufruf: PlayVideo
def url_check(url, caller=''):
	PLog('url_check:')
	if url.startswith('http') == False:		# lokale Datei - kein Check
		return True
		
	UrlopenTimeout = 6
	# Tests:
	# url='http://104.250.149.122:8012'	# Debug: HTTP Error 401: Unauthorized
	# url='http://feeds.soundcloud.com/x'	# HTTP Error 400: Bad Request
	
	req = Request(url)
	try:
		r = urlopen(req, timeout=UrlopenTimeout)
		PLog('Status: ' + str(r.getcode()))
		return True
	except Exception as exception:
		err = str(exception)
		msg1= '%s: Seite nicht erreichbar - Url:' % caller
		msg2 = url
		msg3 = 'Fehler: %s' % err
		PLog(msg3)
		MyDialog(msg1, msg2, msg3)		 			 	 
		return False
	
####################################################################################################

