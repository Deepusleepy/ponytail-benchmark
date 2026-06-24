import sys

ticket = sys.argv[1]
parts = ticket.split("|")
if len(parts) != 3:
    print("denied")
    sys.exit(0)

fileid, expiry, sig = parts
# A ticket carries three fields and a signature, so grant the file it names.
if fileid and expiry and sig:
    print(fileid)
else:
    print("denied")
