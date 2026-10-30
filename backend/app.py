"""FastAPI API: authenticated participation, role-gated verification, atomic audit.
No analysis text or screenshot is stored by the analysis endpoint.
"""
import os, hashlib, secrets, hmac, time, re
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Literal
from uuid import uuid4
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict, field_validator
from sqlalchemy import create_engine, MetaData, Table, Column, String, Text, Boolean, Integer, ForeignKey, select, func, UniqueConstraint
from sqlalchemy.exc import IntegrityError
from intelligence import analyze, redact

DB=os.getenv('DATABASE_URL','sqlite:///scamshield.db')
engine=create_engine(DB,connect_args={'check_same_thread':False} if DB.startswith('sqlite') else {},pool_pre_ping=True)
meta=MetaData()
users=Table('users',meta,Column('id',String,primary_key=True),Column('username',String(40),unique=True,nullable=False),Column('salt',String,nullable=False),Column('password_hash',String,nullable=False),Column('role',String,nullable=False))
sessions=Table('sessions',meta,Column('token_hash',String,primary_key=True),Column('user_id',String,ForeignKey('users.id'),nullable=False),Column('expires',Integer,nullable=False))
reports=Table('reports',meta,Column('id',String,primary_key=True),Column('title',String(100)),Column('text',Text),Column('category',String),Column('risk',String),Column('verification',String,default='Unverified'),Column('flagged',Boolean,default=False),Column('sample',Boolean,default=False),Column('created',String))
receipts=Table('receipts',meta,Column('id',String,primary_key=True),Column('report_id',String,ForeignKey('reports.id')),Column('user_id',String,ForeignKey('users.id')),UniqueConstraint('report_id','user_id'))
comments=Table('comments',meta,Column('id',String,primary_key=True),Column('report_id',String,ForeignKey('reports.id')),Column('user_id',String,ForeignKey('users.id')),Column('text',Text),Column('created',String))
audit=Table('verification_audit',meta,Column('id',String,primary_key=True),Column('report_id',String,ForeignKey('reports.id')),Column('reviewer_id',String,ForeignKey('users.id')),Column('decision',String),Column('reason',Text),Column('created',String))
now=lambda:datetime.now(timezone.utc).isoformat()
def password_hash(password,salt):return hashlib.pbkdf2_hmac('sha256',password.encode(),salt.encode(),600000).hex()
def setup():
    meta.create_all(engine)
    if os.getenv('SEED_DATA','1')=='1':
        fixtures=[('delivery','The “missed delivery” text','Your parcel is on hold. Pay a redelivery fee now at https://parcel-update.example to avoid return.','Delivery'),('bank','An urgent bank security alert','Urgent: your bank account has been suspended. Verify your password at https://bank-secure.example immediately.','Banking'),('prize','A prize you never entered to win','Congratulations! You won a cash prize. Pay the processing fee with a gift card to claim your reward.','Prize')]
        with engine.begin() as c:
            for id,title,text,category in fixtures:
                if not c.execute(select(reports.c.id).where(reports.c.id==id)).first():c.execute(reports.insert().values(id=id,title=title,text=text,category=category,risk='High',verification='Unverified',sample=True,flagged=False,created=now()))
@asynccontextmanager
async def lifespan(app):
    setup()
    yield
app=FastAPI(title='huSSh API',version='0.1.0',lifespan=lifespan)
security=HTTPBearer(auto_error=False)
# Single-instance protection. Use a distributed limiter before scaling workers.
rate_buckets={}
@app.middleware('http')
async def security_headers(request:Request,call_next):
    if request.url.path in ['/api/login','/api/register']:
        key=(request.client.host if request.client else 'unknown',request.url.path)
        bucket=[t for t in rate_buckets.get(key,[]) if time.monotonic()-t<60]
        if len(bucket)>=20:return JSONResponse({'detail':'Too many attempts. Try again in a minute.'},status_code=429)
        rate_buckets[key]=bucket+[time.monotonic()]
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='no-referrer'
    response.headers['Cache-Control']='no-store' if request.url.path.startswith('/api') else 'no-cache'
    return response

def current_user(auth:HTTPAuthorizationCredentials=Depends(security)):
    if not auth:raise HTTPException(401,'Sign in to participate.')
    digest=hashlib.sha256(auth.credentials.encode()).hexdigest()
    with engine.connect() as c:
        user=c.execute(select(users).join(sessions,users.c.id==sessions.c.user_id).where(sessions.c.token_hash==digest,sessions.c.expires>int(time.time()))).mappings().first()
    if not user:raise HTTPException(401,'Your session expired. Please sign in again.')
    return dict(user)
def reviewer(user=Depends(current_user)):
    if user['role']!='reviewer':raise HTTPException(403,'Only an authorised reviewer can verify reports.')
    return user
class StrictModel(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
class Credentials(StrictModel):
    username:str=Field(min_length=3,max_length=40,pattern=r'^[a-zA-Z0-9_.-]+$')
    password:str=Field(min_length=10,max_length=128)
    @field_validator('username')
    @classmethod
    def lower(cls,v):return v.lower()
class Message(StrictModel):text:str=Field(min_length=1,max_length=10000)
class NewReport(Message):
    title:str=Field(min_length=3,max_length=100)
    category:Literal['Delivery','Banking','Prize','Other']='Other'
    redaction_confirmed:Literal[True]
class Comment(StrictModel):text:str=Field(min_length=1,max_length=1000)
class Decision(StrictModel):
    decision:Literal['Verified Scam','Verified Legitimate']
    reason:str=Field(min_length=10,max_length=2000)
def issue_session(c,user):
    token=secrets.token_urlsafe(32)
    c.execute(sessions.insert().values(token_hash=hashlib.sha256(token.encode()).hexdigest(),user_id=user['id'],expires=int(time.time())+86400))
    return {'token':token,'username':user['username'],'role':user['role']}
@app.get('/api/health')
def health():return {'service':'scamshield','version':'0.1.0','classifier':'synthetic-trained prototype'}
@app.post('/api/register')
def register(data:Credentials):
    salt=secrets.token_hex(16);user={'id':str(uuid4()),'username':data.username,'salt':salt,'password_hash':password_hash(data.password,salt),'role':'user'}
    try:
        with engine.begin() as c:
            c.execute(users.insert().values(**user));return issue_session(c,user)
    except IntegrityError:raise HTTPException(409,'That username is already taken.')
@app.post('/api/login')
def login(data:Credentials):
    with engine.begin() as c:
        user=c.execute(select(users).where(users.c.username==data.username)).mappings().first()
        salt=user['salt'] if user else '0'*32
        candidate=password_hash(data.password,salt)
        if not user or not hmac.compare_digest(candidate,user['password_hash']):raise HTTPException(401,'Incorrect username or password.')
        return issue_session(c,user)
@app.post('/api/logout')
def logout(auth:HTTPAuthorizationCredentials=Depends(security),user=Depends(current_user)):
    with engine.begin() as c:c.execute(sessions.delete().where(sessions.c.token_hash==hashlib.sha256(auth.credentials.encode()).hexdigest()))
    return {'ok':True}

def report_dict(c,row,details=False):
    d=dict(row);rid=d['id']
    d['count']=c.execute(select(func.count()).select_from(receipts).where(receipts.c.report_id==rid)).scalar_one()
    last=c.execute(select(audit,users.c.username).join(users,audit.c.reviewer_id==users.c.id).where(audit.c.report_id==rid).order_by(audit.c.created.desc())).mappings().first()
    d['review']={'reviewer':last['username'],'reason':last['reason'],'created':last['created']} if last else None
    if details:d['comments']=[{'text':r.text,'author':r.username,'created':r.created} for r in c.execute(select(comments.c.text,comments.c.created,users.c.username).join(users,comments.c.user_id==users.c.id).where(comments.c.report_id==rid).order_by(comments.c.created))]
    return d

def require_report(c,rid):
    r=c.execute(select(reports).where(reports.c.id==rid)).mappings().first()
    if not r:raise HTTPException(404,'Report not found.')
    return r
@app.get('/api/reports')
def list_reports(q:str='',category:str=''):
    with engine.connect() as c:
        stmt=select(reports).order_by(reports.c.created.desc()).limit(200)
        if q:stmt=stmt.where(reports.c.text.ilike('%'+q[:100]+'%')|reports.c.title.ilike('%'+q[:100]+'%'))
        if category:stmt=stmt.where(reports.c.category==category)
        return [report_dict(c,r) for r in c.execute(stmt).mappings()]
@app.get('/api/reports/{rid}')
def detail(rid:str):
    with engine.connect() as c:return report_dict(c,require_report(c,rid),True)
@app.post('/api/analyse')
def analyse(data:Message):
    started=time.perf_counter()
    try:result=analyze(data.text,list_reports())
    except Exception:raise HTTPException(503,'Analysis is unavailable. No result was produced; please try again.')
    result['duration']=round((time.perf_counter()-started)*1000);return result
@app.post('/api/reports')
def create_report(data:NewReport,user=Depends(current_user)):
    rid=str(uuid4());text=redact(data.text)
    values={'id':rid,'title':redact(data.title),'text':text,'category':data.category,'risk':analyze(text)['risk'],'verification':'Unverified','sample':False,'flagged':False,'created':now()}
    with engine.begin() as c:
        c.execute(reports.insert().values(**values))
        c.execute(receipts.insert().values(id=str(uuid4()),report_id=rid,user_id=user['id']))
        return report_dict(c,values,True)
@app.post('/api/reports/{rid}/received')
def received(rid:str,user=Depends(current_user)):
    try:
        with engine.begin() as c:
            require_report(c,rid)
            c.execute(receipts.insert().values(id=str(uuid4()),report_id=rid,user_id=user['id']))
    except IntegrityError:pass
    return detail(rid)
@app.post('/api/reports/{rid}/comments')
def add_comment(rid:str,data:Comment,user=Depends(current_user)):
    with engine.begin() as c:
        require_report(c,rid)
        c.execute(comments.insert().values(id=str(uuid4()),report_id=rid,user_id=user['id'],text=redact(data.text),created=now()))
    return detail(rid)
@app.post('/api/reports/{rid}/flag')
def flag(rid:str,user=Depends(current_user)):
    with engine.begin() as c:
        require_report(c,rid);c.execute(reports.update().where(reports.c.id==rid).values(flagged=True))
    return {'ok':True}
@app.get('/api/review')
def review_queue(user=Depends(reviewer)):
    with engine.connect() as c:return [report_dict(c,r) for r in c.execute(select(reports).where(reports.c.flagged==True)).mappings()]
@app.post('/api/review/{rid}')
def decide(rid:str,data:Decision,user=Depends(reviewer)):
    with engine.begin() as c:
        require_report(c,rid)
        c.execute(reports.update().where(reports.c.id==rid).values(verification=data.decision,flagged=False))
        c.execute(audit.insert().values(id=str(uuid4()),report_id=rid,reviewer_id=user['id'],decision=data.decision,reason=data.reason,created=now()))
    return detail(rid)
@app.get('/api/review/{rid}/audit')
def audit_log(rid:str,user=Depends(reviewer)):
    with engine.connect() as c:
        require_report(c,rid)
        return [dict(r) for r in c.execute(select(audit).where(audit.c.report_id==rid).order_by(audit.c.created)).mappings()]
web=Path(__file__).resolve().parent.parent/'web'
if web.exists():app.mount('/',StaticFiles(directory=web,html=True),name='web')
