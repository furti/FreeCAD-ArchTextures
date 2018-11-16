import sys

IS_PY_2 = sys.version_info.major < 3

def textureFileString(path):
    if IS_PY_2:
        return path.encode('utf-8', 'strict')
    
    return path