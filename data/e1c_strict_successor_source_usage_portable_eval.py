import ast, json, os
w=json.loads(os.environ["WITNESS_JSON"])
symbol=str(w["symbol"]); candidate=str(w["candidate_path"]).replace("\\","/")
calls=[]; regs=[]; defs=[]
for root,dirs,files in os.walk("/testbed"):
    dirs[:]=[d for d in dirs if d.lower() not in ("test","tests","testing") and d!=".git"]
    for fn in files:
        if not fn.endswith(".py"): continue
        path=os.path.join(root,fn); rel=os.path.relpath(path,"/testbed").replace("\\","/")
        try:
            source=open(path,"r").read(); tree=ast.parse(source)
        except Exception: continue
        for node in ast.walk(tree):
            if isinstance(node,(ast.FunctionDef,ast.ClassDef)) and node.name==symbol: defs.append({"path":rel,"line":getattr(node,"lineno",None)})
            if isinstance(node,ast.Call):
                func=node.func; called=func.id if isinstance(func,ast.Name) else (func.attr if isinstance(func,ast.Attribute) else None)
                if called==symbol: calls.append({"path":rel,"line":getattr(node,"lineno",None)})
                for arg in list(node.args)+[kw.value for kw in node.keywords]:
                    if isinstance(arg,ast.Name) and arg.id==symbol: regs.append({"path":rel,"line":getattr(node,"lineno",None)})
extcalls=[x for x in calls if x["path"]!=candidate]; extregs=[x for x in regs if x["path"]!=candidate]
value={"schema":"e1c-strict-v8-source-usage-result-v1","symbol":symbol,"candidate_path":candidate,"predicate":w.get("predicate"),"definition_count":len(defs),"external_call_count":len(extcalls),"external_registration_count":len(extregs),"passed":bool(extcalls or extregs),"sample_calls":extcalls[:8],"sample_registrations":extregs[:8]}
import hashlib
value["result_sha256"]=hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":" )).encode()).hexdigest()
print(json.dumps(value,sort_keys=True))
