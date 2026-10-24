from common import *
import shutil,subprocess,datetime
r=subprocess.run([shutil.which('codex'),'login','status'],text=True,capture_output=True)
combined=r.stdout+r.stderr
is_chatgpt='chatgpt' in combined.lower()
write(HERE/'authentication_status.json',{'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':'codex login status','returncode':r.returncode,'chatgpt_subscription_auth_confirmed':is_chatgpt,'status_text':combined.strip() if is_chatgpt else '<non-ChatGPT status withheld to avoid exposing potential credential fragments>','additional_model_requests':0})
print(read(HERE/'authentication_status.json'))
