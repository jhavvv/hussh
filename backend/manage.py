"""Explicit operator-only role provisioning, never exposed as an HTTP endpoint."""
import argparse
from sqlalchemy import select
from app import engine,users,setup
p=argparse.ArgumentParser();p.add_argument('action',choices=['promote-reviewer','revoke-reviewer']);p.add_argument('username');a=p.parse_args()
setup()
with engine.begin() as c:
    user=c.execute(select(users).where(users.c.username==a.username.lower())).mappings().first()
    if not user:raise SystemExit('Account does not exist. Register through the app first.')
    role='reviewer' if a.action=='promote-reviewer' else 'user'
    c.execute(users.update().where(users.c.id==user['id']).values(role=role))
print('Role updated. Sign in again to refresh the client interface.')
