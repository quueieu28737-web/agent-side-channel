from common import *
import datetime
source=(HERE/'package_raw.py').read_text(encoding='utf-8-sig')
source=source.replace("for prefix in [home,home.replace('\\\\','/')]:\n     count[0]+=obj.count(prefix);obj=obj.replace(prefix,'<USER_HOME>')", "obj,n=re.subn(r'(?i)[a-z]:[\\\\/]+Users[\\\\/]+[^\\\\/:\"<>|\\r\\n]+','<USER_HOME>',obj);count[0]+=n")
source=source.replace('recursively replace current Windows user-home prefix (backslash or slash spelling)', 'recursively replace any Windows drive:/Users/user-component prefix, including case and short-name aliases (backslash or slash spelling)')
(HERE/'package_raw_v2.py').write_text(source,encoding='utf-8',newline='\n')
write(HERE/'PACKAGING_AMENDMENT.json',{'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'v1_failed_closed':True,'observed_failure':'Unredacted user path: connectivity\\0\\thread_request.json','reason':'Exact current-home replacement did not cover all Windows user-home path spellings/aliases; expand only publication-copy path redaction. Original raw scientific outputs and frozen source unchanged.','original_packager_sha256':sha(HERE/'package_raw.py'),'amended_packager':'package_raw_v2.py','amended_packager_sha256':sha(HERE/'package_raw_v2.py'),'formal_plan_sha256':sha(HERE/'formal_plan.json')})
print((HERE/'package_raw_v2.py').read_text().splitlines()[14:18])
