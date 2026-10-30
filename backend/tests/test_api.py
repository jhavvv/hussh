import os, tempfile, sys
from pathlib import Path
os.environ['DATABASE_URL']='sqlite:///'+str(Path(tempfile.mkdtemp())/'test.db')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select,func
from app import app,engine,meta,users,reports,audit,comments,sessions,receipts
from intelligence import analyze,indicators,redact

@pytest.fixture()
def client():
    meta.drop_all(engine)
    with TestClient(app) as c:yield c

def account(c,name='member',role='user'):
    r=c.post('/api/register',json={'username':name,'password':'test-only-password-4321'})
    assert r.status_code==200,r.text
    if role=='reviewer':
        with engine.begin() as db:db.execute(users.update().where(users.c.username==name).values(role='reviewer'))
    return {'Authorization':'Bearer '+r.json()['token']}

def test_text_and_explanation(client):
    r=client.post('/api/analyse',json={'text':'Urgent bank account suspended verify password immediately https://bank-secure.example'})
    assert r.status_code==200
    d=r.json();assert d['risk']=='High' and d['verification']=='Unverified'
    assert d['cues'] and d['matches'] and 'model' in d and 'indicators' in d

def test_empty_and_long_input(client):
    for text in ['', '   ', 'a'*10001]:assert client.post('/api/analyse',json={'text':text}).status_code==422

def test_indicators():
    d=indicators('Visit https://example.test email me@sample.test call +1 312 555 0101')
    assert len(d['urls'])==len(d['emails'])==len(d['phones'])==1

def test_no_match_is_not_verified():
    r=analyze('Completely novel instructions with no known match',[])
    assert r['matches']==[] and r['verification']=='Unverified'

def test_redaction():
    s=redact('Contact me@sample.test at +1 312 555 0101')
    assert 'me@sample.test' not in s and '312' not in s

def test_authenticated_report(client):
    h=account(client)
    payload={'title':'Suspicious test','text':'Send money to me@sample.test','category':'Other','redaction_confirmed':True}
    assert client.post('/api/reports',json=payload).status_code==401
    r=client.post('/api/reports',headers=h,json=payload).json()
    assert r['count']==1 and r['verification']=='Unverified' and 'me@sample.test' not in r['text']

def test_confirmation_and_role_injection(client):
    h=account(client)
    p={'title':'Test report','text':'Fake notice','category':'Other','redaction_confirmed':False}
    assert client.post('/api/reports',headers=h,json=p).status_code==422
    assert client.post('/api/register',json={'username':'bad','password':'testpassword','role':'reviewer'}).status_code==422

def test_unique_counts_and_no_vote_verification(client):
    h=account(client)
    for _ in range(3):d=client.post('/api/reports/bank/received',headers=h).json()
    assert d['count']==1 and d['verification']=='Unverified'

def test_comments_attached_and_redacted(client):
    h=account(client)
    d=client.post('/api/reports/bank/comments',headers=h,json={'text':'I got it too. test@sample.test'}).json()
    assert len(d['comments'])==1 and 'test@sample.test' not in d['comments'][0]['text']
    assert client.get('/api/reports/prize').json()['comments']==[]

def test_admin_access_and_audit(client):
    user=account(client)
    decision={'decision':'Verified Scam','reason':'Reviewed the synthetic fixture and supporting evidence.'}
    assert client.post('/api/review/bank',headers=user,json=decision).status_code==403
    assert client.post('/api/review/bank',json=decision).status_code==401
    reviewer=account(client,'reviewer','reviewer')
    client.post('/api/reports/bank/flag',headers=user)
    assert len(client.get('/api/review',headers=reviewer).json())==1
    d=client.post('/api/review/bank',headers=reviewer,json=decision).json()
    assert d['verification']=='Verified Scam' and d['review']['reviewer']=='reviewer'
    logs=client.get('/api/review/bank/audit',headers=reviewer).json()
    assert len(logs)==1 and logs[0]['reason']==decision['reason']
    assert client.get('/api/review',headers=reviewer).json()==[]

def test_votes_cannot_change_trusted_decision(client):
    h=account(client,'reviewer','reviewer')
    client.post('/api/review/bank',headers=h,json={'decision':'Verified Legitimate','reason':'Synthetic test of evidence precedence.'})
    u=account(client,'member')
    d=client.post('/api/reports/bank/received',headers=u).json()
    assert d['verification']=='Verified Legitimate'

def test_analysis_does_not_inherit_matching_verification(client):
    h=account(client,'reviewer','reviewer')
    client.post('/api/review/bank',headers=h,json={'decision':'Verified Scam','reason':'Verified synthetic fixture for testing.'})
    r=client.post('/api/analyse',json={'text':'Urgent verify password at https://bank-secure.example'}).json()
    assert r['verification']=='Unverified'
    assert r['matches'][0]['verification']=='Verified Scam'

def test_no_retention(client):
    text='unique-private-message-4215'
    client.post('/api/analyse',json={'text':text})
    with engine.connect() as c:
        assert c.execute(select(func.count()).select_from(reports).where(reports.c.text==text)).scalar()==0
        assert set(meta.tables)=={'users','sessions','reports','receipts','comments','verification_audit'}

def test_failed_classifier(client,monkeypatch):
    import app as module
    def fail(*a,**k):raise RuntimeError('service unavailable')
    monkeypatch.setattr(module,'analyze',fail)
    r=client.post('/api/analyse',json={'text':'Hello'})
    assert r.status_code==503 and 'No result' in r.json()['detail']

def test_missing_report(client):
    h=account(client)
    assert client.post('/api/reports/missing/received',headers=h).status_code==404

def test_logout_revokes_session(client):
    h=account(client)
    assert client.post('/api/logout',headers=h).status_code==200
    assert client.post('/api/reports/bank/received',headers=h).status_code==401
