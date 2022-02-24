# nautilus-columns

If your music files aren't named properly or simply want to see the MP3 and FLAC metadata information (ID3 tags) in Nautilus List View, you can't by default.

But I found a python script (which also comes as a .deb file) on the Ubuntu Forums called "Nautilus Columns" which adds new columns to Nautilus, so you can view such metadata information. Besides MP3 and FLAC, the script was also updated to support JPEG EXIF shooting data.

For more information, please visit:

http://www.webupd8.org/2010/01/mp3-and-flac-metadata-information-id3.html
or
https://github.com/atareao/nautilus-columns

## Requirements

Required dependencies:

```
if [ -f "/etc/debian_version" ]; then
 sudo apt install python3 python3-gi python3-pil gir1.2-nautilus-3.0 gir1.2-gexiv2-0.10 python3-nautilus python3-mutagen python3-pypdf2 python3-plumbum mediainfo
fi
if [ "$(grep -Ei 'fedora|redhat' /etc/*release)" ]; then
 sudo dnf install python3 python3-pillow python3-nautilus python3-mutagen python3-PyPDF2 python3-plumbum mediainfo
fi
```

## Download

Download the package:

```
git clone https://github.com/atareao/nautilus-columns.git
```

## Install

Nautilus:

```
sudo add-apt-repository ppa:atareao/nautilus-extensions
sudo apt update
sudo apt install nautilus-columns
```

Nemo

```
sudo add-apt-repository ppa:atareao/nemo-extensions
sudo apt update
sudo apt install nemo-columns
```

Caja

```
sudo add-apt-repository ppa:atareao/caja-extensions
sudo apt update
sudo apt install caja-columns
```
