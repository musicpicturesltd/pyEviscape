"""
Eviscape API toolkit
Copyright (c) 2009 Music Pictures Ltd
Author: Deepak Thukral
License: MIT
"""

from pyeviscape.utils import get_unauthorised_request_token, get_authorisation_url
from pyeviscape.utils import exchange_request_token_for_access_token
from pyeviscape.eviscape import Comments, Evis, Files, Members, Nodes

#You must provide API_KEY and API_SECRET in config.py

#OAuth specific
def get_request_token():
    return get_unauthorised_request_token()

def authorize_url(request_token):
    return get_authorisation_url(request_token)

def get_access_token(request_token, verifier):
    return exchange_request_token_for_access_token(request_token, verifier)

try:
    request_token = get_request_token()

    print "Please visit below url and approve application"
    print authorize_url(request_token)
    print "Press enter verifier code after authorization ->"
    verifier = raw_input()
    access_token = get_access_token(request_token, verifier)
except:#blind
    print "WARNING: You might need to specify API_KEY and API_SECRET in config.py"
    print "You can get it from:"
    print "http://www.eviscape.com/apps/new"
    print "If you already have API_KEY and API_SECRET then remove blind except and see what you'r missing :)"
    print "Now I'll run methods without access token :("
    access_token = None
    
#Eviscape Api specific
print "Searching 'deepak' on Eviscape ..."
for m in Members.search('deepak'):
    print m
    
print "Press enter to continue ..."
raw_input()

print "Search 'simon' on Eviscape (Nodes)..."
for n in Nodes.search('simon'):
    print n
    
print "Press enter to continue ..."
raw_input()
    
print "Getting nodes of 'iapain' ..."
for n in Nodes.get_for_member('iapain', access_token=access_token):
    print n

print "Press enter to continue ..."
raw_input()

print "Getting node with nod_id=17..."
print Nodes(id=17).get()

print "Press enter to continue ..."
raw_input()

print "Getting Latest Evis ..."
for e in Evis.latest()[:5]:
    print e
    
print "Press enter to continue ..."
raw_input()

print "Getting evi with evi_id=6369 and nod_id=157..."
n = Nodes(id=157)
evi = Evis(id=6369, node=n).get()
print evi

print "Press enter to continue ..."
raw_input()

print "Getting timeline for 'iapain'"
for e in Evis.timeline(Members(id=13),n,access_token=access_token):
    print e.subject

print "Press enter to continue ..."
raw_input()

print "Getting files of above evi ..."
for f in Evis(id=6369, node=n).get_files():
    print f

for f in Evis(id=636900, node=n).get_files():
    print f
    
print "Press enter to continue ..."
raw_input()

#print "Posting commont..."
#print Comments.post(n, m, evi, 'cooooooool', access_token)

print "Getting comments of above evi ..."
for c in Comments.get(node=n, evis=evi):
    print c.ecm_comment
    


