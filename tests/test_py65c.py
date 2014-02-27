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

    def setUp(self):
        pass

    def test_gt(self):
        bin = compile(self._loadFile("gt.py"))
        print bin
        c = self._generic_cpu(bin)
        while True:
            try:
                c.step()
            except:
                break

        self.assertEqual(c.mmu.read(0x200), True)
        self.assertEqual(c.mmu.read(0x201), True)
        self.assertEqual(c.mmu.read(0x202), False)
        self.assertEqual(c.mmu.read(0x203), False)
        self.assertEqual(c.mmu.read(0x204), False)

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()