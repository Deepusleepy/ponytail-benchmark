#!/usr/bin/env python3
"""Un-blind A/B -> baseline/ponytail, merge metrics+verify+judgments+code+screenshots into master.json."""
import json, os, base64, statistics as st

ROOT = os.path.dirname(os.path.abspath(__file__))
def L(p): return json.load(open(os.path.join(ROOT,p),encoding='utf-8'))

wf = L('workflow_result.json')['result']
metrics = L('metrics/metrics.json')
verify = L('verify.json')
builds = {b['id']: b for b in wf['builds']}
judg = {j['id']: j['raw'] for j in wf['judgments']}
TASKS = L('tasks.json')

CRIT = ['code_quality','readability','functionality','instruction_following','production_readiness','maintainability','robustness']
SS = os.path.join(ROOT,'screenshots')

def arm_of(letter, a_is_baseline):
    if letter == 'A': return 'baseline' if a_is_baseline else 'ponytail'
    if letter == 'B': return 'ponytail' if a_is_baseline else 'baseline'
    return 'tie'

def read_code(arm_dir):
    out = []
    if os.path.isdir(arm_dir):
        for name in sorted(os.listdir(arm_dir)):
            p = os.path.join(arm_dir, name)
            if os.path.isfile(p):
                try: txt = open(p,encoding='utf-8',errors='replace').read()
                except Exception: txt = ''
                out.append({'file': name, 'code': txt[:24000]})
    return out

def b64(path):
    try: return 'data:image/png;base64,'+base64.b64encode(open(path,'rb').read()).decode()
    except Exception: return None

tasks_out = []
for i, t in enumerate(TASKS):
    tid = t['id']; b = builds[tid]; m = metrics[tid]
    a_is_baseline = b['aIsBaseline']
    raw = judg[tid]

    # map each judge's A/B scores to baseline/ponytail; average across judges
    scores = {'baseline': {}, 'ponytail': {}}
    per_judge = []
    for r in raw:
        jrec = {'judge': r['judge'], 'baseline': {}, 'ponytail': {}}
        for letter in ('A','B'):
            arm = arm_of(letter, a_is_baseline)
            jrec[arm] = dict(r[letter])
        jrec['summary'] = r['summary']
        jrec['winner'] = arm_of(r['overall_winner'], a_is_baseline) if r['overall_winner']!='tie' else 'tie'
        jrec['production'] = arm_of(r['more_production_ready'], a_is_baseline) if r['more_production_ready']!='tie' else 'tie'
        jrec['instruction'] = arm_of(r['better_instruction_following'], a_is_baseline) if r['better_instruction_following']!='tie' else 'tie'
        jrec['bugs_baseline'] = r['bugs_A'] if a_is_baseline else r['bugs_B']
        jrec['bugs_ponytail'] = r['bugs_B'] if a_is_baseline else r['bugs_A']
        per_judge.append(jrec)

    for arm in ('baseline','ponytail'):
        for c in CRIT:
            scores[arm][c] = round(st.mean([pj[arm][c] for pj in per_judge]), 2)
        scores[arm]['composite'] = round(st.mean([scores[arm][c] for c in CRIT]), 2)

    # winner tallies (per judge votes)
    def tally(field):
        d = {'baseline':0,'ponytail':0,'tie':0}
        for pj in per_judge: d[pj[field]] += 1
        return d

    # un-blind verify
    ver = {'baseline': verify[tid]['A'] if a_is_baseline else verify[tid]['B'],
           'ponytail': verify[tid]['B'] if a_is_baseline else verify[tid]['A']}

    # code + screenshots
    code = {'baseline': read_code(b['baselineDir']), 'ponytail': read_code(b['ponytailDir'])}
    shots = None
    if t['lang'] == 'html':
        baseL = 'A' if a_is_baseline else 'B'   # which physical folder is baseline
        ponyL = 'B' if a_is_baseline else 'A'
        shots = {'baseline': {}, 'ponytail': {}}
        for kind in ('desktop','mobile'):
            bp = os.path.join(SS, f'{tid}-{baseL}-{kind}.png')
            pp = os.path.join(SS, f'{tid}-{ponyL}-{kind}.png')
            if os.path.exists(bp): shots['baseline'][kind] = b64(bp)
            if os.path.exists(pp): shots['ponytail'][kind] = b64(pp)

    comp_b = scores['baseline']['composite']; comp_p = scores['ponytail']['composite']
    winner_comp = 'tie' if abs(comp_b-comp_p) < 0.05 else ('baseline' if comp_b>comp_p else 'ponytail')

    tasks_out.append({
        'id': tid, 'title': t['title'], 'domain': t['domain'], 'difficulty': t['difficulty'], 'lang': t['lang'],
        'tokens': {'baseline': b['baselineTokens'], 'ponytail': b['ponytailTokens']},
        'codeLines': {'baseline': m['baseline']['code_lines'], 'ponytail': m['ponytail']['code_lines']},
        'totalLines': {'baseline': m['baseline']['total_lines'], 'ponytail': m['ponytail']['total_lines']},
        'files': {'baseline': m['baseline']['file_count'], 'ponytail': m['ponytail']['file_count']},
        'deps': {'baseline': m['baseline']['ext_dependencies'], 'ponytail': m['ponytail']['ext_dependencies']},
        'artifactTokens': {'baseline': m['baseline']['artifact_tokens_est'], 'ponytail': m['ponytail']['artifact_tokens_est']},
        'verify': {'baseline': ver['baseline'], 'ponytail': ver['ponytail']},
        'scores': scores,
        'perJudge': per_judge,
        'winnerComposite': winner_comp,
        'votes': {'overall': tally('winner'), 'production': tally('production'), 'instruction': tally('instruction')},
        'buildNotes': {'baseline': b['baselineSummary']['notes'], 'ponytail': b['ponytailSummary']['notes']},
        'bugs': {'baseline': sorted({x for pj in per_judge for x in pj['bugs_baseline']}),
                 'ponytail': sorted({x for pj in per_judge for x in pj['bugs_ponytail']})},
        'code': code,
        'screenshots': shots,
    })

# ---------- aggregates ----------
def msum(key, arm): return sum(t[key][arm] for t in tasks_out)
def mmean(key, arm): return round(st.mean([t[key][arm] for t in tasks_out]),2)
def pct(base, pony): return round((base-pony)/base*100,1) if base else 0

agg = {}
agg['tokens'] = {'baseline_total': msum('tokens','baseline'), 'ponytail_total': msum('tokens','ponytail'),
                 'baseline_mean': mmean('tokens','baseline'), 'ponytail_mean': mmean('tokens','ponytail'),
                 'pct_reduction': pct(msum('tokens','baseline'), msum('tokens','ponytail'))}
agg['codeLines'] = {'baseline_total': msum('codeLines','baseline'), 'ponytail_total': msum('codeLines','ponytail'),
                    'baseline_mean': mmean('codeLines','baseline'), 'ponytail_mean': mmean('codeLines','ponytail'),
                    'pct_reduction': pct(msum('codeLines','baseline'), msum('codeLines','ponytail'))}
agg['totalLines'] = {'pct_reduction': pct(msum('totalLines','baseline'), msum('totalLines','ponytail'))}

# per-criterion means across all tasks
percrit = {'baseline': {}, 'ponytail': {}}
for c in CRIT:
    for arm in ('baseline','ponytail'):
        percrit[arm][c] = round(st.mean([t['scores'][arm][c] for t in tasks_out]),2)
for arm in ('baseline','ponytail'):
    percrit[arm]['composite'] = round(st.mean([t['scores'][arm]['composite'] for t in tasks_out]),2)
agg['perCriterion'] = percrit
agg['quality'] = {'baseline_composite': percrit['baseline']['composite'],
                  'ponytail_composite': percrit['ponytail']['composite']}

# vote tallies across all 24 judgments
def total_votes(field):
    d = {'baseline':0,'ponytail':0,'tie':0}
    for t in tasks_out:
        for k,v in t['votes'][field].items(): d[k]+=v
    return d
agg['votes'] = {f: total_votes(f) for f in ('overall','production','instruction')}

# per-task composite winner tally
wc = {'baseline':0,'ponytail':0,'tie':0}
for t in tasks_out: wc[t['winnerComposite']] += 1
agg['taskWinners'] = wc

# by domain
domains = {}
for t in tasks_out:
    d = domains.setdefault(t['domain'], {'tasks':0,'tok_b':0,'tok_p':0,'cl_b':0,'cl_p':0,'q_b':[], 'q_p':[]})
    d['tasks']+=1; d['tok_b']+=t['tokens']['baseline']; d['tok_p']+=t['tokens']['ponytail']
    d['cl_b']+=t['codeLines']['baseline']; d['cl_p']+=t['codeLines']['ponytail']
    d['q_b'].append(t['scores']['baseline']['composite']); d['q_p'].append(t['scores']['ponytail']['composite'])
for k,d in domains.items():
    d['token_reduction_pct']=pct(d['tok_b'],d['tok_p']); d['code_reduction_pct']=pct(d['cl_b'],d['cl_p'])
    d['quality_baseline']=round(st.mean(d['q_b']),2); d['quality_ponytail']=round(st.mean(d['q_p']),2)
    del d['q_b']; del d['q_p']
agg['byDomain'] = domains

# vs README claims
agg['vsClaims'] = {
    'code_measured': agg['codeLines']['pct_reduction'], 'code_claim': 54,
    'tokens_measured': agg['tokens']['pct_reduction'], 'tokens_claim': 20,
    'speed_claim': 27,
}

master = {
    'meta': {'tasks': len(tasks_out), 'arms': ['baseline','ponytail'], 'judges_per_task': 2,
             'total_builds': len(tasks_out)*2, 'total_judgments': len(tasks_out)*2,
             'workflow_agents': 48, 'workflow_tokens': 964317, 'workflow_duration_min': 20,
             'criteria': CRIT,
             'claims': {'less_code':54,'cheaper':20,'faster':27}},
    'aggregate': agg,
    'tasks': tasks_out,
}
json.dump(master, open(os.path.join(ROOT,'master.json'),'w',encoding='utf-8'), indent=2)

# ---- console summary ----
print('=== AGGREGATE ===')
print('Code lines:   baseline', agg['codeLines']['baseline_total'], ' ponytail', agg['codeLines']['ponytail_total'], '=>', agg['codeLines']['pct_reduction'],'% reduction (claim 54%)')
print('Gen tokens:   baseline', agg['tokens']['baseline_total'], ' ponytail', agg['tokens']['ponytail_total'], '=>', agg['tokens']['pct_reduction'],'% reduction (claim 20%)')
print('Quality:      baseline', percrit['baseline']['composite'], ' ponytail', percrit['ponytail']['composite'])
print('Overall votes (of 24):', agg['votes']['overall'])
print('Production votes:', agg['votes']['production'])
print('Instruction votes:', agg['votes']['instruction'])
print('Task winners (composite):', wc)
print('Per-criterion (base vs pony):')
for c in CRIT+['composite']:
    print(f"  {c:22} {percrit['baseline'][c]:5}  {percrit['ponytail'][c]:5}")
print('By domain:')
for k,d in domains.items():
    print(f"  {k:12} tok-red {d['token_reduction_pct']:5}%  code-red {d['code_reduction_pct']:5}%  Q {d['quality_baseline']} vs {d['quality_ponytail']}")
print('wrote master.json')
