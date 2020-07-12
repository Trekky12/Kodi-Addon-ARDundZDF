# -*- coding: utf-8 -*-
################################################################################
#				arte.py - Teil von Kodi-Addon-ARDundZDF
#		Kategorien der ArteMediathek auf https://www.arte.tv/de/
#
#	Kompatibilität Python2/Python3: Modul future, Modul kodi-six
#	Auswertung via Strings statt json (Performance)
#
################################################################################
#	Stand: 17.06.2020

# Python3-Kompatibilität:
from __future__ import absolute_import		# sucht erst top-level statt im akt. Verz. 
from __future__ import division				# // -> int, / -> float
from __future__ import print_function		# PYTHON2-Statement -> Funktion
from kodi_six import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs

# o. Auswirkung auf die unicode-Strings in PYTHON3:
from kodi_six.utils import py2_encode, py2_decode

import os, sys, subprocess
PYTHON2 = sys.version_info.major == 2
PYTHON3 = sys.version_info.major == 3
if PYTHON2:
	from urllib import quote, unquote, quote_plus, unquote_plus, urlencode, urlretrieve
	from urllib2 import Request, urlopen, URLError 
	from urlparse import urljoin, urlparse, urlunparse, urlsplit, parse_qs
elif PYTHON3:
	from urllib.parse import quote, unquote, quote_plus, unquote_plus, urlencode, urljoin, urlparse, urlunparse, urlsplit, parse_qs
	from urllib.request import Request, urlopen, urlretrieve
	from urllib.error import URLError


import ardundzdf					# -> get_query,test_downloads, get_ZDFstreamlinks
from resources.lib.util import *
from resources.lib.phoenix import getOnline

# Globals
ArteStartCacheTime 	= 43200					# 12 Std.: (60*60)*12
ArteKatCacheTime	= 43200					# 12 Std.: (60*60)*12

ADDON_ID      	= 'plugin.video.ardundzdf'
SETTINGS 		= xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME    	= SETTINGS.getAddonInfo('name')
SETTINGS_LOC  	= SETTINGS.getAddonInfo('profile')
ADDON_PATH    	= SETTINGS.getAddonInfo('path')	# Basis-Pfad Addon
ADDON_VERSION 	= SETTINGS.getAddonInfo('version')
PLUGIN_URL 		= sys.argv[0]				# plugin://plugin.video.ardundzdf/
HANDLE			= int(sys.argv[1])

USERDATA		= xbmc.translatePath("special://userdata")
ADDON_DATA		= os.path.join("%sardundzdf_data") % USERDATA

if 	check_AddonXml('"xbmc.python" version="3.0.0"'):
	ADDON_DATA	= os.path.join("%s", "%s", "%s") % (USERDATA, "addon_data", ADDON_ID)
WATCHFILE		= os.path.join("%s/merkliste.xml") % ADDON_DATA
DICTSTORE 		= os.path.join("%s/Dict") % ADDON_DATA			# hier nur DICTSTORE genutzt

NAME			= 'ARD und ZDF'

BASE_ARTE		= 'https://www.arte.tv'		# + /de/ nach Bedarf
PLAYLIST 		= 'livesenderTV.xml'	  	# enth. Link für arte-Live											

# Icons
ICON 			= 'icon.png'				# ARD + ZDF
ICON_ARTE		= 'icon-arte_kat.png'			
ICON_DIR_FOLDER	= 'Dir-folder.png'
ICON_MEHR 		= 'icon-mehr.png'
ICON_SEARCH 	= 'arte-suche.png'				
ICON_TVLIVE		= 'tv-arte.png'						
ICON_DIR_FOLDER	= "Dir-folder.png"
# ----------------------------------------------------------------------			
def Main_arte(title='', summ='', descr='',href=''):
	PLog('Main_arte:')
	
	li = xbmcgui.ListItem()
	li = home(li, ID=NAME)			# Home-Button

	title="Suche in Arte-Kategorien"
	fparams="&fparams={}" 
	addDir(li=li, label=title, action="dirList", dirID="resources.lib.arte.arte_Search", fanart=R(ICON_ARTE), 
		thumb=R(ICON_SEARCH), fparams=fparams)
	# ------------------------------------------------------
			
	tag='[B][COLOR red]Arte Livestream[/COLOR][/B]'
	title, summ, descr, vonbis, img, href = get_live_data('ARTE')
	if img == '':
		img = R(ICON_TVLIVE)
	summ_par = summ.replace('\n', '||')	
	title=py2_encode(title); href=py2_encode(href); summ_par=py2_encode(summ_par);
	fparams="&fparams={'href': '%s', 'title': '%s', 'Plot': '%s'}" % (quote(href), quote(title), quote(summ_par))
	addDir(li=li, label=title, action="dirList", dirID="resources.lib.arte.arte_Live", fanart=R(ICON_ARTE),
		thumb=img, fparams=fparams, tagline=tag, summary=summ)

	# ------------------------------------------------------
	title="Kategorien"
	fparams="&fparams={}" 
	addDir(li=li, label=title, action="dirList", dirID="resources.lib.arte.Kategorien", fanart=R(ICON_ARTE), 
		thumb=R(ICON_ARTE), fparams=fparams)
		
	xbmcplugin.endOfDirectory(HANDLE, cacheToDisc=True)	
	
# ----------------------------------------------------------------------
# Nutzung EPG-Modul, Daten von tvtoday		
# die json-Seite enthält ca. 4 Tage EPG - 1. Beitrag=aktuell
# 24.06.2020 Nutzung neue Funktion get_ZDFstreamlinks
#
def get_live_data(name):
	PLog('get_live_data:')

	import resources.lib.EPG as EPG
	rec = EPG.EPG(ID='ARTE', mode='OnlyNow')		# Daten holen
	PLog(len(rec))

	if len(rec) == 0:			
		msg1 = 'Sender %s:' % name 
		msg2 = 'keine EPG-Daten gefunden'
		MyDialog(msg1, msg2, '')
		return li
	
	title='Arte'; summ=''; descr=''; vonbis=''; img=''; href=''
	if len(rec) > 0:
		# href (PRG-Seite) hier n.b.
		img=rec[2]; sname=rec[3]; stime=rec[4]; summ=rec[5]; vonbis=rec[6];
		sname = unescape(sname)
		title = sname
		summ = unescape(summ)
		PLog("title: " + title); 
		summ = "[B]LAUFENDE SENDUNG [COLOR red](%s Uhr)[/COLOR][/B]\n\n%s" % (vonbis, summ)
		title= sname
		try:										# 'list' object in summ möglich - Urs. n.b.
			descr = summ.replace('\n', '||')		# \n aus summ -> ||
		except Exception as exception:	
			PLog(str(exception))
			descr = ''
		PLog(title); PLog(img); PLog(sname); PLog(stime); PLog(vonbis); 

	zdf_streamlinks = ardundzdf.get_ZDFstreamlinks(skip_log=True)
	# Zeile zdf_streamlinks: "webtitle|href|thumb|tagline"
	for line in zdf_streamlinks:
		webtitle, href, thumb, tagline = line.split('|')
		# Bsp.: "ZDFneo " in "ZDFneo Livestream":
		if up_low('Arte ') in up_low(webtitle): 	# Arte mit Blank!
			href = href
			break
					
	if href == '':
		PLog('%s: Streamlink fehlt' % 'Arte ')
	if img == '':
		img = thumb									# Fallback Senderlogo (+ in Main_arte)				
	
	return title, summ, descr, vonbis, img, href

####################################################################################################
# arte - TV-Livestream mit akt. PRG
def arte_Live(href, title, Plot):	
	PLog('arte_Live:')

	li = xbmcgui.ListItem()
	li = home(li, ID='arte')			# Home-Button

	img = ICON_TVLIVE
	if SETTINGS.getSetting('pref_video_direct') == 'true': # or Merk == 'true'	# Sofortstart
		PLog('Sofortstart: phoenix_Live')
		PlayVideo(url=href, title=title, thumb=img, Plot=Plot)
		return	
							
	Plot_par = Plot.replace('\n', '||')
	title=py2_encode(title); href=py2_encode(href); img=py2_encode(img);
	Plot_par=py2_encode(Plot_par);
	label = "Bandbreite und Auflösung automatisch (HLS)"
	tag = Plot.replace('||', '\n')
	fparams="&fparams={'url': '%s', 'title': '%s', 'thumb': '%s', 'Plot': '%s', 'sub_path': '', 'Merk': 'false'}" %\
		(quote_plus(href), quote_plus(title), quote_plus(img), quote_plus(Plot_par))
	addDir(li=li, label=label, action="dirList", dirID="PlayVideo", fanart=img, thumb=img, 
		fparams=fparams, mediatype='video', tagline=tag) 		
	
	li =  ardundzdf.Parseplaylist(li, href, img, geoblock='', descr=Plot)	
	
	xbmcplugin.endOfDirectory(HANDLE, cacheToDisc=True)
		
# ----------------------------------------------------------------------
# Webaufruf: BASE_ARTE + '/de/search/?q=%s
# 	Seite html / json gemischt, Blöcke im html-Bereich ohne img-Url's
# 	Problem: Folgeseiten via Web nicht erreichbar
# Api-Call s.u. (div. Varianten, nur 1 ohne Error 401 / 403)
#
def arte_Search(query='', nextpage=''):
	PLog("arte_Search:")
	if 	query == '':	
		query = ardundzdf.get_query(channel='phoenix')	# unbehandelt
	PLog(query)
	if  query == None or query == '':
		return ""
				
	query=py2_encode(query);
	if nextpage == '':
		nextpage = '1'

	path = 'https://www.arte.tv/guide/api/emac/v3/de/web/data/SEARCH_LISTING/?imageFormats=landscape&mainZonePage=1&query=%s&page=%s&limit=20' %\
		(quote(query), nextpage)

	page, msg = get_page(path=path)	
	if page == '':						
		msg1 = 'Fehler in Suche: %s' % query
		msg2 = msg
		MyDialog(msg1, msg2, '')
		return li
	PLog(len(page))
				
		
	li = xbmcgui.ListItem()
	li = home(li, ID='arte')				# Home-Button

	PLog(len(page))
	# page = page.replace('\\u002F', '/')	# hier nicht erf.	
	page = page.replace('\\"', '*')			# Bsp. "\"Brisant\""

	nexturl = stringextract('nextPage":', ',', page)		# letzte Seite: "", auch "null," möglich
	nextpage = stringextract('page=', '&', nexturl)
	PLog("nextpage: " + nextpage)	

	li = GetContent(li, page, ID='SEARCH')						
		
	
	if nextpage:
		img = R(ICON_MEHR)
		title = u"Weitere Beiträge"
		tag = u"weiter zu Seite %s" % nextpage

		query=py2_encode(query); 
		fparams="&fparams={'query': '%s', 'nextpage': '%s'}" % (quote(query), nextpage)
		addDir(li=li, label=title, action="dirList", dirID="resources.lib.arte.arte_Search", fanart=img, 
			thumb=img, fparams=fparams, tagline=tag)

	xbmcplugin.endOfDirectory(HANDLE, cacheToDisc=True)

# ----------------------------------------------------------------------
# Einzel- und Folgebeiträge auch bei Suche möglich. Viele Einzelbeiträge
#	liegen in der Zukunft, bieten aber kleinen Teaser 
#
def GetContent(li, page, ID):
	PLog("GetContent: " + ID)
	
	if ID == 'SEARCH':
		items = blockextract('"programId"',  page)
	else:
		#items = blockextract('programId":',  page)						# Titel fehlt
		items = blockextract('{"title":"',  page)
	if 	len(items) == 0:
		items = blockextract('"programId"',  page)						# Fallback		 
	PLog(len(items))
	
	mediatype=''														# Default für mehrfach
	if SETTINGS.getSetting('pref_video_direct') == 'true':
		mediatype='video'												# für SingleVideo
	
	for item in items:
		mehrfach = False
			
		title = stringextract('title":"', '"', item)
		title_raw = title 												# für Abgleich in Kategorien
		pid = stringextract('programId":"', '"', item)		
		url = stringextract('url":"', '"', item)	
		subtitle = stringextract('subtitle":"', '"', item)				# null möglich -> ''
		summ = stringextract('Description":"', '"', item)				# shortDescription, Alt.: teaserText
		img_alt = stringextract('caption":"', '"', item)
		
		if subtitle:													# arte verbindet mit -
			title  = "%s - %s" % (title, subtitle)
		
		img = get_img(item)			
								
		dur = stringextract('duration":', ',', item)					# 5869,
		PLog('dur: ' + dur)
		if dur != "null":
			dur = seconds_translate(dur)
		else:
			mehrfach = True												# ohne Dauer -> Mehrfachbeitrag
			
		geo = stringextract('geoblocking":', '},', item)
		geo = "Geoblock-Info: %s" % stringextract('code":"', '"', geo)	# "DE_FR", "ALL"
		
		start=''; end=''
		start_end = stringextract('Verfügbar vom', '"', item)			# kann fehlen
		if start_end:													# beide Zeiten bei Suche, o. Uhrzeit
			# start_end = '[B]Verfügbar vom %s [/B]' % start_end		# Anzeige vereinheitlichen:
			s = start_end.split()
			if len(s) > 0:
				start = s[0]; end = s[2];
		else:															# Zeiten getrennt, mit Uhrzeit
			start = stringextract('start":"', '"', item)	
			end = stringextract('end":"', '"', item)
			start=time_translate(start)
			end=time_translate(end)
		if start and end:
			start_end = '[B]Verfügbar vom [COLOR green]%s[/COLOR] bis [COLOR darkgoldenrod]%s[/COLOR][/B]' % (start, end)	

		upcoming  = stringextract('upcomingDate":"', '"', item)			# null möglich -> ''
		if upcoming:													# check Zukunft
			upcoming = getOnline(upcoming, onlycheck=True)
			PLog("upcoming: " + upcoming)
			if 'Zukunft' in upcoming:
				start_end = "%s:%s" % (start_end, upcoming)	
		
		# Beiträge mit 'id":"auch-interessant', 'code":"BONUS"' - im Web:
		#	"Nächstes Video", "Auch interessant für Sie" - entfallen mit
		#	Api-Calls
		if ID == 'SINGLE_MORE':
			title	= u"[COLOR blue]Mehr: %s[/COLOR]" % title
		
		if mehrfach:
			tag = u"[B]Folgebeiträge[/B]"
		else:
			tag = u"Dauer %s\n\n%s\n%s" % (dur, start_end, geo)
			
		title = repl_json_chars(title); 					# franz. Akzent mögl.
		summ = repl_json_chars(summ)						# -"-
		tag_par = tag.replace('\n', '||')					# || Code für LF (\n scheitert in router)
		
		PLog('Satz:')
		PLog(mehrfach); PLog(pid); PLog(title); PLog(url); PLog(tag[:80]); PLog(summ[:80]); 
		PLog(img); PLog(geo);
		title=py2_encode(title); url=py2_encode(url);
		pid=py2_encode(pid); tag_par=py2_encode(tag_par);
		img=py2_encode(img); summ=py2_encode(summ);
		
		if mystrip(title) == '':							# Müll
			continue
			
		if mehrfach:
			if ID == 'KAT_START':							# mit Url + id zurück zu -> Kategorien
				pid = stringextract('id":"', '"', item) 	# programId hier null
				cat = stringextract('label":"%s"' % title, '}]}', page) 	# Kategorie-Liste ausschneiden
				tag = stringextract('description":"', '"', cat)

				fparams="&fparams={'title':'%s'}" % (quote(title))
				addDir(li=li, label=title, action="dirList", dirID="resources.lib.arte.Kategorien", fanart=img, 
					thumb=img, tagline=tag, fparams=fparams)
			else:
				fparams="&fparams={'url': '%s', 'title': '%s'}" % (quote(url), quote(title))
				addDir(li=li, label=title, action="dirList", dirID="resources.lib.arte.Beitrag_Liste", 
					fanart=img, thumb=img, fparams=fparams, tagline=tag, summary=summ)					
		else:	
			fparams="&fparams={'img':'%s','title':'%s','pid':'%s','tag':'%s','summ':'%s','dur':'%s','geo':'%s'}" %\
				(quote(img), quote(title), quote(pid), quote(tag_par), quote(summ), dur, geo)
			addDir(li=li, label=title, action="dirList", dirID="resources.lib.arte.SingleVideo", 
				fanart=img, thumb=img, fparams=fparams, tagline=tag, summary=summ,  mediatype=mediatype)		
	
	return li
	
# -------------------------------
# holt Bild aus Datensatz
#
def get_img(item):
	PLog("get_img:")
	images = stringextract('resolutions":[', '}],', item)
	images = blockextract('url":', images)
	img=''
	for image in images:
		if 'w":720' in image or 'w":940' in image or 'w":1920' in image:
			img = stringextract('url":"', '",', image)
			break
	if img == '':
		img = R(ICON_DIR_FOLDER)
	
	return img
	
# ----------------------------------------------------------------------
# Folgebeiträge aus GetContent
#	-> GetContent -> SingleVideo
def Beitrag_Liste(url, title):
	PLog("Beitrag_Liste:")

	page, msg = get_page(path=url)	
	if page == '':						
		msg1 = 'Fehler in Beitrag_Liste: %s' % title
		msg2 = msg
		MyDialog(msg1, msg2, '')
		return li
	PLog(len(page))
	
	li = xbmcgui.ListItem()
	li = home(li, ID='arte')				# Home-Button

	pos = page.find('__INITIAL_STATE__ ')	# json-Bereich
	page = page[pos:]
	PLog(len(page))
	page = page.replace('\\u002F', '/')	
	page = page.replace('\\"', '*')			# Bsp. "\"Brisant\""

	li = GetContent(li, page, ID='Beitrag_Liste')	
	
	xbmcplugin.endOfDirectory(HANDLE, cacheToDisc=True)

# ----------------------------------------------------------------------
# holt die Videoquellen -> Sofortstart bzw. Liste der  Auflösungen 
# tag hier || behandelt (s. GetContent)
#
def SingleVideo(img, title, pid, tag, summ, dur, geo):
	PLog("SingleVideo: " + pid)
	title_call = title

	path = 'https://api.arte.tv/api/player/v1/config/de/%s/?autostart=0' % pid
	page, msg = get_page(path)	
	if page == '':						
		msg1 = 'Fehler in SingleVideo: %s' % title
		msg2 = msg
		MyDialog(msg1, msg2, '')
		return li
	PLog(len(page))
	page = page.replace('\\/', '/')
	page = page.replace('\\"', '*')			# Bsp. "\"Brisant\""
	
	li = xbmcgui.ListItem()
	li = home(li, ID='arte')				# Home-Button
	
	formitaeten = blockextract('"id":"H', page) # Bsp. "id":"HTTPS_MQ_1", "id":"HLS_XQ_1"
	PLog(len(formitaeten))
	form_arr = []
	for rec in formitaeten:	
		r = []
		mediaType = stringextract('"mediaType":"',  '"', rec)
		bitrate = stringextract('"bitrate":',  ',', rec)
		quality = stringextract('"quality":"',  '"', rec)
		width = stringextract('"width":',  ',', rec)
		height = stringextract('"height":',  ',', rec)
		size = "%sx%s" % (width, height)
		url = stringextract('"url":"',  '"', rec)
		lang = stringextract('"versionLibelle":"',  '"', rec)# z.B. Deutsch (Original)
		lang = transl_json(lang)
		
		# versch. Streams möglich (franz, UT, ..) - in Konzert-Streams
		#	alle Streams erlauben, sonst nur Deutsch + Originalfassung:
		if 'Deutsch' in lang or 'Originalfassung' in lang or '/concert/' in url:							
			lang = lang.replace('Deutsch', '')					# aus Platzgr. entf.
			r.append(mediaType); r.append(bitrate);
			r.append(size); r.append(quality); 
			r.append(url); r.append(lang);
			form_arr.append(r)
		else:
			continue
						
		if 'master.m3u8' in rec:				# master.m3u8 für Sofortstart holen
			href_m3u8 = stringextract('url":"', '"', rec)

	form_arr.sort()								# Sortieren
	if len(form_arr) == 0:
		msg1 = 'Fehler in SingleVideo: %s' % title
		msg2 = 'keine verwertbaren Streams gefunden'
		MyDialog(msg1, msg2, '')
		return li		
			
	Plot_par = tag
	if summ:
		Plot_par = "%s||||%s" % (tag, summ)
	if SETTINGS.getSetting('pref_video_direct') == 'true': 	# or Merk == 'true':	# Sofortstart
		PLog('Sofortstart: arte SingleVideo')
		li.setProperty('IsPlayable', 'false')				# verhindert wiederh. Starten nach Stop
		PlayVideo(url=href_m3u8, title=title, thumb=img, Plot=Plot_par)
		return

	download_list = []						# 2-teilige Liste für Download: 'Titel # url'		
	for rec in form_arr:					# alle Video-Url ausgeben
		mediaType=rec[0];  bitrate=rec[1]
		size = rec[2]; quality=rec[3]; 
		url=rec[4]; lang=rec[5]
		
		PLog('Mark3')
		if 'master.m3u8' in url:
			quality = quality + ' (auto)'
		title = u"Typ: %s, Bitrate: %s, %s, %s" % (up_low(mediaType), bitrate, size, quality)
		if lang:
			title = "%s | %s" % (title, lang)
		if 'mp4' in mediaType:
			download_list.append(title + '#' + url)	# Download-Liste füllen	
	
		PLog('Satz:')
		PLog(title); PLog(url);
		thumb = img
		tag = tag.replace('||', '\n')
		title_call=py2_encode(title_call)
		title=py2_encode(title); url=py2_encode(url);
		thumb=py2_encode(thumb); Plot_par=py2_encode(Plot_par); 
		fparams="&fparams={'url': '%s', 'title': '%s', 'thumb': '%s', 'Plot': '%s'}" %\
			(quote_plus(url), quote_plus(title_call), quote_plus(thumb), quote_plus(Plot_par))	
		addDir(li=li, label=title, action="dirList", dirID="PlayVideo", fanart=thumb, thumb=thumb, fparams=fparams, 
			mediatype='video', tagline=tag) 
			
	PLog(download_list[0])
	if 	download_list:	# Downloadbutton(s), high=0: 1. Video = höchste Qualität	
		# Qualitäts-Index high: hier Basis Bitrate (s.o.)
		title_org = title_call
		summary_org = summ
		tagline_org = repl_json_chars(tag)
		# PLog(summary_org);PLog(tagline_org);PLog(thumb);
		li = ardundzdf.test_downloads(li,download_list,title_org,summary_org,tagline_org,thumb,high=0)  
	
	
	xbmcplugin.endOfDirectory(HANDLE, cacheToDisc=True)
# ----------------------------------------------------------------------
# Cachezeit 12 Std. - Startseite wird nur zum Auslesen der Kategorien
#	verwendet -> GetContent (1. Stufe)
# GetContent -> Kategorien mit Titel der Kategorie  (2. Stufe)
# Hinw.: die Listen aller Subkats befinden sich sowohl in BASE_ARTE 
#	als auch in den einz. SubKats - alle ohne Bilder
#
def Kategorien(title=''):
	PLog("Kategorien: " + title)

	li = xbmcgui.ListItem()
	li = home(li, ID='arte')						# Home-Button
	
	page = Dict("load", 'ArteStart', CacheTime=ArteStartCacheTime)	
	if page == False:								# nicht vorhanden oder zu alt
		page, msg = get_page(path=BASE_ARTE+'/de/')	
		if page == '':						
			msg1 = 'Fehler in Kategorien: %s' % title
			msg2 = msg
			msg2 = u"Seite weder im Cache noch im Web verfügbar"
			MyDialog(msg1, msg2, '')
			return li
		else:
			pos = page.find('__INITIAL_STATE__ ')	# json-Bereich
			page = page[pos:]
			page = page.replace('\\u002F', '/')	
			page = page.replace('\\"', '*')			# Bsp. "\"Brisant\""
			Dict("store", 'ArteStart', page) 		# Seite -> Cache: aktualisieren				
	PLog(len(page))
	
	if title == '':									# 1. Stufe: Kategorien listen
		PLog('Stufe1:')	
		pos = page.find(':"Alle Kategorien"')		
		PLog(pos)
		page = page[pos:]
		PLog(page[:100])
		
		# Kategorien listen
		# GetContent: eigenes ListItem mit Titel (raw) -> KatSub 
		li = GetContent(li, page, ID='KAT_START') 	# eigenes ListItem
		
	else:											# 2. Stufe: Subkats von title listen
		PLog('Stufe2:')		
		pos = page.find('"categories":')			# Listen Subkats am Seitenende o. Bilder
		PLog(pos)
		page = page[pos:]
		PLog(page[:100])
		
		# zum Titel passende Liste suchen:
		page = stringextract('label":"%s"' % title, '}]}', page) 	# Liste ausschneiden
		PLog(page[:100])
		if page == '':						
			msg1 = 'Kategorie nicht gefunden: %s' % title
			MyDialog(msg1, '', '')
			return 
		
		items = blockextract('{"id":"',  page)	
		
		
		for item in items:
			title = stringextract('label":"', '"', item)
			url = stringextract('url":"', '"', item)
			summ = stringextract('escription":"', '"', item)
			pid = stringextract('id":"', '"', item)
			
			# 1. Bild der Subkat aus dem Cache laden, o. Rücksicht auf 
			#	Alter (Bild nur stellvertretend für gesamte Subkat)
			#	bei Cache-miss ICON_DIR_FOLDER . Subkats-Listen ohne img.
			#	Sonderfall arte-concert (mehrere Seiten möglich).
			img = R(ICON_DIR_FOLDER)					# Default 
			page = Dict("load", 'ArteKat_%s' % pid)  	# Normalfall
			if page == False:
				pid = pid.replace('_de', '')			# pid ohne de-Zusatz			
				page = Dict("load", 'ArteKat_%s' % pid) 
			if page == False:							# Special arte-concert
				pid = pid.replace('_de', '')			
				page = Dict("load", 'ArteConcert_%s_page_1' % pid) # Bild von 1. Seite
				
			if page:
				img = get_img(item=page)			
			
			PLog('Satz:');  PLog(title);  PLog(pid); PLog(url);
			
			title=py2_encode(title); url=py2_encode(url);	
			fparams="&fparams={'path': '%s','title':'%s', 'pid':'%s'}" % (quote(url), quote(title), pid)
			addDir(li=li, label=title, action="dirList", dirID="resources.lib.arte.KatSub", fanart=img, 
				thumb=img, summary=summ, fparams=fparams)
	
	xbmcplugin.endOfDirectory(HANDLE, cacheToDisc=True)

# ----------------------------------------------------------------------
# Cachezeit 12 Std. wie Startseite
# listet einzelne Beiträge der Sub-Kategorie title in Datei path
# Hinw.: jede Datei der SubKats enthält die Subkats aller Kategorien
# Sonderfall: Arte Concert - die Url's (nextPage) der folgenden Seiten 
#		ergeben 401-errors. Daher leiten wir SubKats mit /arte-concert/
#		hier aus + verwenden einen Api-Call ähnlich in arte_Search
#		(ermit. in chrome-tools) -> KatSubConcert
#
def KatSub(path, title, pid):
	PLog("KatSub: " + title)
	PLog(pid); PLog(path)
	
	if '/arte-concert/' in path:					# SubKats aus Arte Concert ausleiten
		PLog(path)									# api-Call in KatSubConcert
		return KatSubConcert(title, pid)

	li = xbmcgui.ListItem()
	li = home(li, ID='arte')						# Home-Button
	
	page = Dict("load", 'ArteKat_%s' % pid, CacheTime=ArteKatCacheTime)	
	if page == False:								# nicht vorhanden oder zu alt
		page, msg = get_page(path)	
		if page == '':						
			msg1 = 'Fehler in Kategorien: %s' % title
			msg2 = msg
			msg2 = u"Seite weder im Cache noch im Web verfügbar"
			MyDialog(msg1, msg2, msg3)
			return li
		if 'id="no-content">' in page:				# no-content-Hinweis nur im html-Teil
			msg2 = stringextract('id="no-content">', '</', page)
			if msg2:
				msg1 = 'Arte meldet:'
				MyDialog(msg1, msg2, '')
				return li
		else:
			pos = page.find('__INITIAL_STATE__ ')	# json-Bereich
			page = page[pos:]
			page = page.replace('\\u002F', '/')	
			page = page.replace('\\"', '*')			# Bsp. "\"Brisant\""
			Dict("store", 'ArteKat_%s' % pid, page) # Seite -> Cache: aktualisieren				
	PLog(len(page))
	
													# Start Einzelbeiträge
	# Einzelbeiträge enden bei der Kat-Liste (einschl. SubKats),
	#	Ausnahme: Concert-Subs - hier werten wir alle enth.
	#	Beiträge aus:
	if 'title":"%s"' % title in page:
		page = stringextract('title":"%s"' % title, '"categories":', page)
	PLog(page[:100])
	
	# Kategorien listen
	# GetContent: -> SingleVideo
	li = GetContent(li, page, ID='KAT_SUB') # eigenes ListItem	
	
	xbmcplugin.endOfDirectory(HANDLE, cacheToDisc=True)

# ----------------------------------------------------------------------
# Sonderfall: Arte Concert - s. KatSub
#	Api-Call statt Webseite, Trennung html/json entfällt
#
def KatSubConcert(title, pid, nextpage=''):
	PLog("KatSubConcert: " + pid)
	title_call = title

	li = xbmcgui.ListItem()
	li = home(li, ID='arte')						# Home-Button
	
	pid = pid.replace('_de', '')					# Call mit Zusatz: ohne Daten
	if nextpage == '':
		nextpage = '1'
	path = 'https://www.arte.tv/guide/api/emac/v3/de/web/data/VIDEO_LISTING/?imageFormats=landscape&category=ARS'
	path = path + '&subcategories=%s&videoType=MOST_RECENT&page=%s&limit=20' % (pid, nextpage)
	
	page = Dict("load", 'ArteConcert_%s_page_%s' % (pid, nextpage), CacheTime=ArteKatCacheTime)	
	if page == False:								# nicht vorhanden oder zu alt
		page, msg = get_page(path)	
		if page == '':						
			msg1 = 'Fehler in Kategorien: %s' % title
			msg2 = msg
			msg2 = u"Seite weder im Cache noch im Web verfügbar"
			MyDialog(msg1, msg2, msg3)
			return li
		else:
			page = page.replace('\\"', '*')			# Bsp. "\"Brisant\""
			Dict("store", 'ArteConcert_%s_page_%s' % (pid, nextpage), page) # Seite -> Cache: aktualisieren				
	PLog(len(page))
	
	nexturl = stringextract('nextPage":', ',', page)		# letzte Seite: "", auch "null," möglich
	nextpage = stringextract('page=', '&', nexturl)
	PLog("nextpage: " + nextpage)	
	
	# Abgrenzung zu "categories" (Liste SubKats) hier nicht erforderlich
	li = GetContent(li, page, ID='KatSubConcert')						

	if nextpage:
		img = R(ICON_MEHR)
		title = u"Weitere Beiträge"
		tag = u"weiter zu Seite %s" % nextpage
		
		# Statistik ("datakey":)
		cat = stringextract('category":"', '"', page)
		subcat = stringextract('subcategories":"', '"', page)
		vidtype = stringextract('videoType":"', '"', page)
		PLog('Stat: %s | %s | %s' % (cat, subcat, vidtype))

		title_call=py2_encode(title_call); 
		fparams="&fparams={'title': '%s', 'pid': '%s', 'nextpage': '%s'}" % (quote(title_call), pid, nextpage)
		addDir(li=li, label=title, action="dirList", dirID="resources.lib.arte.KatSubConcert", fanart=img, 
			thumb=img, fparams=fparams, tagline=tag)

	xbmcplugin.endOfDirectory(HANDLE, cacheToDisc=True)

# ----------------------------------------------------------------------

