"""Replaceable prototype classifier, indicator extraction and similarity search.
Synthetic training data is deliberately labelled; this is not a validated fraud model.
"""
import re
from urllib.parse import urlsplit
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
 'NZ Post your address is incomplete open the link and update delivery details',
 'DHL package cannot be delivered confirm home address using this website',
 'FedEx final notice parcel held click tracking link to release',
 'IRD tax refund available provide account details on the linked page',
 'This is your bank fraud team move your savings to a safe account now',
 'You have been selected for a remote job pay a registration fee first',
 'Complete online tasks and deposit money to withdraw your earnings',
 'Your Microsoft account has been locked confirm password through this link',
 'Do not tell anyone this one time login code send it to me',
 'Mum this is my new number please send money for an emergency',
 'I am your manager purchase vouchers and send me the gift card PINs',
 'Your parcel requires a customs fee before it can be released',
 'Final warning pay your infringement fine using the link below',
 'Your account will close today unless you verify identity on this site',
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
 'NZ Post has delivered your parcel to the mailbox thank you',
 'Your DHL delivery is expected tomorrow check its progress in your official app',
 'Your FedEx parcel is ready for collection at the depot',
 'IRD has sent an update to your myIR inbox sign in using the official website',
 'Thank you for applying for the job we will contact shortlisted applicants',
 'Your application was received no payment is required',
 'We will never ask for your one time code or password by text',
 'A login alert was sent to your account no action is needed if it was you',
 'Your banking app has a new statement ready',
 'Please confirm that you can attend the interview on Friday',
 'The parcel address you entered at checkout is incomplete contact our support through the store',
 'NZ Post says to check tracking directly in their app instead of opening links in texts',
]
MODEL=make_pipeline(TfidfVectorizer(ngram_range=(1,2),sublinear_tf=True),LogisticRegression(C=6,random_state=42,max_iter=1000))
MODEL.fit(SCAM+LEGIT,[1]*len(SCAM)+[0]*len(LEGIT))
# Signals are evidence, not verification. Require context for sensitive categories.
RULES = [
    (r'\b(?:urgent|immediately|act now|right now|final warning|within \d+ hours?)\b', 'Pressure to act quickly', 18),
    (r'\b(?:suspend(?:ed)?|blocked|on hold|locked|cannot be delivered|failed delivery)\b', 'Threat of losing access or a delivery', 16),
    (r'\b(?:gift cards?|bitcoin|crypto|wire transfer|voucher codes?)\b', 'Unusual payment method mentioned', 14),
    (r'\b(?:won|winner|prize|guaranteed returns?|inheritance)\b', 'Unexpected financial promise', 16),
]
# A brand name alone is not suspicious, and outside links can be legitimate.
KNOWN_BRANDS = [
    (re.compile(r'\b(?:nz\s*post|new zealand post(?: office)?)\b', re.I), ('nzpost.co.nz',), 'NZ Post'),
    (re.compile(r'\b(?:dhl)\b', re.I), ('dhl.com',), 'DHL'),
    (re.compile(r'\b(?:fedex|federal express)\b', re.I), ('fedex.com',), 'FedEx'),
    (re.compile(r'\b(?:ird|inland revenue|myir)\b', re.I), ('ird.govt.nz',), 'IRD'),
    (re.compile(r'\bkiwibank\b', re.I), ('kiwibank.co.nz',), 'Kiwibank'),
    (re.compile(r'\b(?:anz|anz bank)\b', re.I), ('anz.co.nz',), 'ANZ'),
    (re.compile(r'\b(?:asb|asb bank)\b', re.I), ('asb.co.nz',), 'ASB'),
    (re.compile(r'\bbnz\b', re.I), ('bnz.co.nz',), 'BNZ'),
    (re.compile(r'\bwestpac\b', re.I), ('westpac.co.nz',), 'Westpac'),
]
ACTION_REQUEST = re.compile(r'\b(?:update|verify|confirm|enter|provide|submit|click|open|visit|reply|answer|pay|complete|sign in|log in)\b', re.I)
SENSITIVE_ACTION = re.compile(r'\b(?:password|passcode|one[ -]?time (?:code|password)|\botp\b|pin|bank(?:ing)? details|card details|identity details|login details|security code)\b', re.I)
MONEY_ACTION = re.compile(r'\b(?:pay|fee|deposit|transfer|purchase|send money|send funds|withdraw|release funds|processing charge|upfront)\b', re.I)
DELIVERY_CONTEXT = re.compile(r'\b(?:parcel|package|delivery|shipment|tracking|address|postcode|home number)\b', re.I)
JOB_CONTEXT = re.compile(r'\b(?:job|recruit|employment|hiring|remote work|task|commission|earnings?|interview)\b', re.I)
ACCOUNT_CONTEXT = re.compile(r'\b(?:account|bank|login|sign[ -]?in|security|identity|verify|verification)\b', re.I)
GOV_CONTEXT = re.compile(r'\b(?:ird|inland revenue|tax refund|government|fine|infringement|penalty)\b', re.I)
FAMILY_CONTEXT = re.compile(r'\b(?:mum|mom|dad|daughter|son|boss|manager|ceo|family|new number)\b', re.I)
SHORTENERS = {'bit.ly', 'tinyurl.com', 't.co', 'is.gd', 'cutt.ly', 'shorturl.at', 'rebrand.ly'}

# A warning against sharing credentials must not be treated as a request to share them.
SAFETY_WARNING = re.compile(
    r"\b(?:never|do not|don't|won't|will not|should not|must not|avoid)\b"
    r".{0,60}\b(?:ask|share|send|give|provide|disclos(?:e|ing))\b"
    r".{0,65}\b(?:password|passcode|codes?|otp|pin|credentials?)\b", re.I
)
DISCLOSURE_REQUEST = re.compile(
    r"\b(?:send|share|tell|reply with|give|provide|enter|submit|confirm|verify)\b"
    r".{0,65}\b(?:otp|verification codes?|one[ -]?time codes?|pins?|passwords?|passcodes?)\b", re.I
)

def credential_request(text):
    # Check separate phrases so a legitimate warning doesn't cancel unrelated demands.
    for phrase in re.split(r'[.!?;\n]+', text):
        if DISCLOSURE_REQUEST.search(phrase) and not SAFETY_WARNING.search(phrase):
            return True
    return False


def is_official_domain(host, official_domains):
    return any(host == domain or host.endswith('.' + domain) for domain in official_domains)

def get_hosts(urls):
    hosts = []
    for url in urls:
        try:
            host = (urlsplit(url.rstrip('.,;!)]')).hostname or '').lower().rstrip('.')
        except ValueError:
            continue
        if host:
            hosts.append(host)
    return hosts

def extra_cues(text, urls):
    cues = []
    def add(description, weight):
        if description not in {description for description, _ in cues}:
            cues.append((description, weight))
    hosts = get_hosts(urls)
    action = bool(ACTION_REQUEST.search(text))
    asks_credentials = credential_request(text)
    if asks_credentials and ACCOUNT_CONTEXT.search(text):
        add('Request involving sensitive account or identity information', 28)
    if (action and hosts and ACCOUNT_CONTEXT.search(text)
            and re.search(r'\b(?:verify|confirm|provide|enter)\b.{0,32}\b(?:identity|account details|bank details)\b', text, re.I)
            and not SAFETY_WARNING.search(text)):
        add('Account or identity verification requested through a link', 22)
    if MONEY_ACTION.search(text) and DELIVERY_CONTEXT.search(text):
        add('Delivery linked to a payment or release fee', 25)
    if re.search(r'\b(?:won|winner|prize|lottery|reward)\b', text, re.I) and MONEY_ACTION.search(text):
        add('Unexpected prize linked to payment', 26)
    if JOB_CONTEXT.search(text) and MONEY_ACTION.search(text) and re.search(r'\b(?:fee|deposit|upfront|pay|transfer|withdraw|purchase)\b', text, re.I):
        add('Job or task opportunity involving payment', 42)
    if GOV_CONTEXT.search(text) and action and (MONEY_ACTION.search(text) or SENSITIVE_ACTION.search(text)):
        add('Government-related demand for payment or information', 26)
    if FAMILY_CONTEXT.search(text) and re.search(r'\b(?:new number|emergency|urgent|secret|do not tell|don.t tell)\b', text, re.I) and MONEY_ACTION.search(text):
        add('Personal or workplace impersonation with money request', 43)
    if asks_credentials:
        add('Request to disclose a code or password', 32)
    if action and hosts:
        for pattern, official_domains, brand_name in KNOWN_BRANDS:
            if pattern.search(text) and any(not is_official_domain(h, official_domains) for h in hosts):
                add(f'Claimed {brand_name} identity with a link outside its expected domain', 42)
        if any(h in SHORTENERS for h in hosts):
            add('Action requested through a shortened URL', 12)
        if any('xn--' in h or re.search(r'(?:\d{1,3}\.){3}\d{1,3}$', h) for h in hosts):
            add('Unusual URL hostname structure', 18)
    if DELIVERY_CONTEXT.search(text) and action and re.search(r'\b(?:missing|incomplete|wrong)\b.{0,45}\b(?:address|house number|home number|postcode)\b', text, re.I):
        add('Delivery address correction requested', 14)
    return cues

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
    cues.extend(extra_cues(text, found['urls']))
    probability=float(MODEL.predict_proba([text])[0,1])
    heuristic=min(96,8+sum(w for _,w in cues)+(7 if found['urls'] else 0))
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
