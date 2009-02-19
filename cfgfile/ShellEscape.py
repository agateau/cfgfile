# -*- coding: utf-8 -*-
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
