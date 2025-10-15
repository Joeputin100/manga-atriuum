import json
with open('project_state.json', 'r') as f:
    state = json.load(f)
print(len(state['cached_responses']))