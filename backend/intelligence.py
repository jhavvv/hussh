"""Replaceable prototype classifier, indicator extraction and similarity search.
Synthetic training data is deliberately labelled; this is not a validated fraud model.
"""
import re
from datetime import datetime, timezone
from uuid import uuid4
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

SCAM = [
 'Urgent your account suspended verify password immediately',
 'You won a cash prize pay processing fee to claim reward',
 'Your parcel on hold pay redelivery fee now',
 'Send gift cards to unlock your bank account',
 'Guaranteed crypto investment double your money today',
 'Your tax refund is ready enter your card and security code',
 'Final warning transfer money now to prevent arrest',
 'Verify your identity with your password at this link',
 'Your bank account blocked click here immediately',
 'Congratulations winner claim your lottery prize now',
 'Your delivery failed pay a fee to release the parcel',
 'Send your one time code to secure your account',
 'I am your boss buy gift cards and send the codes',
 'Investment opportunity guaranteed returns pay in bitcoin',
 'Update payment details now or your service is suspended',
 'You have inherited millions send a deposit to release funds',
]
LEGIT = [
 'Hi are we meeting at the library at three today',
 'Your order has shipped view delivery status in your official app',
 'Thanks for dinner yesterday see you next week',
 'The meeting agenda is ready for tomorrow morning',
 'Your appointment is confirmed for Monday at ten',
 'Please bring your notes to the study group',
 'Your monthly statement is available in the banking app',
 'We will never ask for your password or verification code',
 'Class is cancelled today due to weather',
 'Your package was delivered to reception',
 'The invoice you requested is in our usual portal',
 'Lunch at twelve works well for me',
 'The train is delayed by fifteen minutes',
 'Thank you for your feedback we appreciate it',
 'Happy birthday hope you have a lovely day',
 'The library book you reserved is ready to collect',
]
MODEL=make_pipeline(TfidfVectorizer(ngram_range=(1,2),sublinear_tf=True),LogisticRegression(C=6,random_state=42,max_iter=1000))
MODEL.fit(SCAM+LEGIT,[1]*len(SCAM)+[0]*len(LEGIT))
RULES=[(r'urgent|immediately|act now|right now','Pressure to act quickly',22),
       (r'password|one.time|\botp\b|verification code|verify.*account','Sensitive account information requested',30),
       (r'suspend|blocked|on hold','Threat of losing access or a delivery',19),
       (r'gift card|crypto|wire transfer','Unusual payment method',30),
       (r'won|winner|prize|reward|guaranteed return','Unexpected financial promise',22),
       (r'pay|fee|payment','Payment request',14)]

def indicators(text):
    return {'urls':sorted(set(re.findall(r'https?://[^\s<>]+',text,re.I))),
            'emails':sorted(set(re.findall(r'[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}',text,re.I))),
            'phones':sorted(set(re.findall(r'(?:\+?\d[\d ()-]{7,}\d)',text)))}

def redact(text):
    text=re.sub(r'[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}','[email removed]',text,flags=re.I)
    return re.sub(r'(?:\+?\d[\d ()-]{7,}\d)','[number removed]',text)

def analyze(text,reports=()):
    cues=[(desc,weight) for pattern,desc,weight in RULES if re.search(pattern,text,re.I)]
    found=indicators(text)
    probability=float(MODEL.predict_proba([text])[0,1])
    heuristic=min(96,8+sum(w for _,w in cues)+(10 if found['urls'] else 0))
    score=round(.65*heuristic+.35*probability*100)
    words=set(re.findall(r'[a-z]{4,}',text.lower()))
    matches=[]
    for report in reports:
        rw=set(re.findall(r'[a-z]{4,}',report['text'].lower()))
        overlap=len(words&rw)/max(1,len(rw))
        exact=any(u in report['text'] for u in found['urls'])
        if exact or overlap>=.28:
            matches.append({**report,'match_type':'exact URL' if exact else 'text similarity','similarity':round(overlap,2)})
    return {'id':str(uuid4()),'text':text,'risk':'High' if score>=60 else 'Medium' if score>=30 else 'Low',
            'score':score,'ai_score':round(probability*100),'cues':[d for d,_ in cues],
            'indicators':found,'matches':matches,'verification':'Unverified',
            'model':'TF-IDF + logistic regression, synthetic training set; not validated for real-world use',
            'created':datetime.now(timezone.utc).isoformat()}
