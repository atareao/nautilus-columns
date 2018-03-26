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
    python
    python-gi
    python-pil
    gir1.2-nautilus-3.0
    python-nautilus
    python-mutagen
    python-pyexiv2
    python-kaa-metadata
    libnautilus-extension1a
    python-pypdf2
```

## Download

Download the package:

```
git clone https://github.com/atareao/nautilus-columns.git
```

## Install

Nautilus:

```
sudo add-apt-repository ppa:atarea/nautilus-extensions
sudo apt update
sudo apt install nautilus-columns
```

Nemo

```
sudo add-apt-repository ppa:atarea/nemo-extensions
sudo apt update
sudo apt install nemo-columns
```

Caja

```
sudo add-apt-repository ppa:atarea/caja-extensions
sudo apt update
sudo apt install caja-columns
```
