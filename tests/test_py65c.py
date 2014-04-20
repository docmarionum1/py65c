#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_py65c
----------------------------------

Tests for `py65c` module.
"""

import unittest, os

from py65c.compiler import compile, Compiler
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

    def test_malloc_free(self):
        c = Compiler(mmu=MMU([(0, 0x10), (0x20, 0x10)]))
        l1 = c._malloc(0x1)
        self.assertEqual(l1, 0)

        l2 = c._malloc(0x1)
        self.assertEqual(l2, 1)

        l3 = c._malloc(0x10)
        self.assertEqual(l3, 0x20)

        c._free(l1)

        l4 = c._malloc(0x1)
        self.assertEqual(l4, 0)

        with self.assertRaises(Exception):
            c._malloc(0x10)


    def _compile_and_run(self, filename):
        bin = compile(self._loadFile(filename))
        #print bin
        c = self._generic_cpu(bin)
        while True:
            try:
                #print hex(c.r.pc), ":", hex(c.mmu.read(c.r.pc)), c.r
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

    def test_lte(self):
        c = self._compile_and_run("lte.py")

        self.assertEqual(c.mmu.read(0x200), False)
        self.assertEqual(c.mmu.read(0x201), False)
        self.assertEqual(c.mmu.read(0x202), False)
        self.assertEqual(c.mmu.read(0x203), True)
        self.assertEqual(c.mmu.read(0x204), True)

        self.assertEqual(c.mmu.read(0x205), False)
        self.assertEqual(c.mmu.read(0x206), False)
        self.assertEqual(c.mmu.read(0x207), True)
        self.assertEqual(c.mmu.read(0x208), True)
        self.assertEqual(c.mmu.read(0x209), True)

        self.assertEqual(c.mmu.read(0x20a), True)
        self.assertEqual(c.mmu.read(0x20b), False)
        self.assertEqual(c.mmu.read(0x20c), True)
        self.assertEqual(c.mmu.read(0x20d), False)
        self.assertEqual(c.mmu.read(0x20e), True)


    def test_list(self):
        c = self._compile_and_run("list.py")
        print c.mmu.read(0x200)
        print c.mmu.read(0x201)
        print c.mmu.read(0x202)
        print c.mmu.read(0x203)
        print c.mmu.read(0x204)
        print c.mmu.read(0x205)
        print c.mmu.read(0x206)
        print c.mmu.read(0x207)
        print c.mmu.read(0x200)

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
        self.assertEqual(c.mmu.read(0x204), 1)

    def test_bool(self):   
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

    def test_mul(self):   
        c = self._compile_and_run("mul.py")

        self.assertEqual(c.mmu.read(0x200), 25)
        self.assertEqual(c.mmu.read(0x201), 24)
        self.assertEqual(c.mmu.read(0x202), 0)
        self.assertEqual(c.mmu.read(0x203), 0)
        self.assertEqual(c.mmu.read(0x204), 0x10)
        self.assertEqual(c.mmu.read(0x205), 100)
        self.assertEqual(c.mmu.read(0x206), 105)

    def test_fib(self):
        c = self._compile_and_run("fib.py")

        self.assertEqual(c.mmu.read(0x200), 1)
        self.assertEqual(c.mmu.read(0x201), 1)
        self.assertEqual(c.mmu.read(0x202), 2)
        self.assertEqual(c.mmu.read(0x203), 3)
        self.assertEqual(c.mmu.read(0x204), 5)
        self.assertEqual(c.mmu.read(0x205), 8)
        self.assertEqual(c.mmu.read(0x206), 13)
        self.assertEqual(c.mmu.read(0x207), 21)
        self.assertEqual(c.mmu.read(0x208), 34)
        self.assertEqual(c.mmu.read(0x209), 55)

    def test_func(self):
        c = self._compile_and_run("func.py")

        print c.mmu.read(0x1ff)
        print c.mmu.read(0x1fe)
        print c.mmu.read(0x1fd)
        print c.mmu.read(0x1fc)
        print c.mmu.read(0x1fb)
        print c.mmu.read(0x1fa)
        print c.mmu.read(0x1f9)

        self.assertEqual(c.mmu.read(0x200), 3)
        self.assertEqual(c.mmu.read(0x201), 5)
        self.assertEqual(c.mmu.read(0x202), 6)
        #self.assertEqual(c.mmu.read(0x203), 2)
        #elf.assertEqual(c.mmu.read(0x204), 3)

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()