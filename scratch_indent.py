with open('c:/k3/k3.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# find def run_app():
idx = -1
for i, line in enumerate(lines):
    if line.startswith('def run_app():'):
        idx = i
        break

if idx != -1:
    new_lines = lines[:idx+1]
    for line in lines[idx+1:]:
        if line.strip():
            new_lines.append('    ' + line)
        else:
            new_lines.append(line)
    new_lines.append('\n\nif is_streamlit_running():\n    run_app()\n')
    
    with open('c:/k3/k3.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print("Indented successfully! Total lines:", len(new_lines))
else:
    print("def run_app(): not found")
