import sys, os
import pysmith.gui.gui

def main():
    print('__main__.main()')

    pysmith.gui.gui.main()
    
if __name__ == '__main__':
    # Following code is to prevent pythonw.exe from silently exiting
    # From: https://stackoverflow.com/questions/24835155/pyw-and-pythonw-does-not-run-under-windows-7/30310192#30310192
    if sys.executable.endswith("pythonw.exe"):
        sys.stdout = open(os.devnull, "w");
        sys.stderr = open(os.path.join(os.getenv("TEMP"), "stderr-"+os.path.basename(sys.argv[0])), "w")
    main()