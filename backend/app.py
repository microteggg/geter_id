import asyncio
import base64
import copy
import json
import logging
import os
import re
import secrets
import shutil
import time
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

VERSION = "1.0.0"
ROOT = Path(__file__).resolve().parent.parent
BINARY = os.getenv("IDX_BINARY", "idx")
TIMEOUT = int(os.getenv("COMMAND_TIMEOUT", "120"))
MAX_CACHE = 256
SEM = asyncio.Semaphore(2)
CACHE = OrderedDict()
PENDING = {}
RATE = OrderedDict()
OWNER_LOCK = asyncio.Lock()
OWNER_IMPORTED = 0.0
USER = os.getenv("APP_USER", "")
PASSWORD = os.getenv("APP_PASSWORD", "")
if bool(USER) != bool(PASSWORD):
    raise RuntimeError("APP_USER dan APP_PASSWORD harus diisi keduanya atau dikosongkan keduanya.")
log = logging.getLogger("geter")
app = FastAPI(title="GETER IDX", version=VERSION, docs_url=None, redoc_url=None, openapi_url=None)

@app.middleware("http")
async def security(request: Request, call_next):
    path = request.url.path
    if path != "/api/health" and USER:
        raw = request.headers.get("authorization", "")
        valid = False
        if raw.startswith("Basic "):
            try:
                u, pw = base64.b64decode(raw[6:], validate=True).decode().split(":", 1)
                valid = secrets.compare_digest(u.encode(), USER.encode()) & secrets.compare_digest(pw.encode(), PASSWORD.encode())
            except (ValueError, UnicodeError):
                pass
        if not valid:
            return JSONResponse({"detail":"Login diperlukan."},401,headers={"WWW-Authenticate":'Basic realm="GETER IDX"'})
    if path.startswith("/api/") and path != "/api/health":
        # Tidak mempercayai X-Forwarded-For dari browser. Batas ini dapat berlaku bersama di belakang proxy.
        ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        start, count = RATE.get(ip, (now, 0))
        if now - start >= 60:
            start, count = now, 0
        if count >= 90:
            return JSONResponse({"detail":"Terlalu banyak permintaan. Tunggu satu menit."},429,headers={"Retry-After":"60"})
        RATE[ip] = (start, count+1)
        RATE.move_to_end(ip)
        while len(RATE)>1024:
            RATE.popitem(last=False)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'"
    if path.startswith('/api/'):
        response.headers['Cache-Control']='no-store'
    return response

class EngineError(Exception):
    pass

async def run(args, timeout=TIMEOUT):
    async with SEM:
        try:
            proc = await asyncio.create_subprocess_exec(BINARY, "-o", "json", "--timeout", "20", *args,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        except OSError as exc:
            raise EngineError("IDX engine tidak dapat dijalankan. Periksa log build server.") from exc
        try:
            out, err = await asyncio.wait_for(proc.communicate(), timeout)
        except (asyncio.TimeoutError, asyncio.CancelledError) as exc:
            if proc.returncode is None:
                try: proc.kill()
                except ProcessLookupError: pass
            await proc.communicate()
            if isinstance(exc, asyncio.CancelledError): raise
            raise EngineError("Provider terlalu lama merespons. Coba kembali beberapa saat lagi.") from exc
        if proc.returncode:
            log.warning("idx gagal (%s): %s",proc.returncode,err.decode(errors="replace")[-2000:])
            raise EngineError(f"IDX/provider gagal (kode {proc.returncode}). Periksa log server untuk detail.")
        try:
            value=json.loads(out)
        except (ValueError, UnicodeError) as exc:
            raise EngineError("Format respons engine tidak valid.") from exc
        if isinstance(value,dict) and (value.get('ok') is False or value.get('error')):
            raise EngineError("Engine mengembalikan error provider.")
        return value

async def refresh(key,args,ttl):
    try:
        value=await run(args)
        CACHE[key]=(time.monotonic(), datetime.now(timezone.utc).isoformat(), value)
        CACHE.move_to_end(key)
        while len(CACHE)>MAX_CACHE: CACHE.popitem(last=False)
        return value
    finally:
        PENDING.pop(key,None)

async def cached(args,ttl=300):
    key=tuple(args)
    old=CACHE.get(key)
    now=time.monotonic()
    hit=bool(old and now-old[0]<ttl)
    stale=False
    warning=None
    if hit:
        value=old[2]
    else:
        if key not in PENDING:
            if len(PENDING)>=24:
                raise HTTPException(503,"Antrean penuh. Coba lagi nanti.")
            PENDING[key]=asyncio.create_task(refresh(key,args,ttl))
        try:
            value=await asyncio.shield(PENDING[key])
        except EngineError as exc:
            if not old or now-old[0]>86400:
                raise HTTPException(503,str(exc)) from exc
            value=old[2];stale=True;warning=str(exc)
    stamp=CACHE.get(key,old)
    meta={"server_cached":hit,"server_stale":stale,"server_fetched_at":stamp[1] if stamp else None,
          "warning":warning,"mode":"Data provider standar; bukan jaminan realtime."}
    if isinstance(value,dict):
        meta['source']={k:value[k] for k in ('provider','fetched_at','cached','stale','warnings','meta') if k in value}
    return {"data":copy.deepcopy(value.get('data',value) if isinstance(value,dict) else value),"meta":meta}

def symbol(value):
    s=value.strip().upper().removesuffix('.JK')
    if not re.fullmatch(r'[A-Z0-9]{2,12}',s): raise HTTPException(422,"Kode saham tidak valid.")
    return s

@app.get('/api/health')
async def health():
    return {"status":"ok","version":VERSION,"engine_installed":bool(shutil.which(BINARY)),"authentication":bool(USER)}

@app.get('/api/market')
async def market(): return await cached(['market','overview','--top','10'],120)

@app.get('/api/market-foreign')
async def market_foreign(): return await cached(['market','foreign','--top','10'],900)

@app.get('/api/stock/{code}/{section}')
async def stock(code:str,section:str,period:str='6mo',interval:str='1d'):
    s=symbol(code)
    if section=='history':
        if period not in {'1mo','3mo','6mo','1y','2y','5y'} or interval not in {'1d','1wk','1mo'}:
            raise HTTPException(422,'Rentang atau interval tidak didukung.')
        return await cached(['stocks','history',s,'--period',period,'--interval',interval,'--limit','500'],300)
    routes={
      'quote':(['stocks','quote',s],90),
      'technical':(['stocks','technical',s,'--period','1y'],600),
      'fundamental':(['stocks','fundamental',s],21600),
      'foreign':(['stocks','foreign',s,'--days','20'],900),
      'broker':(['broker',s],900),
      'bandar':(['bandar','detect',s,'--period','1m','--top','3'],900),
      'news':(['stocks','news',s],900),
      'actions':(['stocks','actions',s],3600),
    }
    if section=='ownership':
        if os.getenv('ENABLE_OWNERSHIP','false').lower()!='true':
            raise HTTPException(503,'Ownership belum diaktifkan. Set ENABLE_OWNERSHIP=true di server; impor register dapat memerlukan waktu dan memori tambahan.')
        global OWNER_IMPORTED
        async with OWNER_LOCK:
            if not OWNER_IMPORTED or time.monotonic()-OWNER_IMPORTED>86400:
                try: await run(['ownership','import','--latest'],240)
                except EngineError as exc: raise HTTPException(503,str(exc)) from exc
                OWNER_IMPORTED=time.monotonic()
        return await cached(['ownership','ticker',s],86400)
    if section not in routes: raise HTTPException(404,'Bagian tidak ditemukan.')
    args,ttl=routes[section]
    return await cached(args,ttl)

@app.get('/api/screen')
async def screen(preset:str='value'):
    routes={
      'value':['stocks','screen','-f','pe<15,roe>15'],
      'accumulation':['bandar','screen','--preset','accumulation','--scan','20'],
      'big-accumulation':['bandar','screen','--preset','big-accumulation','--scan','20'],
      'distribution':['bandar','screen','--preset','distribution','--scan','20'],
      'foreign-accumulation':['bandar','screen','--preset','foreign-accumulation','--scan','20'],
    }
    if preset not in routes: raise HTTPException(422,'Preset tidak didukung.')
    return await cached(routes[preset],900)

# Kompatibilitas endpoint tahap sebelumnya.
@app.get('/api/quote/{code}')
async def legacy_quote(code:str): return await stock(code,'quote')
@app.get('/api/history/{code}')
async def legacy_history(code:str,period:str='6mo',interval:str='1d'): return await stock(code,'history',period,interval)
@app.get('/api/technical/{code}')
async def legacy_technical(code:str): return await stock(code,'technical')

@app.get('/api/{path:path}')
async def unknown_api(path:str): raise HTTPException(404,'Endpoint tidak ditemukan.')

app.mount('/',StaticFiles(directory=ROOT/'frontend',html=True),name='frontend')
