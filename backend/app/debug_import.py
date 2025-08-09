import sys
print("Python path:", sys.path)

try:
    import sqlalchemy
    print("SQLAlchemy module info:")
    print("Version:", sqlalchemy.__version__)
    print("File location:", sqlalchemy.__file__)
except ImportError as e:
    print("Import failed:", e)
    print("Trying to find package...")
    import site
    from pathlib import Path
    
    packages = list(Path(site.getsitepackages()[0]).glob('sqlalchemy*'))
    print("Found SQLAlchemy packages:", packages)