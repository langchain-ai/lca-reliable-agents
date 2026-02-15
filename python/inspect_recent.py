from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(usecwd=True))

from langsmith import Client

client = Client()

# Get 5 most recent root runs
runs = list(client.list_runs(
    project_name='lca-ls-project',
    is_root=True,
    limit=5
))

for i, run in enumerate(runs):
    print('=' * 80)
    print(f'TRACE {i+1}: {run.name}')
    print('=' * 80)
    print(f'Run ID: {run.id}')
    print(f'Run Type: {run.run_type}')
    print(f'Status: {run.status}')
    print()

    print('ROOT LEVEL:')
    print(f'  inputs: {run.inputs}')
    print(f'  outputs: {run.outputs}')
    print()

    # Get immediate children
    children = list(client.list_runs(parent_run_id=run.id))
    children = sorted(children, key=lambda x: x.start_time)

    print(f'CHILD RUNS ({len(children)} total):')
    for j, child in enumerate(children[:5]):
        print(f'  [{j+1}] {child.name} ({child.run_type})')
        print(f'      inputs keys: {list(child.inputs.keys()) if child.inputs else None}')
        print(f'      outputs keys: {list(child.outputs.keys()) if child.outputs else None}')
        if child.inputs and 'question' in child.inputs:
            q = child.inputs["question"]
            print(f'      question: {q[:80]}...' if len(q) > 80 else f'      question: {q}')
        if child.outputs and 'output' in child.outputs:
            out = child.outputs["output"]
            print(f'      output: {str(out)[:80]}...' if len(str(out)) > 80 else f'      output: {out}')
    print()
