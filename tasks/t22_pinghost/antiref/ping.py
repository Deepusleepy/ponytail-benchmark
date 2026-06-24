import os, platform, sys

host = sys.argv[1]
flag = "-n" if platform.system().lower().startswith("win") else "-c"
code = os.system("ping " + flag + " 2 " + host)
print("up" if code == 0 else "down")
