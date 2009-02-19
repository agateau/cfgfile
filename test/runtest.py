# -*- coding: utf-8 -*-
import os
import shutil
import sys
import unittest
from StringIO import StringIO

sys.path.insert(0, "..")
import cfgfile
from cfgfile.CfgFile import BACKUP_SUFFIX


# First item is unescaped, second item is escaped
_escapeData=[
    ("bla", "bla"),
    ("tok1 tok2", "tok1\\ tok2"),
    ("tok1\\tok2","tok1\\\\tok2"),
    ("tok1'tok2", "tok1\\'tok2"),
    ('tok1"tok2', 'tok1\\"tok2'),
    (" ", "\ "),
    ]

class ShellEscapeTestCase(unittest.TestCase):
    def setUp(self):
        self.escape=cfgfile.ShellEscape()

    def testEscapeData(self):
        for unescaped, escaped in _escapeData:
            self.assertEqual( \
                self.escape.escape(unescaped), \
                escaped)

    def testUnescapeData(self):
        for unescaped, escaped in _escapeData:
            self.assertEqual( \
                self.escape.unescape(escaped), \
                unescaped)

    def testUnescapeSpecial(self):
        specialData=[
            ("", "   "),
            ("bla", "'bla'"),
            ("bla", '"bla"'),
            ("bl'a","'bl\\\'a'")
            ]
        
        for unescaped, escaped in specialData:
            self.assertEqual( \
                self.escape.unescape(escaped), \
                unescaped)


TEST_DATA="""
# a comment

key=value
another_key=another_value

A line which will be skipped
"""
TEST_FILENAME="test.conf"

class CfgFileTestCase(unittest.TestCase):
    def setUp(self):
        fl=file(TEST_FILENAME, "w")
        fl.write(TEST_DATA)


    def tearDown(self):
        files=(TEST_FILENAME, TEST_FILENAME + BACKUP_SUFFIX)
        for file in files:
            if os.path.exists(file):
                os.unlink(file)


    def testGet(self):
        cfg=cfgfile.CfgFile()
        cfg.load(TEST_FILENAME)
        value=cfg.getKey("key")
        self.assertEqual(value, "value")
        
        value=cfg["key"]
        self.assertEqual(value, "value")

        value=cfg.getKey("does_not_exist")
        self.assertEqual(value, "")
        
        value=cfg.getKey("does_not_exist", "custom_default")
        self.assertEqual(value, "custom_default")


    def testEmptyValue(self):
        fl=StringIO("key1=\nkey2=    ")
        cfg=cfgfile.CfgFile()
        cfg.loadFromStream(fl)
        value=cfg.getKey("key1")
        self.assertEqual(value, "")
        value=cfg.getKey("key2")
        self.assertEqual(value, "")
    

    def testOtherSeparator(self):
        for separator in ":", " ":
            cfgString="key" + separator + "value"
            fl=StringIO(cfgString)
            
            cfg=cfgfile.CfgFile()
            cfg.setSeparator(separator)
            cfg.loadFromStream(fl)
            value=cfg.getKey("key")
            self.assertEqual(value, "value")


    def testSet(self):
        cfg=cfgfile.CfgFile()
        cfg.load(TEST_FILENAME)
        self.assertEqual(cfg.modified(), False)
        
        cfg.setKey("key", "value2")
        self.assertEqual(cfg.modified(), True)

        cfg.save(TEST_FILENAME)
        self.assertEqual(cfg.modified(), False)

        expected=TEST_DATA.replace("key=value", "key=value2")
        self.assertEqual(file(TEST_FILENAME).read(), expected)
        
        cfg["key"] =  "value3"
        cfg.save(TEST_FILENAME)
        
        expected=TEST_DATA.replace("key=value", "key=value3")
        self.assertEqual(file(TEST_FILENAME).read(), expected)


    def testSetNoModification(self):
        cfg=cfgfile.CfgFile()
        cfg.load(TEST_FILENAME)
        self.assertEqual(cfg.modified(), False)
        
        cfg.setKey("key", cfg.getKey("key"))
        self.assertEqual(cfg.modified(), False)


    def testSetEmptyFile(self):
        inFL=StringIO("# a comment")
        cfg=cfgfile.CfgFile()
        cfg.loadFromStream(inFL)
        cfg.setKey("key", "value")
        self.assertEqual(cfg.modified(), True)
        outFL=StringIO()
        cfg.saveToStream(outFL)

        expected="# a comment\nkey=value\n"
        self.assertEqual(outFL.getvalue(), expected)


    def testSetToNewFile(self):
        fileName="subdir/newfile.conf"
        try:
            cfg=cfgfile.CfgFile()
            cfg.load(fileName)
            cfg.setKey("key", "value")
            cfg.save(fileName)
            expected="key=value\n"
            self.assertEqual(file(fileName).read(), expected)
        finally:
            if os.path.exists("subdir"):
                shutil.rmtree("subdir")


    def testKeyList(self):
        cfg=cfgfile.CfgFile()
        cfg.load(TEST_FILENAME)
        lst=cfg.keyList()
        
        lst.sort()
        expected=["another_key", "key"]
        expected.sort()
        self.assertEqual(lst, expected)

        self.assert_("key" in cfg)
        self.assert_(not "bla" in cfg)
        

    def testDel(self):
        cfg=cfgfile.CfgFile()
        cfg.load(TEST_FILENAME)
        cfg.delKey("key")
        self.assertEqual(cfg.modified(), True)
        lstAfter=cfg.keyList()
        self.assertEqual(lstAfter, ["another_key"])


class NoEscapeCfgFileTestCase(unittest.TestCase):
    def testSpaceInValue(self):
        cfgString="key= a  value  "
        fl=StringIO(cfgString)
        
        cfg=cfgfile.CfgFile()
        cfg.setSeparator("=")
        cfg.loadFromStream(fl)
        value=cfg.getKey("key")
        self.assertEqual(value, "a  value")



class ShellEscapeCfgFileTestCase(unittest.TestCase):
    def testMultiSpaceSeparator(self):
        cfgString="   key   value\  "
        fl=StringIO(cfgString)
        
        cfg=cfgfile.CfgFile()
        cfg.setEscape(cfgfile.ShellEscape())
        cfg.setSeparator(" ")
        cfg.loadFromStream(fl)
        value=cfg.getKey("key")
        self.assertEqual(value, "value ")


    def testWriteSpaceValue(self):
        cfg=cfgfile.CfgFile()
        cfg.setEscape(cfgfile.ShellEscape())
        cfg.setKey("key", "a value")
        
        outFL=StringIO()
        cfg.saveToStream(outFL)
        
        expected="key=a\\ value\n"
        self.assertEqual(outFL.getvalue(), expected)


def main():
    runner=unittest.TextTestRunner()
    testSuite=unittest.TestSuite()
    for testCase in ShellEscapeTestCase, CfgFileTestCase, ShellEscapeCfgFileTestCase, NoEscapeCfgFileTestCase:
        suite=unittest.makeSuite(testCase, "test")
        testSuite.addTest(suite)
    result=runner.run(testSuite)
    if not result.wasSuccessful():
        sys.exit(-1)

if __name__ == "__main__":
    main()
