#!/usr/bin/env python
# coding: utf-8
"""
Copyright 2009 Aurélien Gâteau

This file is part of Cfgfile.

Cfgfile is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Foobar is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Foobar.  If not, see <http://www.gnu.org/licenses/>.
"""
import getopt
import os
import shutil
import sys

from ShellEscape import ShellEscape
from NoEscape import NoEscape

COMMENTS=['#', ';']
SEPARATOR='='

BACKUP_SUFFIX=".pre-cfgfile"

MODFLAG="/tmp/modflag"

ESCAPE_CLASS_DICT={
    "none":  NoEscape,
    "shell": ShellEscape
    }

class CfgLine:
    def __init__(self, cfgFile):
        self._cfgFile=cfgFile
        self._key=None
        self._value=None


    def loadFromString(self, txt):
        # Do not use strip, this would skip the last space in a line like this:
        # "bla=a\ value\ with\ an\ ending\ space\ "
        txt=txt.lstrip()
        
        self._key, self._value = txt.split(self._cfgFile._separator, 1)
        self._key = self._key.strip()

        self._value = self._cfgFile._escape.unescape(self._value)


    def __str__(self):
        return self._key + self._cfgFile._separator + self._cfgFile._escape.escape(self._value)


    def key(self):
        return self._key


    def value(self):
        return self._value


    def set(self, key, value):
        self._key=key
        self._value=value



class CfgFile:
    def __init__(self):
        self._lines=[]
        self._keyLineDict={}
        self._separator=SEPARATOR
        self._comments=COMMENTS
        self._modified=False
        self._escape=NoEscape()


    def setEscape(self, escape):
        self._escape=escape


    def escape(self):
        return self._escape


    def setSeparator(self, value):
        self._separator=value


    def separator(self):
        return self._separator


    def loadFromStream(self, fl):
        self._modified=False
        for txt in fl.readlines():
            if txt.endswith("\n"):
                txt=txt[:-1]
            if self._isKey(txt):
                line=CfgLine(self)
                line.loadFromString(txt)
                self._keyLineDict[line.key()]=line
            else:
                line=txt
            self._lines.append(line)


    def setKey(self, key, value):
        if key in self._keyLineDict:
            line=self._keyLineDict[key]
            if line.value()!=value:
                line.set(key, value)
                self._modified=True
        else:
            line=CfgLine(self)
            line.set(key, value)
            self._lines.append(line)
            self._keyLineDict[line.key()]=line
            self._modified=True


    def getKey(self, key, default=""):
        if key in self._keyLineDict:
            return self._keyLineDict[key].value()
        else:
            return default


    def keyList(self):
        return self._keyLineDict.keys()


    def delKey(self, key):
        if not key in self._keyLineDict:
            return
        line=self._keyLineDict[key]
        self._lines.remove(line)
        del self._keyLineDict[key]
        self._modified=True


    def saveToStream(self, fl):
        for line in self._lines:
            fl.write(str(line) + "\n")
        self._modified=False


    def modified(self):
        return self._modified


    def _isKey(self, txt):
        txt=txt.strip()
        if len(txt)==0:
            return False
        if txt[0] in self._comments:
            return False
        if not self._separator in txt:
            return False
        return True


    def load(self, fileName):
        if not os.path.exists(fileName):
            return
        fl=file(fileName)
        self.loadFromStream(fl)
    
    
    def save(self, fileName):
        if not self._modified:
            return

        if os.path.exists(fileName):
            os.rename(fileName, fileName + BACKUP_SUFFIX)
        else:
            baseDir=os.path.dirname(fileName)
            if not os.path.exists(baseDir):
                os.makedirs(baseDir, 0755)
        fl=file(fileName, "w")
        self.saveToStream(fl)
        if os.path.exists(fileName + BACKUP_SUFFIX):
            shutil.copymode(fileName + BACKUP_SUFFIX, fileName)

    # Dict-like methods

    def __setitem__(self, key, value):
        self.setKey(key, value)
    
    
    def __getitem__(self, key):
        return self.getKey(key)


    def __contains__(self, key):
        return key in self._keyLineDict

    


def usage(msg=""):
    if msg!="":
        print "ERROR:", msg
    print """
Usage: cfgfile [options] file [action] [action params]
  -h,--help
  --escape=%(escape)s
    How to escape config values. Default to none
  
  --separator
    key, value separator. Default to '%(sep)s'
        
  --modflag
    Create a file named %(modflag)s if a file has been modified

  --keepflag
    Only usefull with --modflag. Do not delete %(modflag)s before running. This
    is useful to chain modifications like this:
    
    cfgfile --modflag file1 set key value
    cfgfile --modflag --keepflag file2 set key value
    [ -e %(modflag)s ] && some_command

    some_command will be run if one of the files has been modified
  
actions:
  set key value [key value [key value...]]

  get key [default]

  del key

  keylist
""" % {
    "escape":  ",".join(ESCAPE_CLASS_DICT.keys()),
    "sep":     SEPARATOR,
    "modflag": MODFLAG
    }
    
    sys.exit(1)


def save(cfgFile, modFlag, fileName):
    modified=cfgFile.modified()
    cfgFile.save(fileName)
    
    if modified and modFlag:
        flag=file(MODFLAG, "w")
        flag.close()


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help", "escape=", "separator=", "modflag", "keepflag"])
    except getopt.GetoptError, exc:
        usage(exc)
    
    separator=SEPARATOR
    modFlag=False
    keepFlag=False
    escapeName="none"
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            
        elif opt=="--separator":
            separator=arg
            
        elif opt=="--modflag":
            modFlag=True
            
        elif opt=="--keepflag":
            keepFlag=True

        elif opt=="--escape":
            if not arg in ESCAPE_CLASS_DICT:
                usage("'%s' is not a value for --escape." % arg)
            escapeName=arg

    if len(args)<2:
        usage("Not enough arguments")
        
    fileName=args[0]
    if modFlag and not keepFlag and os.path.exists(MODFLAG):
        os.unlink(MODFLAG)

    cfgFile=CfgFile()
    cfgFile.setSeparator(separator)
    cfgFile.setEscape( ESCAPE_CLASS_DICT[escapeName]() )
    cfgFile.load(fileName)

    action=args[1]

    del args[:2]
    
    if action=="set":
        while len(args)>0:
            key=args[0]
            value=args[1]
            del args[:2]
            cfgFile.setKey(key, value)
        save(cfgFile, modFlag, fileName)
        
    elif action=="get":
        key=args[0]
        if len(args)==2:
            default=args[1]
        else:
            default=""
        print cfgFile.getKey(key, default)

    elif action=="del":
        key=args[0]
        cfgFile.delKey(key)
        save(cfgFile, modFlag, fileName)
    
    elif action=="keylist":
        print "\n".join(cfgFile.keyList())

    else:
        usage("Unknown action '%s'" % action)
        

if __name__=="__main__":
    main()
# vi: ts=4 sw=4 et
