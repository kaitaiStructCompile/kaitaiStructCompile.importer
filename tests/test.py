#!/usr/bin/env python3
import sys
from pathlib import Path
import unittest
from collections import OrderedDict

testsDir = Path(__file__).parent.absolute()
parentDir = testsDir.parent.absolute()

from kaitaiStructCompile import compile

inputDir = testsDir / "ksys"


class Test(unittest.TestCase):
	def testImport(self):
		import kaitaiStructCompile.importer

		kaitaiStructCompile.importer._importer.searchDirs.append(inputDir)
		kaitaiStructCompile.importer._importer.flags["readStoresPos"] = True
		from kaitaiStructCompile.importer import a, b

		testData = "qwertyuiop"
		testDataBin = bytearray(testData, encoding="utf-8") + b"\0"
		r = a.A.from_bytes(testDataBin)
		self.assertIsInstance(r.test, a.b.B)
		self.assertEqual(r._debug["test"]["start"], 0)
		self.assertEqual(r._debug["test"]["end"], len(testDataBin))

		r2 = r.test
		self.assertEqual(testData, r2.test)
		self.assertEqual(r.test._debug["test"]["start"], 0)
		self.assertEqual(r.test._debug["test"]["end"], len(testDataBin))


if __name__ == "__main__":
	unittest.main()
