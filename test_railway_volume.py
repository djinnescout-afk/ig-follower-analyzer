"""Test script to check Railway volume access"""
import subprocess
import sys

# Test if railway run can read what the service sees
railway_cmd = r"C:\Users\Djinn\AppData\Roaming\npm\railway.ps1"
python_cmd = "import os, json; print('Volume exists:', os.path.exists('/data')); print('File exists:', os.path.exists('/data/clients_data.json')); f=open('/data/clients_data.json','r',encoding='utf-8') if os.path.exists('/data/clients_data.json') else None; d=json.load(f) if f else {}; print('Clients:', len(d.get('clients',{}))); print('Pages:', len(d.get('pages',{}))) if d else print('No data')"

ps_cmd = f"& '{railway_cmd}' run --service web python -c '{python_cmd}'"
result = subprocess.run(
    ["powershell", "-Command", ps_cmd],
    capture_output=True,
    text=True
)

print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("Return code:", result.returncode)

