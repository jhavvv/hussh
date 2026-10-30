"""Small synthetic holdout smoke evaluation, never real-world accuracy evidence."""
import json, statistics, time
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
from intelligence import MODEL, analyze
DATA=[
('Last chance: account suspended. Send your password now.',1),
('Claim your prize with a gift card payment.',1),
('Urgent parcel fee required to release delivery.',1),
('Wire transfer needed to avoid account closure immediately.',1),
('Enter your one time code at this verification page.',1),
('Guaranteed investment reward if you pay crypto now.',1),
('Winner selected: pay a tax fee before cash release.',1),
('Bank security needs your password to unblock access.',1),
('Meet you outside the classroom after lunch.',0),
('Your dentist appointment is tomorrow at nine.',0),
('I left your study notes on the kitchen table.',0),
('Please review the agenda before our team meeting.',0),
('Your books are due back next Thursday.',0),
('The usual portal has your latest statement.',0),
('Happy birthday from everyone in the group.',0),
('Dinner was great, thank you for inviting us.',0),
]
y=[label for _,label in DATA];pred=MODEL.predict([text for text,_ in DATA])
times=[]
for text,_ in DATA:
    t=time.perf_counter();analyze(text);times.append((time.perf_counter()-t)*1000)
print(json.dumps({'dataset':'16 synthetic holdout examples; no real-world validity claim','classifier':'TF-IDF logistic regression; threshold 0.5','precision':precision_score(y,pred,zero_division=0),'recall':recall_score(y,pred,zero_division=0),'f1':f1_score(y,pred,zero_division=0),'confusion_matrix':confusion_matrix(y,pred).tolist(),'median_local_classifier_ms':statistics.median(times),'not_measured':'Device OCR latency, mobile build, real network median, independent real-world corpus'},indent=2))
