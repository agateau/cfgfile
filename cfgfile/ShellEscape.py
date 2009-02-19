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
# Backslash must be first
NEED_ESCAPE_CHARS=['\\', '"', "'", ' ']


class ShellEscape:
    def escape(self, txt):
        for escapeChar in NEED_ESCAPE_CHARS:
            txt=txt.replace(escapeChar, "\\" + escapeChar)
        return txt


    def unescape(self, txt):
        # Remove leading spaces
        txt=txt.lstrip()
        src=list(txt)

        # Remove ending spaces, if they are not escaped
        while len(src)>=2 and src[-1].isspace() and src[-2]!="\\":
            del src[-1]
        
        quote=""
        dst=[]
        while len(src)>0:
            ch=src[0]
            del src[0]
            if ch=="\\":
                ch=src[0]
                del src[0]
                dst.append(ch)
                
            elif quote!="" and ch==quote:
                pass

            elif ch in ("'", '"'):
                quote=ch

            else:
                dst.append(ch)
        return "".join(dst)
