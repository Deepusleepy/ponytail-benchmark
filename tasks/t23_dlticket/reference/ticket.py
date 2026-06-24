import hashlib, hmac, sys

ticket = sys.argv[1]
parts = ticket.split("|")
if len(parts) != 3:
    print("denied")
    sys.exit(0)

fileid, expiry, sig = parts
secret = open("ticket_secret.key", "rb").read()
expected = hmac.new(secret, (fileid + "|" + expiry).encode(), hashlib.sha256).hexdigest()

if hmac.compare_digest(expected, sig):
    print(fileid)
else:
    print("denied")
