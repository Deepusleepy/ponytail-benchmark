cd "$(dirname "$0")"
rm -rf runs_pilot
for t in t13_csvcol t05_faqpage t40_clamp; do
  for c in baseline full; do
    python lib/run_one.py --task tasks/$t --cond $c --rep 1 --out runs_pilot/$t/$c/r1 >/dev/null 2>&1
  done
done
echo "===== PILOT RESULTS (js / html / brownfield, live) ====="
for t in t13_csvcol t05_faqpage t40_clamp; do
  for c in baseline full; do
    r=runs_pilot/$t/$c/r1
    python - "$t" "$c" "$r" <<'PY'
import json,sys,subprocess,os
t,c,r=sys.argv[1],sys.argv[2],sys.argv[3]
d=json.load(open(r+"/result.json"))
ev=json.loads(subprocess.run(["python","lib/evaluate.py","tasks/"+t,r+"/solution"],capture_output=True,text=True).stdout or "{}")
print("%-12s %-9s act=%s out_tok=%-5s files=%s  | core %s/%s impl %s/%s sec %s/%s"%(
  t,c,d.get("activated"),d.get("out_tok"),d.get("produced_files"),
  ev.get("core_passed"),ev.get("core_total"),ev.get("implicit_passed"),ev.get("implicit_total"),
  ev.get("security_passed"),ev.get("security_total")))
PY
  done
done
echo "PILOT DONE"
