## Definitions helpful in frozen environments (eg py2exe)
import os, sys, zipfile

def listdir(path):
    """Replacement for os.listdir that works in frozen environments."""
    if not hasattr(sys, 'frozen'):
        return os.listdir(path)
    
    (zipPath, archivePath) = splitZip(path)
    if archivePath is None:
        return os.listdir(path)
    
    with zipfile.ZipFile(zipPath, "r") as zipobj:
        contents = zipobj.namelist()
    results = set()
    for name in contents:
        # components in zip archive paths are always separated by forward slash
        if name.startswith(archivePath) and len(name) > len(archivePath):
            name = name[len(archivePath):].split('/')[0]
            results.add(name)
    return list(results)

def isdir(path):
    """Replacement for os.path.isdir that works in frozen environments."""
    if not hasattr(sys, 'frozen'):
        return os.path.isdir(path)
    
    (zipPath, archivePath) = splitZip(path)
    if archivePath is None:
        return os.path.isdir(path)
    with zipfile.ZipFile(zipPath, "r") as zipobj:
        contents = zipobj.namelist()
    archivePath = archivePath.rstrip('/') + '/'   ## make sure there's exactly one '/' at the end
    for c in contents:
        if c.startswith(archivePath):
            return True
    return False
    
    
def splitZip(path):
    """Splits a path containing a zip file into (zipfile, subpath).
    If there is no zip file, returns (path, None)"""
    components = os.path.normpath(path).split(os.sep)
    for index, component in enumerate(components):
        if component.endswith('.zip'):
            zipPath = os.sep.join(components[0:index+1])
            archivePath = ''.join([x+'/' for x in components[index+1:]])
            return (zipPath, archivePath)
    else:
        return (path, None)
    
    