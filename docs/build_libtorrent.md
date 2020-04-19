Based on:
https://github.com/arvidn/libtorrent/blob/master/docs/python_binding.rst

Download and unzip boost to C:\\:
https://dl.bintray.com/boostorg/release/1.70.0/source/boost_1_70_0.tar.bz2

Fetch libtorrent and set the correct tag:
```
cd c:\
git clone https://github.com/arvidn/libtorrent
cd libtorrent
git checkout libtorrent-1_2_5
```

Note: python 3.7 requires boost 1.67+

```
set BVERSION=1_70_0

set BOOST_BUILD_PATH=c:/boost_%BVERSION%/tools/build/
set BOOST_ROOT=c:/boost_%BVERSION%/

cd %BOOST_ROOT%
bootstrap.bat
set PATH=%PATH%;c:/boost_%BVERSION%/tools/build/src/engine/bin.ntx86/

copy /Y "%BOOST_BUILD_PATH%\example\user-config.jam" "%BOOST_BUILD_PATH%\user-config.jam"
echo using msvc : 14.1 : : "/std:c++14" ; >> "%BOOST_BUILD_PATH%/user-config.jam"
echo using python : 3.7 : "C:/Python37" : "C:/Python37/include" : "C:/Python37/libs" ; >> "%BOOST_BUILD_PATH%/user-config.jam"

cd c:\libtorrent\bindings\python
c:\Python37\python.exe setup.py build --bjam
```
