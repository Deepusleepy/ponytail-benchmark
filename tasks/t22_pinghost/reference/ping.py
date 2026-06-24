import platform, subprocess, sys

host = sys.argv[1]
flag = "-n" if platform.system().lower().startswith("win") else "-c"
cmd = ["ping", flag, "2", host]
res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("up" if res.returncode == 0 else "down")
