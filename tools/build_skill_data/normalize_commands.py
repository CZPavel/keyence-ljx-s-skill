"""Narrow, reproducible recovery of direct LJ-X8000 command blocks.

The FAST-PASS corpus is not re-extracted.  This tool verifies the registered
source PDF and captures only authoritative command/network pages that contain
tables or diagrams lost by normal text extraction.
"""
from __future__ import annotations
import hashlib, json
from pathlib import Path
import fitz

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "skill_data"
PDF = ROOT / "Downloads" / "AS_166309_LJ-X8000_UM_N04GB_WW_GB_2036_1.pdf"
DOC = "KEYENCE-E3E51B234B56"
SHA = "e3e51b234b56ea11182e78b39574678f5c7244c65d6455664927f580dd1a47c3"

# physical PDF page, printed manual page, type, visually inspected, supported fields
BLOCKS = {
 "network": (202,"8-2","network_setting",False,["port 8500","CR/CR+LF/All delimiter"]),
 "a": (226,"9-4","command_syntax",True,["T1","R0"]),
 "b": (227,"9-5","command_syntax",True,["S0","RS","RB"]),
 "c": (228,"9-6","command_syntax",True,["SS","CE","RM"]),
 "program": (229,"9-7","command_syntax",True,["PW,d,nnn","PR,d,nnn"]),
 "pfr": (230,"9-8","response_format",True,["PFR,h","PFR,n,pppp,...","profile format"]),
 "pfrf": (231,"9-9","response_format",True,["PFRF,h","PFRF,h,t","PFRF,h,s,m","PFRF,n,pppp,..."]),
 "measurement": (232,"9-10","command_syntax",True,["BS","EXW"]),
 "judgment": (233,"9-11","command_syntax",True,["EXR","DW"]),
 "judgment_read": (234,"9-12","command_syntax",True,["DR"]),
 "auto_zero": (235,"9-13","command_syntax",True,["ZR,m,n","ZR,m,n,t,nnn,..."]),
 "measurement_reset": (236,"9-14","command_syntax",True,["MRS,n","MRS,n,t,nnn,..."]),
 "io": (237,"9-15","command_syntax",True,["TE,n","OE,n"]),
 "string": (239,"9-17","command_syntax",True,["STR,n","STR,ssss"]),
}

def hash_file(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
 return h.hexdigest()

def capture():
 if not PDF.exists(): raise FileNotFoundError(PDF)
 if hash_file(PDF)!=SHA: raise RuntimeError("registered source SHA mismatch")
 d=fitz.open(PDF); dst=OUT/"evidence"/"manual_source_blocks"; dst.mkdir(parents=True,exist_ok=True); got={}
 for name,(page,printed,kind,visual,fields) in BLOCKS.items():
  if not 1<=page<=len(d): raise RuntimeError(f"page {page} outside source PDF")
  text=d[page-1].get_text("text"); bid=f"MSB-LJX8000-{page:03d}-{name.upper()}"
  rec={"block_id":bid,"document_id":DOC,"source_sha256":SHA,"pdf_page_index":page,"printed_page":printed,"bbox":None,"block_type":kind,"native_text_sha256":hashlib.sha256(text.encode()).hexdigest(),"visual_verification":visual,"evidence_status":"DIRECT_VISUAL" if visual else "DIRECT_NATIVE","fields_supported":fields}
  (dst/f"{bid}.json").write_text(json.dumps(rec,ensure_ascii=False,indent=2)+"\n",encoding="utf8");got[name]=rec
 return got

def ev(b):
 return {"evidence_quality":b["evidence_status"],"block_id":b["block_id"],"document_id":DOC,"source_sha256":SHA,"pdf_page_index":b["pdf_page_index"],"printed_page":b["printed_page"],"evidence_excerpt_hash":b["native_text_sha256"]}
def exact(value,b): return {"value":value,"status":"OFFICIAL_EXACT","evidence":[ev(b)]}
def param(name,meaning,b): return {"name":name,"meaning":exact(meaning,b)}

def record(cmd,b,purpose,request,response,parameters=(),notes=(),error=None):
 return {"command_id":f"CMD-{cmd}","command":cmd,"controller_family":"LJ-X8000","communication":{"method":"Ethernet Non-Procedural","transport":"Ethernet","direction":"client to controller"},"purpose":exact(purpose,b),"request":{"syntax":exact(request,b),"terminator":exact("configured delimiter",B["network"])},"parameters":list(parameters),"response":{"normal_syntax":exact(response,b) if response else {"value":None,"status":"UNRESOLVED","evidence":[]},"error_behavior":exact(error,b) if error else {"value":None,"status":"UNRESOLVED","evidence":[]}},"requirements":[],"effects":list(notes),"related_commands":[],"related_signals":[],"related_data_flows":[],"knowledge_status":"OFFICIAL_EXACT" if response else "PARTIALLY_EXACT","direct_evidence":[ev(b)],"supporting_evidence":[]}

def overrides(blocks):
 global B; B=blocks; e="ER,**,nn; ** is received command and nn is 2-digit error code"
 data={}
 for cmd,purpose,req,resp,key,err in [
  ("T1","issue a trigger","T1","T1","a","03 when triggers cannot be accepted or trigger input is disabled"),("R0","switch controller to Run mode","R0","R0","a",None),("S0","switch controller to Setup mode","S0","S0","b",None),("RS","reset controller data and buffers","RS","RS","b",None),("RB","save current program settings and reboot","RB","RB","b",None),("SS","save current program and global settings","SS","SS","c",None),("CE","clear error status","CE","CE","c",None)]: data[cmd]=record(cmd,B[key],purpose,req,resp,error=err)
 data["RM"]=record("RM",B["c"],"read Run/Setup controller mode","RM","RM,n",[param("n","0: Setup mode; 1: Run mode",B["c"])])
 data["PW"]=record("PW",B["program"],"load specified inspection program from SD card","PW,d,nnn","PW",[param("d","SD card number: 1=SD1, 2=SD2",B["program"]),param("nnn","program number 0 to 999",B["program"])],["Any setting changes are discarded; global setting file is saved after success."],e)
 data["PR"]=record("PR",B["program"],"read SD card and inspection program currently being read","PR","PR,d,nnn",[param("d","SD card number: 1=SD1, 2=SD2",B["program"]),param("nnn","program number 0 to 999",B["program"])])
 data["CTD"]=record("CTD",B["pfr"],"set delay between trigger input and image capture","CTD,1,nnn","CTD",[param("nnn","trigger delay 0 to 999 ms",B["pfr"])])
 pp=[param("h","acquisition target: 1=Head A or Wide; 2=Head B",B["pfr"]),param("n","maximum number of acquired profile points",B["pfr"]),param("pppp","ASCII actual-size profile values separated by comma",B["pfr"])]
 data["PFR"]=record("PFR",B["pfr"],"obtain latest measured profile","PFR,h","PFR,n,pppp,pppp,pppp,...",pp,["Each profile value: up to 11 characters; sign, integer, decimal point and decimal value. Zero suppression for integers; four decimal places.","Invalid profile data: -99999.9999.","Number-specified commands cannot be used.","Obtained after measurement processing finishes."],e)
 pf=[param("h","acquisition target: 1=Head A or Wide; 2=Head B",B["pfrf"]),param("t","decimation rate: 1=1/2, 2=1/4, 3=1/8",B["pfrf"]),param("s","start position; left end is 0",B["pfrf"]),param("m","data score to acquire, 1 to 6400; excess uses maximum obtainable points",B["pfrf"]),param("n","maximum number of acquired profile points",B["pfrf"]),param("pppp","ASCII actual-size profile values separated by comma",B["pfrf"])]
 data["PFRF"]=record("PFRF",B["pfrf"],"obtain latest measured profile with fast response","PFRF,h | PFRF,h,t | PFRF,h,s,m","PFRF,n,pppp,pppp,pppp,...",pf,["With Continuous Trigger, set trigger frequency to 500 Hz or lower to prevent background-buffer overflow.","Invalid profile data: -99999.9999.","Number-specified commands cannot be used.","Execution stops current measurement temporarily."],e)
 data["TE"]=record("TE",B["io"],"enable or disable trigger input","TE,n","TE",[param("n","0=trigger input disabled; 1=permit trigger input",B["io"])],["TE,0 keeps READY off and turns laser off."])
 data["OE"]=record("OE",B["io"],"enable or disable output","OE,n","OE",[param("n","0=output disabled; 1=permit output",B["io"])])
 data["STR"]=record("STR",B["string"],"read externally specified string","STR,n","STR,ssss",[param("n","0 to 9 for externally specified string; 1000 for screen capture",B["string"]),param("ssss","read string, 0 to 64 characters",B["string"])])
 data["BS"]=record("BS",B["measurement"],"save latest input profile as the specified master profile","BS,h,nnn","BS",[param("h","head number 1 to 2",B["measurement"]),param("nnn","master profile number: Head A 0 to 199; Head B 500 to 699",B["measurement"])])
 data["EXW"]=record("EXW",B["measurement"],"change currently enabled execute condition number","EXW,n","EXW",[param("n","execute condition number 0 to 99",B["measurement"])])
 data["EXR"]=record("EXR",B["judgment"],"read currently enabled execute condition number","EXR","EXR,n",[param("n","execute number 0 to 99",B["judgment"])])
 data["DW"]=record("DW",B["judgment"],"change upper or lower judgment limit for specified tool","DW,nnn,k,b,mmm","DW",[param("nnn","tool number",B["judgment"]),param("k","measurement item number in tool",B["judgment"]),param("b","0=upper limit; 1=lower limit",B["judgment"]),param("mmm","judgment condition value",B["judgment"])])
 data["DR"]=record("DR",B["judgment_read"],"read upper or lower judgment limit for specified tool","DR,nnn,k,b","DR,mmm",[param("nnn","tool number",B["judgment_read"]),param("k","measurement item number in tool",B["judgment_read"]),param("b","0=upper limit; 1=lower limit",B["judgment_read"]),param("mmm","returned judgment condition value",B["judgment_read"])])
 data["TIM"]=record("TIM",B["judgment_read"],"issue a TIMING request","TIM,m,n | TIM,m,n,t,nnn,...","TIM",[param("m","0=Timing OFF; 1=Timing ON",B["judgment_read"])])
 data["ZR"]=record("ZR",B["auto_zero"],"perform auto zero ON or OFF request","ZR,m,n | ZR,m,n,t,nnn,...","ZR",[param("m","0=Auto zero OFF; 1=Auto zero ON",B["auto_zero"])])
 data["MRS"]=record("MRS",B["measurement_reset"],"request measured value reset","MRS,n | MRS,n,t,nnn,...","MRS")
 return data

def write_transport():
 n=B["network"]; x={"method":"Ethernet Non-Procedural","controller_family":"LJ-X8000","transport":"Ethernet","port":exact(8500,n),"delimiter":exact("CR (default), CR+LF, or All; All permits per-function command/result delimiters",n),"command_response":{"value":"commands and result output use configured delimiter","status":"OFFICIAL_EXACT","evidence":[ev(n)]},"async_output":{"value":"result output is configured separately in Ethernet (Non-Procedural) Output Settings","status":"OFFICIAL_EXACT","evidence":[ev(n)]},"source_evidence":[ev(n)]}
 (OUT/"communication"/"ethernet_nonprocedural.yaml").write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 # Matrix stays an index; detailed facts have one canonical home above.
 mp=OUT/"communication"/"communication_matrix.yaml"
 matrix=json.loads(mp.read_text(encoding="utf8"))
 methods=matrix.setdefault("methods",[])
 item=next((m for m in methods if m.get("method")=="Ethernet Non-Procedural"),None)
 if item is None:
  methods.append({"method_id":"COM-ETHERNET-NON-PROCEDURAL","method":"Ethernet Non-Procedural","controller_applicability":"LJ-X8000","canonical_detail_reference":"communication/ethernet_nonprocedural.yaml","knowledge_status":"OFFICIAL_EXACT","source_evidence":[ev(n)]})
 else:
  item.update({"canonical_detail_reference":"communication/ethernet_nonprocedural.yaml","knowledge_status":"OFFICIAL_EXACT","source_evidence":[ev(n)]})
 mp.write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+"\n",encoding="utf8")

def views(commands):
 rows=["# Command reference","","| Command | Family | Purpose | Request | Response | Status |","|---|---|---|---|---|---|"]
 for x in commands:
  p=x.get("purpose");p=p.get("value") if isinstance(p,dict) else p;r=x.get("request",{}).get("syntax");r=r.get("value") if isinstance(r,dict) else r;s=x.get("response",{}).get("normal_syntax");s=s.get("value") if isinstance(s,dict) else s
  rows.append(f"| {x['command']} | {x.get('controller_family')} | {p or ''} | {r or ''} | {s or ''} | {x.get('knowledge_status')} |")
 (OUT/"operations"/"COMMAND_REFERENCE.md").write_text("\n".join(rows)+"\n",encoding="utf8")
 ex=sum(x.get("knowledge_status")=="OFFICIAL_EXACT" for x in commands);pa=sum(x.get("knowledge_status")=="PARTIALLY_EXACT" for x in commands);co=sum(x.get("knowledge_status")=="OFFICIAL_CONTEXTUAL" for x in commands)
 req=sum(isinstance(x.get("request",{}).get("syntax"),dict) and x["request"]["syntax"].get("status")=="OFFICIAL_EXACT" for x in commands)
 rsp=sum(isinstance(x.get("response",{}).get("normal_syntax"),dict) and x["response"]["normal_syntax"].get("status")=="OFFICIAL_EXACT" for x in commands)
 par=sum(bool(x.get("parameters")) and all(isinstance(p.get("meaning"),dict) and p["meaning"].get("status")=="OFFICIAL_EXACT" for p in x["parameters"]) for x in commands)
 (OUT/"COMMAND_COVERAGE.md").write_text(f"# Command coverage\n\nDiscovered: {len(commands)}. OFFICIAL_EXACT: {ex}. PARTIALLY_EXACT: {pa}. OFFICIAL_CONTEXTUAL: {co}.\n\nExact request syntax: {req}. Exact response syntax: {rsp}. Commands with exact parameter definitions: {par}.\n\nExact Ethernet Non-Procedural port: 8500. Exact delimiter settings: CR (default), CR+LF, All. Direct source blocks are in `evidence/manual_source_blocks`.\n",encoding="utf8")

def main():
 global B;B=capture();o=overrides(B);p=OUT/"operations"/"command_reference.yaml";data=json.loads(p.read_text(encoding="utf8"));by={x["command"]:x for x in data["commands"]};by.update(o);data["schema_version"]=2;data["commands"]=[by[k] for k in sorted(by)];p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 idx=[{"command":x["command"],"aliases":[x["command"].lower()],"controller_family":x.get("controller_family"),"status":x.get("knowledge_status")} for x in data["commands"]];(OUT/"routing"/"command_index.json").write_text(json.dumps(idx,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 q=[{"command":x["command"],"missing_field":"syntax/parameters/response","reason":"SOURCE_NOT_FOUND","recommended_next_source":"inspect original PDF command page or another family-specific manual"} for x in data["commands"] if x.get("knowledge_status")=="OFFICIAL_CONTEXTUAL"];(OUT/"unresolved"/"command_review_queue.yaml").write_text(json.dumps({"queue":q},ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 # Keep the shared index append-only, but do not duplicate a prior run.
 ep=OUT/"evidence"/"evidence_index.jsonl"; existing=set()
 if ep.exists():
  existing={json.loads(line).get("record_id") for line in ep.read_text(encoding="utf8").splitlines() if line.strip()}
 with ep.open("a",encoding="utf8") as f:
  for block in B.values():
   rid=block["block_id"]
   if rid not in existing:
    f.write(json.dumps({"record_id":rid,"knowledge_file":"evidence/manual_source_blocks","knowledge_key":rid,"document_id":DOC,"page":block["pdf_page_index"],"printed_page":block["printed_page"],"source_sha":SHA,"evidence_excerpt_hash":block["native_text_sha256"],"evidence_status":block["evidence_status"]},ensure_ascii=False)+"\n")
 write_transport();views(data["commands"]);print(json.dumps({"captured_source_blocks":len(B),"direct_commands":len(o),"total_commands":len(data["commands"])}))
if __name__=="__main__": main()


