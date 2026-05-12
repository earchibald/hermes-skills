#!/usr/bin/env python3
"""Inter-Agent Communication Test Harness — shared by all 3 agents."""

import argparse, hashlib, hmac, json, os, platform, socket, subprocess, sys, time, urllib.request, urllib.error

PASS, FAIL = "✅", "❌"

def detect_agent():
    hostname = socket.gethostname().lower()
    if platform.system() == "Darwin":
        v = os.path.expanduser("~/work/Agent-Vault")
        if os.path.isdir(v):
            return {"name": "argus", "vault": v, "hermes_home": os.path.expanduser("~/.hermes"),
                    "host": f"{hostname}.local", "host_ip": "192.168.1.104"}
    if "nuc-1" in hostname or hostname.startswith("nuc"):
        hh = os.path.expanduser("~/.hermes")
        if os.path.isdir(hh):
            return {"name": "hermes", "vault": os.path.expanduser("~/obsidian-vaults/Agent-Vault"),
                    "hermes_home": hh, "host": "nuc-1.local", "host_ip": "100.105.253.43"}
    if os.path.isdir("/opt/data"):
        vl = "/opt/data/Loom-Vault"
        return {"name": "loom", "vault": os.path.realpath(vl) if os.path.islink(vl) else vl,
                "hermes_home": "/opt/data", "host": "192.168.1.201", "host_ip": "192.168.1.201"}
    for p in [os.path.expanduser("~/work/Agent-Vault"), os.path.expanduser("~/obsidian-vaults/Agent-Vault")]:
        if os.path.isdir(p):
            return {"name": "unknown", "vault": p, "hermes_home": os.path.expanduser("~/.hermes"),
                    "host": hostname, "host_ip": None}
    return None

class TestSuite:
    def __init__(self, agent):
        self.agent = agent; self.results = []; self.name = agent["name"].title()
    def test(self, label, fn):
        try:
            r = fn(); s = PASS if r else FAIL
        except Exception as e: s = FAIL; label = f"{label}  [{e}]"
        self.results.append((s, label)); return s
    def summary(self):
        p = sum(1 for s,_ in self.results if s==PASS); f = sum(1 for s,_ in self.results if s==FAIL)
        print(f"\n{'='*50}\n  {self.name}: {PASS} {p}  {FAIL} {f}\n{'='*50}"); return f==0

def wexists(p): return p and os.path.exists(p)

def webhook_post(url, secret, ev, sender, msg, timeout=5):
    payload = json.dumps({"event_type": ev, "sender": sender, "message": msg}).encode()
    sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type":"application/json","X-Webhook-Signature":sig})
    try:
        r = urllib.request.urlopen(req, timeout=timeout); return (True, r.read().decode()[:200])
    except urllib.error.HTTPError as e: return (False, f"HTTP {e.code}: {e.read().decode()[:100]}")
    except Exception as e: return (False, str(e))

def run_tests(agent, quick=False):
    s = TestSuite(agent); v = agent["vault"]; hh = agent["hermes_home"]; me = agent["name"]
    ib = os.path.join(v, "Agent-Share")
    ai = {"argus": os.path.join(v,"Argus","inbox"), "hermes": os.path.join(v,"Hermes","inbox"), "loom": os.path.join(v,"Loom","inbox")}
    print(f"\n{'='*50}\n  Inter-Agent Test Harness — {s.name}\n  Vault: {v}\n  Hermes Home: {hh}\n{'='*50}")

    # 1. Infrastructure
    print("\n── 1. Infrastructure ──")
    s.test("Vault root exists", lambda: wexists(v))
    for n,p in [("broadcast",os.path.join(ib,"broadcast")),("pool",os.path.join(ib,"pool")),
                ("Argus/inbox",ai["argus"]),("Hermes/inbox",ai["hermes"]),("Loom/inbox",ai["loom"])]:
        s.test(f"  {n}/ exists", lambda pp=p: wexists(pp))

    # 2. Watchdog Health
    print("\n── 2. Watchdog Health ──")
    wp = os.path.join(hh,"scripts","vault-watchdog.py")
    s.test("Watchdog script exists", lambda: wexists(wp))
    if wexists(wp):
        r = subprocess.run([sys.executable,"-c",f"import py_compile; py_compile.compile('{wp}',doraise=True)"],
                           capture_output=True,text=True,timeout=10)
        s.test("Watchdog script compiles", lambda: r.returncode==0)
    else: s.test("Watchdog script compiles", lambda: False)
    cjp = os.path.join(hh,"cron","jobs.json")
    if wexists(cjp):
        with open(cjp) as f: jobs = json.load(f).get("jobs",[])
        s.test("Watchdog cron job registered", lambda: any("watchdog" in j.get("name","").lower() or "vault" in (j.get("script") or "").lower() for j in jobs))
    else: s.test("Watchdog cron job registered", lambda: False)
    sf = os.path.join(hh,"vault-watchdog-state.json")
    s.test("Watchdog state file exists", lambda: wexists(sf))

    # 3. Webhook Reachability
    print("\n── 3. Webhook Reachability ──")
    # Target URLs must use hardcoded IPs of the target agent, NOT the running agent's own host_ip.
    # Using agent['host_ip'] here would build a URL pointing at the running agent itself.
    wt = {"argus→hermes":{"url":"http://nuc-1.local:8644/webhooks/agent-argus","secret":"wcZgCehug4agX7Mewzr81IhT0zEZUPV15rncoe-LjIg","event":"agent-message"},
          "argus→loom":{"url":"http://192.168.1.201:8644/webhooks/vault-cron","secret":"vaultBridgeSecure2026","event":"vault-update"}}
    if quick: print("  (SKIPPED: --quick)"); wt = {}
    elif me=="hermes":
        # hermes→argus: Hermes tests if it can REACH Argus's webhook. URL must point to Argus (macOS).
        wt["hermes→argus"]={"url":"http://192.168.1.104:8644/webhooks/vault-cron","secret":"vaultBridgeSecure2026","event":"vault-update"}
    elif me=="loom":
        # loom→argus: Loom tests if it can REACH Argus's webhook. URL must point to Argus (macOS).
        wt["loom→argus"]={"url":"http://192.168.1.104:8644/webhooks/vault-cron","secret":"vaultBridgeSecure2026","event":"vault-update"}
    for n,t in wt.items():
        ok,_ = webhook_post(t["url"],t["secret"],t["event"],f"{s.name} (test)","🧪 Test ping")
        s.test(f"  {n} responds", lambda: ok)

    # 4. Vault Write + Detection
    print("\n── 4. Vault Write + Detection ──")
    tid = f"test-{int(time.time())}"; tc = f"# Test — {tid}\n\n> [!INFO] Auto-generated by {s.name} test harness.\n"
    tf = os.path.join(ib,"broadcast",f"{tid}.md")
    try: open(tf,"w").write(tc); s.test("Write test file to broadcast/", lambda: wexists(tf))
    except: s.test("Write test file to broadcast/", lambda: False)
    mi = ai.get(me)
    if mi and wexists(mi):
        mf = os.path.join(mi,f"{tid}.md")
        try: open(mf,"w").write(tc); s.test(f"Write test file to {me}/inbox/", lambda: wexists(mf))
        except: s.test(f"Write test file to {me}/inbox/", lambda: False)

    # 5. State File Integrity
    print("\n── 5. State File Integrity ──")
    if wexists(sf):
        with open(sf) as f: state = json.load(f)
        exp = [f"inbox/{a}" for a in ["argus","hermes","loom"]] + ["broadcast","pool"]
        s.test("State file has all expected sections", lambda: all(sec in state for sec in exp))
        for sec in exp:
            if sec in state: s.test(f"  {sec}: {len(state[sec])} tracked files", lambda: True)
            else: s.test(f"  {sec}: missing", lambda: False)
    else: s.test("State file integrity checks", lambda: False)

    # 6. Self-Reference Fix
    print("\n── 6. Self-Reference Fix ──")
    has_fix = False; srcs = []
    cp = os.path.join(hh,"config.yaml")
    if wexists(cp):
        with open(cp) as f: ct = f.read()
        if any(m in ct.lower() for m in ["first-person","first person","never use your own name"]): has_fix = True; srcs.append("config.yaml")
        if not has_fix:
            for line in ct.split("\n"):
                line=line.strip()
                if line.startswith("personality:"):
                    v=line.split(":",1)[1].strip().strip("'\"")
                    if v: has_fix=True; srcs.append(f"personality '{v}'")
                    break
    skd = os.path.join(hh,"skills")
    if not has_fix and wexists(skd):
        for r,d,fs in os.walk(skd):
            for fn in fs:
                if not fn.endswith(".md"): continue
                with open(os.path.join(r,fn)) as f: c=f.read()
                if "first-person" in c.lower() or "never use your own name" in c.lower():
                    has_fix=True; srcs.append(f"skill '{r.split('/')[-1]}'"); break
            if has_fix: break
    s.test("Self-reference first-person fix applied", lambda: has_fix)
    if has_fix:
        for src in srcs: print(f"    (found in {src})")

    # 7. Webhook Route Registration
    print("\n── 7. Webhook Registrations ──")
    sp = os.path.join(hh,"webhook_subscriptions.json")
    if wexists(sp):
        with open(sp) as f: r = f.read().strip()
        subs = json.loads(r) if r else {}
        s.test("Webhook subscriptions exist", lambda: len(subs)>0)
        for rn in subs: s.test(f"  Route '{rn}' registered", lambda: True)
    else: s.test("Webhook subscriptions exist", lambda: False)

    print("\n── Results ──")
    for st,lb in s.results: print(f"  {st}  {lb}")
    return s.summary()

def cleanup(agent):
    v=agent["vault"]; n=0
    for d in [os.path.join(v,"Agent-Share","broadcast"),os.path.join(v,"Agent-Share","pool"),
              os.path.join(v,"Argus","inbox"),os.path.join(v,"Hermes","inbox"),os.path.join(v,"Loom","inbox")]:
        if not os.path.isdir(d): continue
        for fn in os.listdir(d):
            fp=os.path.join(d,fn)
            if fn.startswith("test-") and fn.endswith(".md") and os.path.isfile(fp): os.remove(fp); n+=1
    print(f"Cleaned up {n} test file(s)."); return n

def main():
    p=argparse.ArgumentParser(); p.add_argument("--quick",action="store_true"); p.add_argument("--cleanup",action="store_true")
    a=p.parse_args(); agent=detect_agent()
    if not agent: print(f"{FAIL} Could not detect agent environment."); sys.exit(1)
    print(f"Detected agent: {agent['name']}")
    if a.cleanup: cleanup(agent); return
    sys.exit(0 if run_tests(agent,quick=a.quick) else 1)

if __name__=="__main__": main()
