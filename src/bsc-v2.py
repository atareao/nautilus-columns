#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of nautilus-columns

# this script can installed to the current user account by running the
# following commands:

# sudo apt-get install python-FileManager python-mutagen python-pyexiv2
# python-kaa-metadata

# mkdir ~/.local/share/FileManager-python/extensions/
# cp bsc-v2.py ~/.local/share/FileManager-python/extensions/
# chmod a+x ~/.local/share/FileManager-python/extensions/bsc-v2.py

# alternatively, you can be able to place the script in:
# /usr/share/FileManager-python/extensions/

# change log:
# geb666: original bsc.py, based on work by Giacomo Bordiga
# jmdsdf: version 2 adds extra ID3 and EXIF tag support
# jmdsdf: added better error handling for ID3 tags, added mp3 length support,
#         distinguished between exif image size and true image size
# SabreWolfy: set consistent hh:mm:ss format, fixed bug with no ID3 information
#             throwing an unhandled exception
# jmdsdf: fixed closing file handles with mpinfo (thanks gueba)
# jmdsdf: fixed closing file handles when there's an exception
#         (thanks Pitxyoki)
# jmdsdf: added video parsing (work based on enbeto, thanks!)
# jmdsdf: added FLAC audio parsing through kaa.metadata
#         (thanks for the idea l-x-l)
# jmdsdf: added trackno, added mkv file support (thanks ENigma885)
# jmdsdf: added date/album for flac/video (thanks eldon.t)
# jmdsdf: added wav file support thru pyexiv2
# jmdsdf: added sample rate file support thru mutagen and kaa
#         (thanks for the idea N'ko)
# jmdsdf: fix with tracknumber for FLAC, thanks l-x-l
# draxus: support for pdf files
# arun (engineerarun@gmail.com): made changes to work with naulitus 3.x
# Andrew@webupd8.org: get EXIF support to work with FileManager 3
# Julien Blanc: fix bug caused by missing Exif.Image.Software key
# Andreas Schönfelder: show stars as rating

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import gi
try:
    gi.require_version('Nautilus', '3.0')
    gi.require_version('GObject', '2.0')
except Exception as e:
    print(e)
    exit(1)
from gi.repository import Nautilus as FileManager
from gi.repository import GObject

import urllib
# for id3 support
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MPEGInfo
# for exif support
import pyexiv2
# for reading videos. for future improvement, this can also read mp3!
import kaa.metadata
# for reading image dimensions
# import Image
from PIL import Image
# for reading pdf
from PyPDF2 import PdfFileReader
# locale
import sys
import os
import locale
import gettext

APP = 'nautilus-columns'
ROOTDIR = '/usr/share/'
LANGDIR = os.path.join(ROOTDIR, 'locale-langpack')

try:
    current_locale, encoding = locale.getdefaultlocale()
    language = gettext.translation(APP, LANGDIR, [current_locale])
    language.install()
    if sys.version_info[0] == 3:
        _ = language.gettext
    else:
        _ = language.ugettext
except Exception as e:
    print(e)
    _ = str


class ColumnExtension(GObject.GObject,
                      FileManager.ColumnProvider,
                      FileManager.InfoProvider):
    def __init__(self):
        pass

    def get_columns(self):
        return (
            FileManager.Column(name='FileManagerPython::title_column',
                               attribute='title',
                               label=_('Title'),
                               description=_('Song title')),
            FileManager.Column(name='FileManagerPython::album_column',
                               attribute='album',
                               label=_('Album'),
                               description=_('Album')),
            FileManager.Column(name='FileManagerPython::artist_column',
                               attribute='artist',
                               label=_('Artist'),
                               description=_('Artist')),
            FileManager.Column(name='FileManagerPython::tracknumber_column',
                               attribute='tracknumber',
                               label=_('Track'),
                               description=_('Track number')),
            FileManager.Column(name='FileManagerPython::genre_column',
                               attribute='genre',
                               label=_('Genre'),
                               description=_('Genre')),
            FileManager.Column(name='FileManagerPython::date_column',
                               attribute='date',
                               label=_('Date'),
                               description=_('Date')),
            FileManager.Column(name='FileManagerPython::bitrate_column',
                               attribute='bitrate',
                               label=_('Bitrate'),
                               description=_('Audio Bitrate in kilo bits per \
second')),
            FileManager.Column(name='FileManagerPython::samplerate_column',
                               attribute='samplerate',
                               label=_('Sample rate'),
                               description=_('Sample rate in Hz')),
            FileManager.Column(name='FileManagerPython::length_column',
                               attribute='length',
                               label=_('Length'),
                               description=_('Length of audio')),
            FileManager.Column(name='\
FileManagerPython::exif_datetime_original_column',
                               attribute='exif_datetime_original',
                               label=_('EXIF Dateshot'),
                               description=_('Get the photo capture date from \
EXIF data')),
            FileManager.Column(name='FileManagerPython::exif_software_column',
                               attribute='exif_software',
                               label=_('EXIF Software'),
                               description=_('EXIF - software used to save \
image')),
            FileManager.Column(name='FileManagerPython::exif_flash_column',
                               attribute='exif_flash',
                               label=_('EXIF flash'),
                               description=_('EXIF - flash mode')),
            FileManager.Column(name='\
FileManagerPython::exif_pixeldimensions_column',
                               attribute='exif_pixeldimensions',
                               label=_('EXIF Image Size'),
                               description=_('Image size - pixel dimensions \
as reported by EXIF data')),
            FileManager.Column(name='\
FileManagerPython::width_column',
                               attribute='width',
                               label=_('Width'),
                               description=_('Image/video width (pixel)')),
            FileManager.Column(name='\
FileManagerPython::height_column',
                               attribute='height',
                               label=_('Height'),
                               description=_('Image/video height (pixel)')),
            FileManager.Column(name='FileManagerPython::exif_rating',
                               attribute='exif_rating',
                               label=_('EXIF Rating'),
                               description=_('Rating of the Image as reported \
by EXIF data')),
        )

    def update_file_info(self, file):
        # set defaults to blank
        file.add_string_attribute('title', '')
        file.add_string_attribute('album', '')
        file.add_string_attribute('artist', '')
        file.add_string_attribute('tracknumber', '')
        file.add_string_attribute('genre', '')
        file.add_string_attribute('date', '')
        file.add_string_attribute('bitrate', '')
        file.add_string_attribute('samplerate', '')
        file.add_string_attribute('length', '')
        file.add_string_attribute('exif_datetime_original', '')
        file.add_string_attribute('exif_software', '')
        file.add_string_attribute('exif_flash', '')
        file.add_string_attribute('exif_pixeldimensions', '')
        file.add_string_attribute('exif_rating', '')
        file.add_string_attribute('width', '')
        file.add_string_attribute('height', '')

        if file.get_uri_scheme() != 'file':
            return

        # strip file:// to get absolute path
        filename = urllib.unquote(file.get_uri()[7:])

        # mp3 handling
        if file.is_mime_type('audio/mpeg'):
            # attempt to read ID3 tag
            try:
                audio = EasyID3(filename)
                # sometimes the audio variable will not have one of these items
                # defined, that's why there is this long try / except attempt
                try:
                    if 'title' in audio.keys():
                        file.add_string_attribute('title', audio['title'][0])
                    else:
                        file.add_string_attribute('title', '')
                except Exception:
                    file.add_string_attribute('title', _('Error'))
                try:
                    file.add_string_attribute('album', audio['album'][0])
                except Exception:
                    file.add_string_attribute('album', _('Error'))
                try:
                    file.add_string_attribute('artist', audio['artist'][0])
                except Exception:
                    file.add_string_attribute('artist', _('Error'))
                try:
                    file.add_string_attribute('tracknumber',
                                              audio['tracknumber'][0])
                except Exception:
                    file.add_string_attribute('tracknumber', _('Error'))
                try:
                    file.add_string_attribute('genre', audio['genre'][0])
                except Exception:
                    file.add_string_attribute('genre', _('Error'))
                try:
                    file.add_string_attribute('date', audio['date'][0])
                except Exception:
                    file.add_string_attribute('date', _('Error'))
            except Exception:
                # [SabreWolfy] some files have no ID3 tag and will throw this
                # exception:
                file.add_string_attribute('title', '')
                file.add_string_attribute('album', '')
                file.add_string_attribute('artist', '')
                file.add_string_attribute('tracknumber', '')
                file.add_string_attribute('genre', '')
                file.add_string_attribute('date', '')
            # try to read MP3 information (bitrate, length, samplerate)
            try:
                mpfile = open(filename)
                mpinfo = MPEGInfo(mpfile)
                file.add_string_attribute(
                    'bitrate', str(mpinfo.bitrate / 1000) + ' Kbps')
                file.add_string_attribute(
                    'samplerate', str(mpinfo.sample_rate) + ' Hz')
                # [SabreWolfy] added consistent formatting of times in format
                # hh:mm:ss
                # [SabreWolfy[ to allow for correct column sorting by length
                mp3length = '%02i:%02i:%02i' % ((int(mpinfo.length / 3600)),
                                                (int(mpinfo.length / 60 % 60)),
                                                (int(mpinfo.length % 60)))
                mpfile.close()
                file.add_string_attribute('length', mp3length)
            except Exception:
                file.add_string_attribute('bitrate', _('Error'))
                file.add_string_attribute('length', _('Error'))
                file.add_string_attribute('samplerate', _('Error'))
                try:
                    mpfile.close()
                except Exception:
                    pass

        # image handling
        if file.is_mime_type('image/jpeg') or\
                file.is_mime_type('image/png') or\
                file.is_mime_type('image/gif') or\
                file.is_mime_type('image/bmp'):
            # EXIF handling routines
            try:
                metadata = pyexiv2.ImageMetadata(filename)
                metadata.read()
                try:
                    exif_datetimeoriginal = metadata['\
Exif.Photo.DateTimeOriginal']
                    file.add_string_attribute(
                        'exif_datetime_original',
                        str(exif_datetimeoriginal.raw_value))
                except Exception:
                    file.add_string_attribute('exif_datetime_original', '')
                try:
                    exif_imagesoftware = metadata['Exif.Image.Software']
                    file.add_string_attribute(
                        'exif_software', str(exif_imagesoftware.raw_value))
                except Exception:
                    file.add_string_attribute('exif_software', '')
                try:
                    exif_photoflash = metadata['Exif.Photo.Flash']
                    file.add_string_attribute(
                        'exif_flash', str(exif_photoflash.raw_value))
                except Exception:
                    file.add_string_attribute('exif_flash', '')
                try:
                    exif_pixelydimension = metadata['\
Exif.Photo.PixelYDimension']
                    exif_pixelxdimension = metadata['\
Exif.Photo.PixelXDimension']
                    file.add_string_attribute(
                        'exif_pixeldimensions',
                        str(exif_pixelydimension.raw_value) + 'x' +
                        str(exif_pixelxdimension.raw_value))
                except Exception:
                    file.add_string_attribute('exif_pixeldimensions', '')
                try:
                    exif_rating = metadata['Xmp.xmp.Rating']
                    stars = ''
                    for i in range(1, 6):
                        if i <= int(exif_rating.raw_value):
                            stars += u'\u2605'
                        else:
                            stars += u'\u2606'
                    file.add_string_attribute('exif_rating', stars)
                except Exception:
                    file.add_string_attribute(
                        'exif_rating', u'\u2606\u2606\u2606\u2606\u2606')
            except Exception:
                # no exif data?
                file.add_string_attribute('exif_datetime_original', '')
                file.add_string_attribute('exif_software', '')
                file.add_string_attribute('exif_flash', '')
                file.add_string_attribute('exif_pixeldimensions', '')
                file.add_string_attribute(
                    'exif_rating', u'\u2606\u2606\u2606\u2606\u2606')
            # try read image info directly
            try:
                im = Image.open(filename)
                try:
                    file.add_string_attribute('width', str(im.size[0]))
                except Exception:
                    file.add_string_attribute('width', _('Error'))
                try:
                    file.add_string_attribute('height', str(im.size[1]))
                except Exception:
                    file.add_string_attribute('height', _('Error'))
            except Exception:
                file.add_string_attribute('width', '')
                file.add_string_attribute('height', '')

        # video/flac handling
        if file.is_mime_type('video/x-msvideo') or\
                file.is_mime_type('video/mpeg') or\
                file.is_mime_type('video/x-ms-wmv') or\
                file.is_mime_type('video/mp4') or\
                file.is_mime_type('audio/x-flac') or\
                file.is_mime_type('video/x-flv') or\
                file.is_mime_type('video/x-matroska') or\
                file.is_mime_type('audio/x-wav'):
            try:
                info = kaa.metadata.parse(filename)
                try:
                    file.add_string_attribute(
                        'length',
                        '%02i:%02i:%02i' % ((int(info.length / 3600)),
                                            (int(info.length / 60 % 60)),
                                            (int(info.length % 60))))
                except Exception:
                    file.add_string_attribute('length', _('Error'))
                try:
                    file.add_string_attribute('width',
                                              str(info.video[0].width))
                except Exception:
                    file.add_string_attribute('height', _('Error'))
                try:
                    file.add_string_attribute('height',
                                              str(info.video[0].height))
                except Exception:
                    file.add_string_attribute('width', _('Error'))
                try:
                    file.add_string_attribute(
                        'bitrate', str(round(info.audio[0].bitrate / 1000)))
                except Exception:
                    file.add_string_attribute('bitrate', _('Error'))
                try:
                    file.add_string_attribute(
                        'samplerate',
                        str(int(info.audio[0].samplerate)) + _(' Hz'))
                except Exception:
                    file.add_string_attribute('samplerate', _('Error'))
                try:
                    file.add_string_attribute('title', info.title)
                except Exception:
                    file.add_string_attribute('title', _('Error'))
                try:
                    file.add_string_attribute('artist', info.artist)
                except Exception:
                    file.add_string_attribute('artist', _('Error'))
                try:
                    file.add_string_attribute('genre', info.genre)
                except Exception:
                    file.add_string_attribute('genre', _('Error'))
                try:
                    file.add_string_attribute('tracknumber', info.trackno)
                except Exception:
                    file.add_string_attribute('tracknumber', _('Error'))
                try:
                    file.add_string_attribute('date', info.userdate)
                except Exception:
                    file.add_string_attribute('date', _('Error'))
                try:
                    file.add_string_attribute('album', info.album)
                except Exception:
                    file.add_string_attribute('album', _('Error'))
            except Exception:
                file.add_string_attribute('length', _('Error'))
                file.add_string_attribute('width', _('Error'))
                file.add_string_attribute('height', _('Error'))
                file.add_string_attribute('bitrate', _('Error'))
                file.add_string_attribute('samplerate', _('Error'))
                file.add_string_attribute('title', _('Error'))
                file.add_string_attribute('artist', _('Error'))
                file.add_string_attribute('genre', _('Error'))
                file.add_string_attribute('track', _('Error'))
                file.add_string_attribute('date', _('Error'))
                file.add_string_attribute('album', _('Error'))
        # pdf handling
        if file.is_mime_type('application/pdf'):
            try:
                f = open(filename, 'rb')
                pdf = PdfFileReader(f)
                try:
                    file.add_string_attribute('title',
                                              pdf.getDocumentInfo().title)
                except Exception:
                    file.add_string_attribute('title', _('Error'))
                try:
                    file.add_string_attribute('artist',
                                              pdf.getDocumentInfo().author)
                except Exception:
                    file.add_string_attribute('artist', _('Error'))
                f.close()
            except Exception:
                file.add_string_attribute('title', _('Error'))
                file.add_string_attribute('artist', _('Error'))
        self.get_columns()
