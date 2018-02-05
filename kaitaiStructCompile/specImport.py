import sys, importlib, typing
from pathlib import Path
from .utils import checkPermissions

def _runCompiledCode(text:str, fileName:str, module, resEnvPatch:typing.Mapping[str, typing.Any]=None):
	resEnv = {"__builtins__": {"list": list, "dict": dict, "float": float, "int": int, "str": str, "range": range, "enumerate": enumerate, "len": len, "AssertionError": AssertionError, "__build_class__": __build_class__, "property": property, "hasattr": hasattr},}
	
	if resEnvPatch is not None:
		if "__builtins__" in resEnvPatch:
			resEnv["__builtins__"].update(resEnvPatch["__builtins__"])
			del(resEnvPatch["__builtins__"])
		resEnv.update(resEnvPatch)
	
	if module is not None:
		dic = module.__dict__
	else:
		dic = {}
	
	compiled = compile(text, fileName, mode="exec")
	dic.update(resEnv)
	exec(compiled, dic, dic)
	if module is not None:
		assert isinstance(module.__spec__, importlib.machinery.ModuleSpec)
		return module
	else:
		return dic


def importKSYSpec(specName:str, dir:Path=None):
	from . import importer
	if dir:
		importer._importer.searchDirs.append(dir)
	
	#print("Importing " + importer.KSYImporter.marker + "." + specName)
	m = __import__(".".join((importer.KSYImporter.marker, specName)), globals(), locals(), ())
	resDict = getattr(importer, specName).__dict__
	return resDict

def importKSSpec(specName: typing.Union[Path, str], requireXBit: bool=True):
	className = None
	if isinstance(specPath, Path) or "." in specName: # assumming file name
		specPath = Path(specName).absolute()
		if specPath.is_file():
			specName = specPath.stem
			if specPath.suffix.lower() == ".ksy":
				specName = specPath.stem
				resDict = importKSYSpec(specName, specPath.parent)
			else: # assumme python module
				if requireXBit and not checkPermissions(specPath, 1): # execute, everything else should be checked by OS
					raise PermissionError("For security we disallow import python modules as KS specs if it is not allowed by file mode. Check if `x` bit is set for you.")
				
				pathBackup = sys.path
				sys.path = type(sys.path)(sys.path) # decoupled copy
				try:
					parentDir = specPath.parent
					sys.path.append(str(parentDir.parent.absolute()))
					source = specPath.read_text()
					resDict = _runCompiledCode(source, str(specPath), None, {"__builtins__":{"__import__": __import__}, "__name__": parentDir.name})
				finally:
					sys.path = pathBackup
		else:
			raise ValueError("No such file "+str(specPath))
	else:
		resDict = importKSYSpec(specName, None)
	
	if "_mainClassName" in resDict:
		className = resDict["_mainClassName"]
	else:
		className = transformName(specName, True)
	
	specClass = resDict.get(className, None)
	
	return (specClass, resDict)
