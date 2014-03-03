#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_py65c
----------------------------------

Tests for `py65c` module.
"""

import unittest, os

from py65c.compiler import compile
from py65emu.cpu import CPU
from py65emu.mmu import MMU



class TestPy65c(unittest.TestCase):

    def _loadFile(self, filename):
        return open(os.path.join(
            os.path.dirname(os.path.realpath(__file__)), 
            "files", filename
        ))

    def _generic_cpu(self, rom):
        mmu = MMU([
            (0x0000, 0x400), #RAM
            (0x1000, 0x1000, True, rom) #ROM
        ])
        c = CPU(mmu, 0x1000)
        return c

    def _compile_and_run(self, filename):
        bin = compile(self._loadFile(filename))
        print bin
        c = self._generic_cpu(bin)
        while True:
            try:
                print hex(c.r.pc), ":", c.mmu.read(c.r.pc), c.r
                c.step()
            except:
                break

        return c

    def setUp(self):
        pass

    def test_gt(self):
        c = self._compile_and_run("gt.py")

        self.assertEqual(c.mmu.read(0x200), True)
        self.assertEqual(c.mmu.read(0x201), True)
        self.assertEqual(c.mmu.read(0x202), False)
        self.assertEqual(c.mmu.read(0x203), False)
        self.assertEqual(c.mmu.read(0x204), False)

    def test_gte(self):
        c = self._compile_and_run("gte.py")

        self.assertEqual(c.mmu.read(0x200), True)
        self.assertEqual(c.mmu.read(0x201), True)
        self.assertEqual(c.mmu.read(0x202), True)
        self.assertEqual(c.mmu.read(0x203), False)
        self.assertEqual(c.mmu.read(0x204), False)


    def test_list(self):
        c = self._compile_and_run("list.py")

        self.assertEqual(c.mmu.read(0x200), 1)
        self.assertEqual(c.mmu.read(0x201), 2)
        self.assertEqual(c.mmu.read(0x202), 3)
        self.assertEqual(c.mmu.read(0x203), 4)
        self.assertEqual(c.mmu.read(0x204), 5)

        #a, i
        self.assertEqual(c.mmu.read(0x206), 15)
        self.assertEqual(c.mmu.read(0x207), 0)

        self.assertEqual(c.mmu.read(0x205), 15)


    def test_while(self):
        c = self._compile_and_run("while.py")

        self.assertEqual(c.mmu.read(0x200), 2)
        self.assertEqual(c.mmu.read(0x201), 64)

    def test_if(self):   
        c = self._compile_and_run("if.py")

        self.assertEqual(c.mmu.read(0x200), 64)

    def test_addsub(self):   
        c = self._compile_and_run("addsub.py")

        self.assertEqual(c.mmu.read(0x200), 2)
        self.assertEqual(c.mmu.read(0x201), 1)
        self.assertEqual(c.mmu.read(0x202), 0xff)
        self.assertEqual(c.mmu.read(0x203), 0)

    def test_addsub(self):   
        c = self._compile_and_run("bool.py")

        self.assertEqual(c.mmu.read(0x200), True)
        self.assertEqual(c.mmu.read(0x201), False)
        self.assertEqual(c.mmu.read(0x202), False)
        self.assertEqual(c.mmu.read(0x203), True)
        self.assertEqual(c.mmu.read(0x204), False)
        self.assertEqual(c.mmu.read(0x205), 5)
        self.assertEqual(c.mmu.read(0x206), 4)
        self.assertEqual(c.mmu.read(0x207), 0)
        self.assertEqual(c.mmu.read(0x208), 5)
        self.assertEqual(c.mmu.read(0x209), 4)
        self.assertEqual(c.mmu.read(0x20a), 4)
        self.assertEqual(c.mmu.read(0x20b), 4)


    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()