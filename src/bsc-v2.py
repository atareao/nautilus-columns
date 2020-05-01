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
    gi.require_version('GExiv2', '0.10')
except Exception as e:
    print(e)
    exit(1)
from gi.repository import Nautilus as FileManager
from gi.repository import GObject
from gi.repository import GExiv2

import urllib
# for id3 support
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MPEGInfo
# for reading image dimensions
from PIL import Image
# for reading pdf
from PyPDF2 import PdfFileReader
# for reading videos. for future improvement, this can also read mp3!
from plumbum import local
from plumbum import CommandNotFound
# locale
import sys
import os
import json
import math
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


def get_resolution_unit(metadata):
    try:
        value = metadata.get_tag_string('Exif.Image.ResolutionUnit')
    except Exception:
        value == -1
    if value == '1':
        return _('No absolute unit of measurement')
    elif value == '2':
        return _('Inch')
    elif value == '3':
        return _('Centimeter')
    return _('Unknown')


def get_orientation(metadata):
    try:
        value = metadata.get_orientation()
    except Exception:
        value == -1
    if value == GExiv2.Orientation.UNSPECIFIED:
        return _('Unknown')
    elif value == GExiv2.Orientation.NORMAL:
        return _('Normal')
    elif value == GExiv2.Orientation.HFLIP or\
            value == GExiv2.Orientation.VFLIP or\
            value == GExiv2.Orientation.ROT_90_HFLIP or\
            value == GExiv2.Orientation.ROT_90_VFLIP:
        return _('Flipped')
    elif value == GExiv2.Orientation.ROT_180:
        return _('180º')
    elif value == GExiv2.Orientation.ROT_90:
        return _('90º')
    elif value == GExiv2.Orientation.ROT_270:
        return _('270º')
    return _('Unknown')


def get_metering_mode(metadata):
    try:
        value = metadata.get_tag_string('Exif.Photo.MeteringMode')
    except Exception:
        value = -1
    if value == '0':
            return _('Unknown')
    elif value == '1':
            return _('Average')
    elif value == '2':
            return _('Center weighted average')
    elif value == '3':
            return _('Spot')
    elif value == '4':
            return _('Multi spot')
    elif value == '5':
            return _('Pattern')
    elif value == '6':
            return _('Partial')
    elif value == '255':
            return _('other ')
    return _('Unknown')


def get_light_source(metadata):
    try:
        value = metadata.get_tag_string('Exif.Photo.LightSource')
    except Exception:
        value = -1
    if value == '0':
            return _('Unknown')
    elif value == '1':
            return _('Daylight')
    elif value == '2':
            return _('Fluorescent')
    elif value == '3':
            return _('Tungsten (incandescent light)')
    elif value == '4':
            return _('Flash')
    elif value == '9':
            return _('Fine weather')
    elif value == '10':
            return _('Cloudy weather')
    elif value == '11':
            return _('Shade')
    elif value == '12':
            return _('Daylight fluorescent (D 5700 - 7100K)')
    elif value == '13':
            return _('Day white fluorescent (N 4600 - 5400K)')
    elif value == '14':
            return _('Cool white fluorescent (W 3900 - 4500K)')
    elif value == '15':
            return _('White fluorescent (WW 3200 - 3700K)')
    elif value == '17':
            return _('Standard light A')
    elif value == '18':
            return _('Standard light B')
    elif value == '19':
            return _('Standard light C')
    elif value == '20':
            return _('D55')
    elif value == '21':
            return _('D65')
    elif value == '22':
            return _('D75')
    elif value == '23':
            return _('D50')
    elif value == '24':
            return _('ISO studio tungsten')
    elif value == '255':
            return _('Other light source')
    return _('Unknown')


def get_exposure_mode(metadata):
    try:
        value = metadata.get_tag_string('Exif.Photo.ExposureMode')
    except Exception:
        value = -1
    if value == '0':
        return _('Auto exposure')
    elif value == '1':
        return _('Manual exposure')
    elif value == '2':
        return _('Auto bracket')
    return _('Unknown')


def get_gain_control(metadata):
    try:
        value = metadata.get_tag_string('Exif.Photo.GainControl')
    except Exception:
        value = -1
    if value == '0':
        return _('None')
    elif value == '1':
        return _('Low Gain Up')
    elif value == '2':
        return _('High Gain Up')
    elif value == '3':
        return _('Low Gain Down')
    elif value == '4':
        return _('High Gain Down')
    return _('Unknown')


def get_flash(metadata):
    try:
        value = metadata.get_tag_string('Exif.Photo.Flash')
    except Exception:
        value = -1
    if value == '0':
        return _('Flash did not fire')
    elif value == '1':
        return _('Flash fired')
    elif value == '2':
        return _('Strobe return light detected')
    elif value == '4':
        return _('Strobe return light not detected')
    elif value == '8':
        return _('Compulsory flash mode')
    elif value == '16':
        return _('Auto mode')
    elif value == '32':
        return _('No flash function')
    elif value == '64':
        return _('Red eye reduction mode')
    return _('Unknown')


class MediaInfo:
    """
    MediaInfo wraps the mediainfo command and pulls the data into an object
    form:
        metadata=MediaInfo('multimedia-file.mov')
    """

    def __init__(self, path_to_video):
        self.path_to_video = path_to_video

        try:
            mediainfo = local['mediainfo']
        except CommandNotFound:
            raise IOError('mediainfo not found.')

        if os.path.isfile(path_to_video):
            options = ['--Output=JSON', '-f', path_to_video]
            data = json.loads(MediaInfo(options))
            for medatada in data['media']['track']:
                if metadata['@type'] == 'General':
                    metadata = data['media']['track'][0]
                    self._format = metadata.get('Format', _('Unknown'))
                    self._duration = metadata.get('Duration', -1)
                    self._overallbitrate = metadata.get('OverallBitRate', _('Unknown'))
                    self._framerate = metadata.get('FrameRate', _('Unknown'))
                    self._framecount = metadata.get('FrameCount', _('Unknown'))
                elif metadata['@type'] == 'Video':
                    self._videoformat = metadata.get('Format', _('Unknown'))
                    self._width = metadata.get('Width', _('Unknown'))
                    self._height = metadata.get('Height', _('Unknown'))
                    self._bitdepth = metadata.get('BitDepth', _('Unknown'))
                elif metadata['@type'] == 'Audio':
                    self._audioformat = metadata.get('Format', _('Unknown'))
        else:
            self._format = _('Unknown')
            self._duration = _('Unknown')
            self._overallbitrate = _('Unknown')
            self._framerate = _('Unknown')
            self._framecount = _('Unknown')
            self._videoformat = _('Unknown')
            self._width = _('Unknown')
            self._height = _('Unknown')
            self._bitdepth = _('Unknown')
            self._audioformat = _('Unknown')

    def get_format(self):
        """TODO: Docstring for get_format.

        :f: TODO
        :returns: TODO

        """
        return self._format

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
            # Images
            FileManager.Column(name='FileManagerPython::exposure_time_column',
                               attribute='exposure_time',
                               label=_('Exposure time'),
                               description=_('Exposure time in seconds')),
            FileManager.Column(name='FileManagerPython::fnumber_column',
                               attribute='fnumber',
                               label=_('F number'),
                               description=_('Exposure F number')),
            FileManager.Column(name='FileManagerPython::fnumber_focal_length',
                               attribute='focal_length',
                               label=_('Focal length'),
                               description=_('The actual focal length of the \
lens, in mm.')),
            FileManager.Column(name='FileManagerPython::gps_altitude_column',
                               attribute='gps_altitude',
                               label=_('Altitude'),
                               description=_('GPS Altitude')),
            FileManager.Column(name='FileManagerPython::gps_latitude_column',
                               attribute='gps_latitude',
                               label=_('Latitude'),
                               description=_('GPS Latitude')),
            FileManager.Column(name='FileManagerPython::gps_longitude_column',
                               attribute='gps_longitude',
                               label=_('Longitude'),
                               description=_('GPS Longitude')),
            FileManager.Column(name='FileManagerPython::iso_speed_column',
                               attribute='iso_speed',
                               label=_('ISO'),
                               description=_('ISO Speed')),
            FileManager.Column(name='FileManagerPython::orientation_column',
                               attribute='orientation',
                               label=_('Orientation'),
                               description=_('Orientation')),
            FileManager.Column(name='FileManagerPython::model_column',
                               attribute='model',
                               label=_('Model'),
                               description=_('Model')),
            FileManager.Column(name='\
FileManagerPython::resolution_unit_column',
                               attribute='resolution_unit',
                               label=_('Resolution unit'),
                               description=_('The unit for measuring')),
            FileManager.Column(name='FileManagerPython::xresolution_column',
                               attribute='xresolution',
                               label=_('X resolution'),
                               description=_('The resolution in the x axis')),
            FileManager.Column(name='FileManagerPython::yresolution_column',
                               attribute='yresolution',
                               label=_('Y resolution'),
                               description=_('The resolution in the y axis')),
            FileManager.Column(name='\
FileManagerPython::datetime_original_column',
                               attribute='datetime_original',
                               label=_('Capture date'),
                               description=_('Photo capture date')),
            FileManager.Column(name='\
FileManagerPython::shutter_speed_value_column',
                               attribute='shutter_speed_value',
                               label=_('Shutter speed'),
                               description=_('Shutter speed')),
            FileManager.Column(name='\
FileManagerPython::aperture_value_column',
                               attribute='aperture_value',
                               label=_('Aperture'),
                               description=_('The lens aperture')),
            FileManager.Column(name='\
FileManagerPython::brightness_value_column',
                               attribute='brightness_value',
                               label=_('Brightness'),
                               description=_('Brightness')),
            FileManager.Column(name='\
FileManagerPython::exposure_bias_value_column',
                               attribute='exposure_bias_value',
                               label=_('Exposure'),
                               description=_('The exposure bias')),
            FileManager.Column(name='\
FileManagerPython::max_aperture_value_column',
                               attribute='max_aperture_value',
                               label=_('Max aperture'),
                               description=_(
                                    'The smallest F number of the lens')),
            FileManager.Column(name='\
FileManagerPython::metering_mode_column',
                               attribute='metering_mode',
                               label=_('Metering mode'),
                               description=_('The metering mode')),
            FileManager.Column(name='\
FileManagerPython::light_source_column',
                               attribute='light_source',
                               label=_('Light source'),
                               description=_('The kind of light source')),
            FileManager.Column(name='\
FileManagerPython::flash_column',
                               attribute='flash',
                               label=_('Flash'),
                               description=_('Indicates the status of flash \
when the image was shot')),
            FileManager.Column(name='\
FileManagerPython::exposure_mode_column',
                               attribute='exposure_mode',
                               label=_('Exposure mode'),
                               description=_('The exposure mode set when the \
image was shot')),
            FileManager.Column(name='\
FileManagerPython::gain_control_column',
                               attribute='gain_control',
                               label=_('Gain control'),
                               description=_('The degree of overall image \
gain adjustment')),
            FileManager.Column(name='\
FileManagerPython::width_column',
                               attribute='width',
                               label=_('Width'),
                               description=_(
                                    'Image/video/pdf width (pixel/mm)')),
            FileManager.Column(name='\
FileManagerPython::height_column',
                               attribute='height',
                               label=_('Height'),
                               description=_(
                                    'Image/video/pdf height (pixel/mm)')),
            FileManager.Column(name='\
FileManagerPython::pages_column',
                               attribute='pages',
                               label=_('Pages'),
                               description=_('Number of pages')),
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
        file.add_string_attribute('datetime_original', '')
        file.add_string_attribute('exposure_time', '')
        file.add_string_attribute('fnumber', '')
        file.add_string_attribute('focal_length', '')
        file.add_string_attribute('gps_altitude', '')
        file.add_string_attribute('gps_latitude', '')
        file.add_string_attribute('gps_longitude', '')
        file.add_string_attribute('iso_speed', '')
        file.add_string_attribute('get_orientation', '')
        file.add_string_attribute('model', '')
        file.add_string_attribute('resolution_unit', '')
        file.add_string_attribute('xresolution', '')
        file.add_string_attribute('yresolution', '')
        file.add_string_attribute('shutter_speed_value', '')
        file.add_string_attribute('aperture_value', '')
        file.add_string_attribute('brightness_value', '')
        file.add_string_attribute('exposure_bias_value', '')
        file.add_string_attribute('max_aperture_value', '')
        file.add_string_attribute('metering_mode', '')
        file.add_string_attribute('light_source', '')
        file.add_string_attribute('flash', '')
        file.add_string_attribute('exposure_mode', '')
        file.add_string_attribute('gain_control', '')
        file.add_string_attribute('width', '')
        file.add_string_attribute('height', '')
        file.add_string_attribute('pages', '')

        if file.get_uri_scheme() != 'file':
            return

        # strip file:// to get absolute path
        filename = urllib.parse.unquote_plus(file.get_uri()[7:])

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
        if file.get_mime_type().split('/')[0] in ('image'):
            # EXIF handling routines
            try:
                metadata = GExiv2.Metadata(filename)
                try:
                    file.add_string_attribute(
                        'datetime_original',
                        metadata.get_tag_string('Exif.Image.DateTime'))
                except Exception:
                    file.add_string_attribute('datetime_original', '')
                try:
                    file.add_string_attribute(
                        'artist',
                        metadata.get_tag_string('Exif.Image.Artist'))
                except Exception:
                    file.add_string_attribute('artist', '')
                try:
                    file.add_string_attribute(
                        'title',
                        metadata.get_tag_string('Exif.Image.ImageDescription'))
                except Exception:
                    file.add_string_attribute('title', '')
                try:
                    file.add_string_attribute(
                        'exposure_time',
                        metadata.get_exposure_time())
                except Exception:
                    file.add_string_attribute('exposure_time', '')
                try:
                    file.add_string_attribute(
                        'fnumber',
                        metadata.get_fnumber())
                except Exception:
                    file.add_string_attribute('fnumber', '')
                try:
                    file.add_string_attribute(
                        'focal_length',
                        metadata.get_focal_length())
                except Exception:
                    file.add_string_attribute('focal_length', '')
                try:
                    file.add_string_attribute(
                        'gps_altitude',
                        metadata.get_gps_altitude())
                except Exception:
                    file.add_string_attribute('gps_altitude', '')
                try:
                    file.add_string_attribute(
                        'gps_latitude',
                        metadata.get_gps_latitude())
                except Exception:
                    file.add_string_attribute('gps_latitude', '')
                try:
                    file.add_string_attribute(
                        'gps_longitude',
                        metadata.get_gps_longitude())
                except Exception:
                    file.add_string_attribute('gps_longitude', '')
                try:
                    file.add_string_attribute(
                        'iso_speed',
                        metadata.get_iso_speed())
                except Exception:
                    file.add_string_attribute('iso_speed', '')
                file.add_string_attribute('orientation',
                                          get_orientation(metadata))
                try:
                    file.add_string_attribute(
                        'model',
                        metadata.get_tag_string('Exif.Image.Model'))
                except Exception:
                    file.add_string_attribute('model', '')
                file.add_string_attribute('resolution_unit',
                                          get_resolution_unit(metadata))
                try:
                    file.add_string_attribute(
                        'xresolution',
                        metadata.get_tag_string('Exif.Image.XResolution'))
                except Exception:
                    file.add_string_attribute('xresolution', '')
                try:
                    file.add_string_attribute(
                        'yresolution',
                        metadata.get_tag_string('Exif.Image.YResolution'))
                except Exception:
                    file.add_string_attribute('yresolution', '')
                try:
                    file.add_string_attribute(
                        'shutter_speed_value',
                        metadata.get_tag_string(
                            'Exif.Photo.ShutterSpeedValue'))
                except Exception:
                    file.add_string_attribute('shutter_speed_value', '')
                try:
                    file.add_string_attribute(
                        'aperture_value',
                        metadata.get_tag_string(
                            'Exif.Photo.ApertureValue'))
                except Exception:
                    file.add_string_attribute('aperture_value', '')
                try:
                    file.add_string_attribute(
                        'brightness_value',
                        metadata.get_tag_string(
                            'Exif.Photo.BrightnessValue'))
                except Exception:
                    file.add_string_attribute('brightness_value', '')
                try:
                    file.add_string_attribute(
                        'brightness_value',
                        metadata.get_tag_string(
                            'Exif.Photo.BrightnessValue'))
                except Exception:
                    file.add_string_attribute('brightness_value', '')
                try:
                    file.add_string_attribute(
                        'exposure_bias_value',
                        metadata.get_tag_string(
                            'Exif.Photo.ExposureBiasValue'))
                except Exception:
                    file.add_string_attribute('exposure_bias_value', '')
                try:
                    file.add_string_attribute(
                        'max_aperture_value',
                        metadata.get_tag_string(
                            'Exif.Photo.MaxApertureValue'))
                except Exception:
                    file.add_string_attribute('max_aperture_value', '')
                file.add_string_attribute(
                    'metering_mode',
                    get_metering_mode(metadata))
                file.add_string_attribute(
                    'light_source',
                    get_light_source(metadata))
                file.add_string_attribute(
                    'flash',
                    get_flash(metadata))
                file.add_string_attribute(
                    'exposure_mode',
                    get_exposure_mode(metadata))
                file.add_string_attribute(
                    'gain_control',
                    get_gain_control(metadata))
            except Exception:
                file.add_string_attribute('datetime_original', '')
                file.add_string_attribute('artist', '')
                file.add_string_attribute('title', '')
                file.add_string_attribute('exposure_time', '')
                file.add_string_attribute('fnumber', '')
                file.add_string_attribute('focal_length', '')
                file.add_string_attribute('gps_altitude', '')
                file.add_string_attribute('gps_latitude', '')
                file.add_string_attribute('gps_longitude', '')
                file.add_string_attribute('iso_speed', '')
                file.add_string_attribute('get_orientation', '')
                file.add_string_attribute('model', '')
                file.add_string_attribute('resolution_unit', '')
                file.add_string_attribute('xresolution', '')
                file.add_string_attribute('yresolution', '')
                file.add_string_attribute('shutter_speed_value', '')
                file.add_string_attribute('aperture_value', '')
                file.add_string_attribute('brightness_value', '')
                file.add_string_attribute('exposure_bias_value', '')
                file.add_string_attribute('max_aperture_value', '')
                file.add_string_attribute('metering_mode', '')
                file.add_string_attribute('light_source', '')
                file.add_string_attribute('flash', '')
                file.add_string_attribute('exposure_mode', '')
                file.add_string_attribute('gain_control', '')
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
                info = FFProbe(filename)
                try:
                    file.add_string_attribute('codec_name',
                                              str(info.get_codec_name()))
                except Exception:
                    file.add_string_attribute('codec_name', _('Error'))
                try:
                    segundos = info.get_duration()
                    duration = '%02i:%02i:%02i' % ((int(segundos / 3600)),
                                                   (int(segundos / 60 % 60)),
                                                   (int(segundos % 60)))
                    file.add_string_attribute('length', duration)
                except Exception:
                    file.add_string_attribute('length', _('Error'))
                try:
                    file.add_string_attribute('width',
                                              str(info.get_width()))
                except Exception:
                    file.add_string_attribute('height', _('Error'))
                try:
                    file.add_string_attribute('height',
                                              str(info.get_height()))
                except Exception:
                    file.add_string_attribute('width', _('Error'))
                try:
                    file.add_string_attribute(
                        'bitrate', str(round(info.get_bitrate() / 1000)))
                except Exception:
                    file.add_string_attribute('bitrate', _('Error'))
                try:
                    file.add_string_attribute('frames',
                                              str(info.get_frames()))
                except Exception:
                    file.add_string_attribute('frames', _('Error'))
            except Exception:
                file.add_string_attribute('codec_name', _('Error'))
                file.add_string_attribute('length', _('Error'))
                file.add_string_attribute('width', _('Error'))
                file.add_string_attribute('height', _('Error'))
                file.add_string_attribute('bitrate', _('Error'))
                file.add_string_attribute('frames', _('Error'))
        # pdf handling
        if file.is_mime_type('application/pdf'):
            try:
                f = open(filename, 'rb')
                pdf = PdfFileReader(f)
                info = pdf.getDocumentInfo()
                try:
                    file.add_string_attribute(
                        'title',
                        info.title if info.title is not None else '')
                except Exception:
                    file.add_string_attribute('title', _('Error'))
                try:
                    file.add_string_attribute(
                        'artist',
                        info.author if info.author is not None else '')
                except Exception:
                    file.add_string_attribute('artist', _('Error'))
                try:
                    file.add_string_attribute(
                        'pages',
                        str(pdf.getNumPages()))
                except Exception:
                    file.add_string_attribute('pages', _('Error'))
                if pdf.getNumPages() > 0:
                    try:
                        width = abs(pdf.getPage(0).mediaBox.upperRight[0] -
                                    pdf.getPage(0).mediaBox.lowerLeft[0])
                        file.add_string_attribute(
                            'width',
                            str(int(float(width) * math.sqrt(2.0) / 4.0)))
                    except Exception:
                        file.add_string_attribute('width', '')
                    try:
                        height = abs(pdf.getPage(0).mediaBox.upperRight[1] -
                                     pdf.getPage(0).mediaBox.lowerLeft[1])
                        file.add_string_attribute(
                            'height',
                            str(int(float(height) * math.sqrt(2.0) / 4.0)))
                    except Exception:
                        file.add_string_attribute('height', '')
                else:
                    file.add_string_attribute('width', '')
                    file.add_string_attribute('height', '')
                f.close()
            except Exception:
                file.add_string_attribute('title', _('Error'))
                file.add_string_attribute('artist', _('Error'))
                file.add_string_attribute('pages', _('Error'))
                file.add_string_attribute('width', _('Error'))
                file.add_string_attribute('height', _('Error'))
        self.get_columns()
