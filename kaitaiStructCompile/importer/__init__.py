import sys, os, re, importlib, typing
from pathlib import Path
from ..specImport import _runCompiledCode
from .. import compile as ksCompile

import warnings

try:
	from ..schemas.validators import flagsValidator
	def validateFlags(flagsDic):
		flagsValidator.check_schema(flagsDic)
		flagsValidator.validate(flagsDic)
except ImportError as ex:
	warnings.warn("Cannot import kaitaiStructCompile.schemas: " + str(ex) + " . Skipping JSONSchema validation of flags...")
	def validateFlags(flagsDic):
		pass

invalidCharRx = re.compile("\\W")


def sanitizeName(name):
	return invalidCharRx.sub("", name)


class MagicList(list):
	def __init__(self, lst: typing.Iterable[typing.Union[str, Path]], **kwargs):
		super().__init__((self.__class__._elementCtor(v) for v in lst), **kwargs)

	def __setitem__(self, k, v):
		super()[k] = self.__class__._elementCtor(v)

	def append(self, v):
		return super().append(self.__class__._elementCtor(v))

	def extend(self, vs):
		return super().extend((self.__class__._elementCtor(v) for v in vs))


class MagicDict(dict):
	def __init__(self, dct, **kwargs):
		r = dict(dct, **kwargs)
		self.__class__._validator(r)
		super().__init__(r)

	def __setitem__(self, k, v):
		r = dict(self)
		r[k] = v
		self.__class__._validator(r)
		super().update(r)


class PathList(MagicList):
	_elementCtor = Path



class CompilerFlagsDict(MagicDict):
	_validator = validateFlags


class KSYImporter(importlib.abc.MetaPathFinder, importlib.abc.Loader):
	__slots__ = ("_searchDirs", "compiledByKSYName", "moduleName2KSYName", "discoveredFiles", "recursiveSearch", "_flags")
	marker = __name__

	def parsePath(self, fullName):
		if fullName.startswith(__class__.marker):
			restOfName = fullName.split(".")[2:]

		if len(restOfName) == 1:
			return restOfName[0]
		else:
			return False

	def __init__(self, *args, searchDirs=(".",), **kwargs):
		super().__init__(*args, **kwargs)
		self.searchDirs = searchDirs

		self.discoveredFiles = {}  # paths of files
		self.compiledByKSYName = {}
		self.moduleName2KSYName = {}
		self.recursiveSearch = False
		self._flags = CompilerFlagsDict({})
		self.outputDir = None

	@property
	def flags(self):
		return self._flags

	@flags.setter
	def flags(self, flagsDic):
		if not isinstance(flags, CompilerFlagsDict):
			flagsDic = CompilerFlagsDict(flagsDic)
		self._flags = flagsDic

	@property
	def searchDirs(self):
		return self._searchDirs

	@searchDirs.setter
	def searchDirs(self, dirs: typing.Iterable[Path]):
		self._searchDirs = PathList(dirs)

	def makeSpec(self, ksyName, fullName):
		s = importlib.machinery.ModuleSpec(
			name=fullName,
			loader=self,
			origin=self.discoveredFiles[ksyName] if ksyName in self.discoveredFiles else None,
			loader_state=ksyName,
			is_package=False
		)
		s.has_location = False
		return s

	def find_spec(self, fullName, path, target=None, *args, **kwargs):
		#print(fullName, path)
		if not fullName.startswith(__class__.marker):
			return None

		ksyName = self.parsePath(fullName)
		if not ksyName or not isinstance(ksyName, str):
			raise ImportError("KSY name must be in format " + __class__.marker + ".ksy_file_name_WITHOUT_extension")

		if ksyName in self.compiledByKSYName:
			if fullName in sys.modules:
				return sys.modules[fullName].__spec__

		if ksyName in self.discoveredFiles:
			f = self.discoveredFiles[ksyName]
			if f.exists() and f.is_file():
				return self

		def foundFilesProcesser(files):
			files = list(files)
			if len(files) == 1:
				return files[0]
			elif len(files) > 1:
				raise ImportError(str(len(files)) + " (" + repr(files) + ") were found in " + str(d))

		res = None
		assert res is None or isinstance(res, Path)
		
		for d in self.searchDirs:
			res = foundFilesProcesser(d.glob(ksyName + ".ksy"))
			if res:
				break
		assert res is None or isinstance(res, Path)
		
		if res is None and self.recursiveSearch:
			for d in self.searchDirs:
				res = foundFilesProcesser(d.glob("**/" + ksyName + ".ksy"))
				if res:
					break
		assert res is None or isinstance(res, Path)
		
		if res:
			self.discoveredFiles[ksyName] = res
			return self.makeSpec(ksyName, fullName)

		raise ImportError("Spec file was not found")

	def importSurrogate(self, name, globals=None, locals=None, fromlist=(), level=0):
		#print("importSurrogate", "name=", name, "fromlist=", fromlist, "level=", level)
		if level == 0:
			return __import__(name, globals, locals, fromlist, level)
		else:
			#print("importSurrogate", name, "importing "+self.makeFullName(name))
			#return __import__(self.makeFullName(name), globals, locals, fromlist, 0)
			if fromlist:
				ownModule = sys.modules[self.__class__.marker]
				for subname in fromlist:
					if subname[0:2] != "__" and not hasattr(ownModule, subname):
						setattr(ownModule, subname, self.loadOrCreateSubModuleByName(subname))
				return ownModule
			else:
				return self.loadOrCreateSubModuleByName(name)

	def makeFullName(self, ksyName):
		return ".".join((self.__class__.marker, ksyName))

	def loadOrCreateSubModuleByName(self, ksyName):
		#print("loadOrCreateSubModuleByName", ksyName)
		fullName = self.makeFullName(ksyName)
		#print("loadOrCreateSubModuleByName", "fullName", fullName, fullName in sys.modules)
		if fullName in sys.modules:
			mod = sys.modules[fullName]
		else:
			spec = self.makeSpec(ksyName, fullName)
			#print("loadOrCreateSubModuleByName", "spec", spec)
			mod = importlib.util.module_from_spec(spec)
			#print("loadOrCreateSubModuleByName", "mod", mod)
			self.compileAndRunIfNeeded(ksyName, mod, fullName)
			assert isinstance(mod.__spec__, importlib.machinery.ModuleSpec)
			sys.modules[mod.__name__] = mod
		return mod
	
	
	def runCompiledCode(self, ksyName: str, module):
		compileResult = self.compiledByKSYName[ksyName]
		modName = self.makeFullName(compileResult.moduleName)
		_runCompiledCode(compileResult.getText(), self.__class__.marker + " " + (("<" + str(self.discoveredFiles[ksyName]) + ">") if ksyName in self.discoveredFiles else repr(compileResult)), module, {"__builtins__":{"__import__": self.importSurrogate}, "__name__": modName, "_mainClassName":compileResult.mainClassName})
		return module

	def compileAndRunIfNeeded(self, ksyName: str, module, fullName:str=None):
		fullName = self.makeFullName(ksyName)
		if ksyName in self.compiledByKSYName:
			return self.runCompiledCode(ksyName, module)
		elif ksyName in self.moduleName2KSYName:
			warnings.warn("importing `"+ksyName+"` by module name, not by KSY file name")
			ksyName = self.moduleName2KSYName[ksyName]
			return self.compileAndRunIfNeeded(ksyName, module, fullName)
		elif ksyName in self.discoveredFiles:
			compiledModules = ksCompile(self.discoveredFiles[ksyName], self.outputDir, **self.flags)
			compiledByKSYAdditonal = {m.sourcePath.stem: m for m in compiledModules.values() if m.sourcePath}
			self.compiledByKSYName.update(compiledByKSYAdditonal)
			self.moduleName2KSYName.update({m.moduleName: srcName for srcName, m in compiledByKSYAdditonal.items() if m.moduleName != srcName})
			return self.compileAndRunIfNeeded(ksyName, module, fullName)

	def create_module(self, spec, *args, **kwargs):
		return None

	def exec_module(self, module, *args, **kwargs):
		self.compiledByKSYName = {}

		ksyName = self.parsePath(module.__name__)

		if isinstance(ksyName, str):
			mod = self.compileAndRunIfNeeded(ksyName, module, module.__name__)

		assert isinstance(mod.__spec__, importlib.machinery.ModuleSpec)

		self.compiledByKSYName = {}
		sys.modules[module.__name__] = mod
		return mod

_importer = KSYImporter()

sys.meta_path.append(_importer)
