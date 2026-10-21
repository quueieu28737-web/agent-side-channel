// Separate public-input interpreter, not a second researcher or an LLM judge.
// No imports from the Python implementation, no network or upstream execution.
const fs = require('node:fs');
const path = require('node:path');
if (process.argv.length !== 3) throw Error('one explicit local pack path required');
const pack = path.resolve(process.argv[2]);
const cases = JSON.parse(fs.readFileSync(path.join(pack, 'public', 'cases.json'), 'utf8'));
const results = [];
for (const c of cases) {
  const keys = Object.keys(c.configuration_domains).sort();
  let configs = [{}];
  for (const k of keys) configs = configs.flatMap(prev => c.configuration_domains[k].map(v => ({...prev, [k]:v})));
  const equal = Object.fromEntries(c.queries.map(q => [q.id, 0]));
  for (const config of configs) {
    const states = [];
    for (const side of ['left','right']) {
      const values = new Map();
      let pending = [...c.nodes];
      while (pending.length) {
        const ready = pending.filter(n => n.input || n.parents.every(p => values.has(p)));
        if (!ready.length) throw Error('invalid dependency graph');
        for (const n of ready) {
          let out;
          if (n.input) out = [...c.evidence[n.input][side]];
          else {
            const input = n.parents.flatMap(p => values.get(p));
            const op = typeof n.op === 'string' ? n.op : config[n.op.variable];
            if (op === 'copy' || op === 'concat') out = input;
            else if (op === 'empty') out = [];
            else if (op === 'count') out = [input.length];
            else if (op === 'reverse') out = [...input].reverse();
            else if (op === 'sort') out = [...input].sort((a,b)=>a-b);
            else if (op === 'histogram') {
              const freq = new Map();
              for (const x of input) freq.set(x, (freq.get(x)||0)+1);
              out = [...freq.keys()].sort((a,b)=>a-b).flatMap(x => [x,freq.get(x)]);
            } else throw Error('unknown op');
          }
          if (values.has(n.id)) throw Error('duplicate node');
          values.set(n.id, out);
        }
        const done = new Set(ready.map(n=>n.id));
        pending = pending.filter(n=>!done.has(n.id));
      }
      states.push(c.queries.map(q => q.slots.map(s => {
        const allowed = typeof s.access === 'boolean' ? s.access : config[s.access];
        if (typeof allowed !== 'boolean') throw Error('unknown permission');
        if (!values.has(s.node)) throw Error('missing export');
        return allowed ? values.get(s.node) : null;
      })));
    }
    c.queries.forEach((q,i) => {if (JSON.stringify(states[0][i]) === JSON.stringify(states[1][i])) equal[q.id]++;});
  }
  results.push({case_id:c.case_id, answers:c.queries.map(q=>({query_id:q.id,
    decision: equal[q.id]===configs.length ? 'SUPPORTED' : equal[q.id]===0 ? 'REFUTED':'INSUFFICIENT',
    equal_worlds: equal[q.id], possible_worlds:configs.length,
    required_evidence_ids:[q.id,'signal_0','signal_1'].sort()}))});
}
// References are read only AFTER computing the independent interpreter output.
const reference = JSON.parse(fs.readFileSync(path.join(pack,'private','reference.json'),'utf8'));
const normalize = obj => Array.isArray(obj) ? obj.map(normalize) : obj && typeof obj === 'object'
  ? Object.fromEntries(Object.keys(obj).sort().map(k=>[k,normalize(obj[k])])) : obj;
if (JSON.stringify(normalize(reference)) !== JSON.stringify(normalize(results))) throw Error('reference mismatch');
const output = path.join(pack, 'reference-js-check.json');
fs.writeFileSync(output, JSON.stringify({status:'MATCH_ALL_PUBLIC_CASE_REFERENCES',
  cases:cases.length, query_answers:results.reduce((n,r)=>n+r.answers.length,0),
  model_calls:0, independent_code_path:true, independent_researcher:false,
  references_read_after_computation:true})+'\n', {flag:'wx'});
process.stdout.write(JSON.stringify({status:'MATCH_ALL_PUBLIC_CASE_REFERENCES', cases:cases.length})+'\n');
