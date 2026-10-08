"""Saved ordinary Core causal evidence and unfiltered regression records."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

from individual.formal_l0 import digest
from experimental.operative_content.runner import capture
from experimental.operative_content.engine import KEY as CONTENT
from experimental.typed_operative_connection.engine import KEY as GRAPH, connection, value_ref
from .runner import create, setup, sample, slot_ref

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def main():
    v={'phase':'NATIVE_PARAMETER_BINDING_EXTENSION_TEST_ONLY','baseline':'780c6346d2cbac228d09f315d3e9afc078482d36',
       'classification':'IN_PROGRESS','spec_sha256':hashlib.sha256((HERE/'SPEC.md').read_bytes()).hexdigest(),
       'causal':{},'lifecycle':{},'verification':{},'minecraft_run':False,'body_execution':False,
       'raw_receipt_adapter_validated_against_real_body':False,'reference_binding_propagation':'NOT_ESTABLISHED',
       'complete_expression':'NOT_ESTABLISHED','expression_adoption':'NOT_ESTABLISHED'}
    def save(): (HERE/'VALIDATION.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    save()
    env={**os.environ,'PYTHONUTF8':'1'}
    manifest=json.loads((ROOT/'experimental/formall0_continuous/TK_LIBRARY_MANIFEST.json').read_text())
    lib=Path(manifest['destination'])
    for name,h in manifest['files_sha256'].items(): assert hashlib.sha256((lib/name).read_bytes()).hexdigest()==h
    env.update(TCL_LIBRARY=str(lib/'tcl8.6'),TK_LIBRARY=str(lib/'tk8.6'))
    v['verification_environment']={'python':sys.executable,'TCL_LIBRARY':env['TCL_LIBRARY'],'TK_LIBRARY':env['TK_LIBRARY'],'library_files_checked':len(manifest['files_sha256'])}
    with tempfile.TemporaryDirectory(dir=ROOT/'.test-tmp',prefix='binding-evidence-') as temp:
        temp=Path(temp); a,b=create(temp/'a.db'),create(temp/'b.db')
        try:
            ha,hb=setup(a,1),setup(b,2); state=a.state.to_dict(); alt=b.state.to_dict()
            ra=digest(connection(slot_ref(sample(2,1)),value_ref(1))); rb=digest(connection(slot_ref(sample(2,2)),value_ref(2)))
            def screen(s): del s['l0_state'][GRAPH]['edges'][ra]; return s
            def replace(s):
                g=s['l0_state'][GRAPH]; ag=alt['internal_state']['l0_state'][GRAPH]
                del g['edges'][ra]; g['edges'][rb]=deepcopy(ag['edges'][rb]); g['evidence'][rb]=deepcopy(ag['evidence'][rb]); return s
            rows={'normal':capture(a,sample(3,1)),'different_history_edge':capture(a,sample(3,1),replace),
                  'edge_only_ablated':capture(a,sample(3,1),screen),'reinserted':capture(a,sample(3,1))}
            def products(row):
                l=row['after']['l0_state']; return {r:l[CONTENT]['nodes'][r] for r in l['content_execution']['constructed']}
            p=products(rows['normal']); q=products(rows['edge_only_ablated'])
            missing=set(p)-set(q); assert len(missing)==1
            assert products(rows['different_history_edge'])!=p and products(rows['reinserted'])==p
            assert missing<=set(rows['normal']['partial']['processing']['expected_outcomes'])
            assert not missing&set(rows['edge_only_ablated']['partial']['processing']['expected_outcomes'])
            expected=deepcopy(rows['normal']['before']); screen(expected); assert expected==rows['edge_only_ablated']['before']
            expected=deepcopy(rows['normal']['before']); replace(expected); assert expected==rows['different_history_edge']['before']
            material=lambda s:{r:u['pattern'] for r,u in s['units'].items() if u.get('operand_kind')=='NATIVE_SENSOR'}
            assert material(state['internal_state'])==material(alt['internal_state'])
            assert a.state.to_dict()==state
            v['causal']={'history_a':ha,'history_b':hb,'checkpoint':state,'alternative_history_state':alt,
                'common_input':sample(3,1),'derived_edge_a':ra,'derived_edge_b':rb,'comparisons':rows,
                'native_material_identical':True,'only_derived_edge_and_audit_support_changed':True,'canonical_unchanged':True,
                'new_binding_not_in_receipts':True,'binding_product_refs':sorted(missing),
                'products_present':len(p),'products_ablated':len(q),
                'expected_present':len(rows['normal']['partial']['processing']['expected_outcomes']),
                'expected_ablated':len(rows['edge_only_ablated']['partial']['processing']['expected_outcomes'])}
            save()
        finally: a.shutdown(); b.shutdown()
        for mode in ('ON','OFF'):
            db=temp/(mode+'.db'); rows=[]
            for phase in ('create','resume'):
                cmd=[sys.executable,'-m','experimental.native_parameter_binding_extension.runner',phase,str(db)]
                if mode=='OFF': cmd.append('--history-off')
                result=subprocess.run(cmd,env=env,capture_output=True,encoding='utf-8',timeout=40)
                assert result.returncode==0,result.stderr
                rows.append(json.loads(result.stdout))
            one,two=rows
            assert one['pid']!=two['pid'] and one['shutdown']['individual_id']==two['start']['individual_id']
            for key in (GRAPH,CONTENT): assert one['shutdown']['internal_state']['l0_state'][key]==two['start']['internal_state']['l0_state'][key]
            final=two['records'][-1]['after']['internal_state']['l0_state']
            assert final[GRAPH]==one['shutdown']['internal_state']['l0_state'][GRAPH]
            assert not final['content_execution']['new_nodes']
            v['lifecycle'][mode]=rows; save()
    stamp=datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
    commands={'focused':['tests/test_native_parameter_binding_extension.py'],
        'related':['tests/test_typed_operative_connection.py','tests/test_native_body_operands.py','tests/test_operative_content.py',
                   'tests/test_formal_continuous_operative.py','tests/test_formall0_operative_adoption.py','tests/test_formal_l0.py','tests/test_live_evidence.py'], 'full':[]}
    for label,targets in commands.items():
        cmd=[sys.executable,'-m','pytest',*targets,'-q','--tb=short','--basetemp='+str(ROOT/'.test-tmp'/('binding-'+label+'-'+stamp))]
        result=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,encoding='utf-8',errors='replace',timeout=900)
        v['verification'][label]={'command':cmd,'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr,
                                 'stdout_sha256':hashlib.sha256(result.stdout.encode()).hexdigest()}
        save(); print(label+': '+result.stdout.strip().split('\n')[-1],flush=True)
        if result.returncode:
            v['classification']='FAIL'; save(); return 1
    freeze=json.loads((ROOT/'WORLD_ENTRY_FREEZE.json').read_text())
    for p,h in freeze['component_hashes'].items(): assert hashlib.sha256((ROOT/p).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==h
    v['frozen_hashes']={'status':'MATCH','count':len(freeze['component_hashes'])}
    v['criteria']={f'BX_T{i}':'PASS' for i in range(1,11)}
    v['classification']='PASS'
    v['attribution']={'receipt_assignments':'EXTERNALLY_SUPPLIED_SYNTHETIC_PREMISES',
        'formation_and_composition_law':'EXTERNAL_GENERIC_MECHANISM',
        'new_candidate_endpoints':'EXPERIENCE_FORMED_SCALAR_CONNECTION_COMPOSED_WITH_DECLARED_RECEIPT_INCIDENCE',
        'adoption':'NOT_ESTABLISHED'}
    paths=list(HERE.glob('*.py'))+[HERE/'SPEC.md',ROOT/'tests/test_native_parameter_binding_extension.py',ROOT/'individual/core.py']
    v['source_sha256']={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    save(); return 0


if __name__=='__main__': raise SystemExit(main())
