# http://bazaar.launchpad.net/~testtools-committers/testtools/trunk/view/head:/testtools/compat.py

# Copyright (c) 2008-2011 Jonathan M. Lange <jml@mumak.net> and the testtools
# authors.
#
# The testtools authors are:
#  * Canonical Ltd
#  * Twisted Matrix Labs
#  * Jonathan Lange
#  * Robert Collins
#  * Andrew Bennetts
#  * Benjamin Peterson
#  * Jamu Kakar
#  * James Westby
#  * Martin [gz]
#  * Michael Hudson-Doyle
#  * Aaron Bentley
#  * Christian Kampka
#  * Gavin Panella
#  * Martin Pool
#  * Vincent Ladeuil
#
# and are collectively referred to as "testtools developers".
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# Some code in testtools/run.py taken from Python's unittest module:
# Copyright (c) 1999-2003 Steve Purcell
# Copyright (c) 2003-2010 Python Software Foundation
#
# This module is free software, and you may redistribute it and/or modify
# it under the same terms as Python itself, so long as this copyright message
# and disclaimer are retained in their original form.
#
# IN NO EVENT SHALL THE AUTHOR BE LIABLE TO ANY PARTY FOR DIRECT, INDIRECT,
# SPECIAL, INCIDENTAL, OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE USE OF
# THIS CODE, EVEN IF THE AUTHOR HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.
#
# THE AUTHOR SPECIFICALLY DISCLAIMS ANY WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE.  THE CODE PROVIDED HEREUNDER IS ON AN "AS IS" BASIS,
# AND THERE IS NO OBLIGATION WHATSOEVER TO PROVIDE MAINTENANCE,
# SUPPORT, UPDATES, ENHANCEMENTS, OR MODIFICATIONS.

import codecs
import linecache
import locale
import os
import re
import sys
import traceback

# The default source encoding is actually "iso-8859-1" until Python 2.5 but
# using non-ascii causes a deprecation warning in 2.4 and it's cleaner to
# treat all versions the same way
_default_source_encoding = "ascii"

# Pattern specified in <http://www.python.org/dev/peps/pep-0263/>
_cookie_search = re.compile("coding[:=]\s*([-\w.]+)").search


def _detect_encoding(lines):
    """Get the encoding of a Python source file from a list of lines as bytes

    This function does less than tokenize.detect_encoding added in Python 3 as
    it does not attempt to raise a SyntaxError when the interpreter would, it
    just wants the encoding of a source file Python has already compiled and
    determined is valid.
    """
    if not lines:
        return _default_source_encoding
    if lines[0].startswith("\xef\xbb\xbf"):
        # Source starting with UTF-8 BOM is either UTF-8 or a SyntaxError
        return "utf-8"
    # Only the first two lines of the source file are examined
    magic = _cookie_search("".join(lines[:2]))
    if magic is None:
        return _default_source_encoding
    encoding = magic.group(1)
    try:
        codecs.lookup(encoding)
    except LookupError:
        # Some codecs raise something other than LookupError if they don't
        # support the given error handler, but not the text ones that could
        # actually be used for Python source code
        return _default_source_encoding
    return encoding


class _EncodingTuple(tuple):
    """A tuple type that can have an encoding attribute smuggled on"""


def _get_source_encoding(filename):
    """Detect, cache and return the encoding of Python source at filename"""
    try:
        return linecache.cache[filename].encoding
    except (AttributeError, KeyError):
        encoding = _detect_encoding(linecache.getlines(filename))
        if filename in linecache.cache:
            newtuple = _EncodingTuple(linecache.cache[filename])
            newtuple.encoding = encoding
            linecache.cache[filename] = newtuple
        return encoding


def _get_exception_encoding():
    """Return the encoding we expect messages from the OS to be encoded in"""
    if os.name == "nt":
        # GZ 2010-05-24: Really want the codepage number instead, the error
        #                handling of standard codecs is more deterministic
        return "mbcs"
    # GZ 2010-05-23: We need this call to be after initialisation, but there's
    #                no benefit in asking more than once as it's a global
    #                setting that can change after the message is formatted.
    return locale.getlocale(locale.LC_MESSAGES)[1] or "ascii"


def _exception_to_text(evalue):
    """Try hard to get a sensible text value out of an exception instance"""
    try:
        return unicode(evalue)
    except KeyboardInterrupt:
        raise
    except:
        # Apparently this is what traceback._some_str does. Sigh - RBC 20100623
        pass
    try:
        return str(evalue).decode(_get_exception_encoding(), "replace")
    except KeyboardInterrupt:
        raise
    except:
        # Apparently this is what traceback._some_str does. Sigh - RBC 20100623
        pass
    # Okay, out of ideas, let higher level handle it
    return None

# GZ 2010-05-23: This function is huge and horrible and I welcome suggestions
#                on the best way to break it up
_TB_HEADER = u'Traceback (most recent call last):\n'


def _format_exc_info(eclass, evalue, tb, limit=None):
    """Format a stack trace and the exception information as unicode

    Compatibility function for Python 2 which ensures each component of a
    traceback is correctly decoded according to its origins.

    Based on traceback.format_exception and related functions.
    """
    fs_enc = sys.getfilesystemencoding()
    if tb:
        list = [_TB_HEADER]
        extracted_list = []
        for filename, lineno, name, line in traceback.extract_tb(tb, limit):
            extracted_list.append((
                filename.decode(fs_enc, "replace"),
                lineno,
                name.decode("ascii", "replace"),
                line and line.decode(
                    _get_source_encoding(filename), "replace")))
        list.extend(traceback.format_list(extracted_list))
    else:
        list = []
    if evalue is None:
        # Is a (deprecated) string exception
        list.append((eclass + "\n").decode("ascii", "replace"))
        return list
    if isinstance(evalue, SyntaxError):
        # Avoid duplicating the special formatting for SyntaxError here,
        # instead create a new instance with unicode filename and line
        # Potentially gives duff spacing, but that's a pre-existing issue
        try:
            msg, (filename, lineno, offset, line) = evalue
        except (TypeError, ValueError):
            pass  # Strange exception instance, fall through to generic code
        else:
            # Errors during parsing give the line from buffer encoded as
            # latin-1 or utf-8 or the encoding of the file depending on the
            # coding and whether the patch for issue #1031213 is applied, so
            # give up on trying to decode it and just read the file again
            if line:
                bytestr = linecache.getline(filename, lineno)
                if bytestr:
                    if lineno == 1 and bytestr.startswith("\xef\xbb\xbf"):
                        bytestr = bytestr[3:]
                    line = bytestr.decode(
                        _get_source_encoding(filename), "replace")
                    del linecache.cache[filename]
                else:
                    line = line.decode("ascii", "replace")
            if filename:
                filename = filename.decode(fs_enc, "replace")
            evalue = eclass(msg, (filename, lineno, offset, line))
            list.extend(traceback.format_exception_only(eclass, evalue))
            return list
    sclass = eclass.__name__
    svalue = _exception_to_text(evalue)
    if svalue:
        list.append("%s: %s\n" % (sclass, svalue))
    elif svalue is None:
        # GZ 2010-05-24: Not a great fallback message, but keep for the moment
        list.append("%s: <unprintable %s object>\n" % (sclass, sclass))
    else:
        list.append("%s\n" % sclass)
    return list
