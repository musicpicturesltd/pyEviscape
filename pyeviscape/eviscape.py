"""
Eviscape API wrapper
Author: Deepak Thukral<deepak@musicpictures.com>
PyEviscape provides functions for interacting with the Eviscape API.

The MIT License

Copyright (c) 2009 MMIX Musicpictures Ltd, Berlin
"""

#Preferably requires python2.5+ if you are using older python make sure you've
#hashlib packages

import hashlib
import pickle
import random
import StringIO
import time
import urllib
from utils import request_get, request_protected_get, request_protected_post, SERVER, smart_str, parseDateTime
from config import FORMATTER
    
    
class Files(object):
    """ Represents files on Eviscape """
    def __init__(self, id, fle_title=None, fle_permalink=None):
        self.id = id
        self.fle_title = fle_title
        self.fle_permalink = fle_permalink
        
    def __str__(self):
        return smart_str("File Object: %s (%s)" % (self.id, self.fle_permalink))
    

class Comments(object):
    """ Represent comments on Eviscape """
    def __init__(self, id, node=None, ecm_comment=None, mem_pen_name=None, ecm_insert_date=None):
        self.id = id
        self.node = node
        self.ecm_comment = ecm_comment
        self.mem_pen_name = mem_pen_name
        self.ecm_insert_date = ecm_insert_date
    
    @classmethod
    def get(self, node, evis, access_token=None, per_page=10, page=1):
        """
        Gets comments for an evis (optionally required access_token)
        Usage: Comments.get(Nodes(id=17), Evis(id=6259, Nodes(id=17))
        Returns: List of Comments object
        Eviscape API Method: comments.get
        """
        method = "comments.get"
        if access_token is None:
            data = request_get(method, nod_id=node.id, evi_id=evis.id,\
                               per_page=per_page, page=page)
        else:
            data = request_protected_get(method, access_token, nod_id=node.id,\
                                         evi_id=evis.id, per_page=per_page, page=page)
        if FORMATTER == 'json':
            return _handle_comment_json(data)
        else:
            return _handle_comment_xml(data)
    
    @classmethod
    def post(self, node, member, evis, comment_body, access_token, per_page=10, page=1):
        """
        Posts a comments for an evis (optionally required access_token)
        Usage: Comments.post(Nodes(id=17), Members(id=13), Evis(id=6259, Nodes(id=17), "Hello World")
        Returns: Comments object
        Eviscape API Method: comment.post
        """
        method="comment.post"
        data = request_protected_post(method, access_token, nod_id=node.id,\
                                         evi_id=evis.id, mem_id=member.id, comment=comment_body,\
                                         per_page=per_page, page=page)
        if FORMATTER == 'json':
            return _handle_comment_json(data)[0]
        else:
            return _handle_comment_xml(data)[0]
    
    def __str__(self):
        return smart_str("Comment Object: %s" % self.id)

class Members(object):
    """ Represent User/Member on Eviscape """
    def __init__(self, id, mem_name=None, mem_full_name=None,\
                 mem_pen_name=None, primary_node=None):
        self.id = id
        self.mem_name = mem_name
        self.mem_full_name = mem_full_name
        self.mem_pen_name = mem_pen_name
        self.primary_node = primary_node
        
    @classmethod
    def get_by_token(self, access_token, per_page=10, page=1):
        """
        Get member via access_token
        Usage: Member.get_by_token(access_token)
        Returns: Member Object
        Eviscape API Method: member.token
        """
        method = "member.token"
        data = request_protected_get(method, access_token, per_page=per_page, page=page)
        if FORMATTER == 'json':
            return _handle_member_json(data)[0]
        else:
            return _handle_member_xml(data)[0]
        

    @classmethod
    def search(self, q, per_page=10, page=1):
        """
        Search members on eviscape
        Usage: Members.search("deepak")
        Returns: List of Members object
        Eviscape API Method: members.search
        """
        method = "members.search"
        data = request_get(method, q=q, per_page=per_page, page=page)
        if FORMATTER == 'json':
            return _handle_member_json(data)
        else:
            return _handle_member_xml(data)
        
    
    def __str__(self):
        return smart_str("Member Object: %s (%s)" % (self.id, str(self.mem_name)))

class Nodes(object):
    """ Represent Node/Profile/Evisite on Eviscape """
    def __init__(self, id, nod_name=None, member=None, nod_permalink=None, nod_strict=None,\
                 nod_logo_image=None, nod_desc=None, nod_listener_count=None):
        self.id = id
        self.member = member
        self.nod_name = nod_name
        self.nod_desc = nod_desc
        self.nod_listener_count = nod_listener_count
        if nod_permalink is not None and not nod_permalink.startswith('http'):
            if nod_permalink == '':
                self.nod_permalink = None
            else:
                self.nod_permalink = "http://"+ SERVER + nod_permalink
        else:
            self.nod_permalink = nod_permalink
        if nod_logo_image is not None and not nod_logo_image == "":
            self.nod_logo_image = "http://%s/static/%s" % (SERVER, nod_logo_image)
        else:
            self.nod_logo_image = None
        self.nod_strict = nod_strict
        
    def get(self, access_token=None, per_page=10, page=1):
        """
        Get details of a Node/Profile/Evisite
        Usage: Nodes(id=17).get()
        Returns: Nodes object
        Eviscape API Method: node.get
        """
        method="node.get"
        if access_token is None:
            data = request_get(method, nod_id=self.id, per_page=per_page, page=page)
        else:
            data = request_protected_get(method, access_token, nod_id=self.id,\
                                         per_page=per_page, page=page)
        if FORMATTER == 'json':
            return _handle_node_json(data)[0]
        else:
            return _handle_node_xml(data)[0]
    
    
    def listeners(self, access_token=None, per_page=10, page=1):
        """
        Get Listeners/Followers of a Node/Profile/Evisite
        Usage: Nodes(id=17).listeners()
        Returns: List of Nodes object
        Eviscape API Method: nodes.listeners
        """
        method = "nodes.listeners"
        if access_token is None:
            data = request_get(method, nod_id=self.id, per_page=per_page, page=page)
        else:
            data = request_protected_get(method, access_token, nod_id=self.id,\
                                         per_page=per_page, page=page)
        if FORMATTER == 'json':
            return _handle_node_json(data)
        else:
            return _handle_node_xml(data)
        
    
    def speakers(self, access_token=None, per_page=10, page=1):
        """
        Get Nodes/Profile/Evisite which base node is Followering 
        Usage: Nodes(id=17).speakers()
        Returns: List of Nodes object
        Eviscape API Method: nodes.speakers
        """
        method = "nodes.speakers"
        if access_token is None:
            data = request_get(method, nod_id=self.id, per_page=per_page, page=page)
        else:
            data = request_protected_get(method, access_token, nod_id=self.id,\
                                         per_page=per_page, page=page)
        if FORMATTER == 'json':
            return _handle_node_json(data)
        else:
            return _handle_node_xml(data)
    
    @classmethod
    def get_for_member(self, member_name, perms='write', access_token=None, per_page=10, page=1):
        """
        Get Node/Profile/Evisite of a User/Member
        Usage: Nodes.get_for_memnber("iapain")
        Returns: List of Nodes object
        Eviscape API Method: nodes.get
        """
        method = "nodes.member"
        if access_token is None:
            data = request_get(method, mem_name=member_name, perms=perms, per_page=per_page, page=page)
        else:
            data = request_protected_get(method, access_token, mem_name=member_name,\
                                          perms=perms, per_page=per_page, page=page)
        if FORMATTER == 'json':
            return _handle_node_json(data)
        else:
            return _handle_node_xml(data)
    
    @classmethod
    def created_by_member(self, member_name, access_token=None, per_page=10, page=1):
        """
        Get Node/Profile/Evisite which was created by User/Member
        Usage: Nodes.created_by_member("iapain")
        Returns: List of Nodes object
        Eviscape API Method: nodes.get
        """
        method = "nodes.get"
        if access_token is None:
            data = request_get(method, mem_name=member_name, per_page=per_page, page=page)
        else:
            data = request_protected_get(method, access_token, mem_name=member_name,\
                                         per_page=per_page, page=page)
        if FORMATTER == 'json':
            return _handle_node_json(data)
        else:
            return _handle_node_xml(data) 
    
    @classmethod
    def search(self, q, per_page=10, page=1):
        """
        Searches Nodes/Evisite/Profile on eviscape (public only)
        Usage: Nodes.search('iapain')
        Returns: List of Nodes object
        Eviscape API Method: nodes.search
        """
        method = "nodes.search"
        data = request_get(method, q=q, per_page=per_page, page=page)
        if FORMATTER == 'json':
            return _handle_node_json(data)
        else:
            return _handle_node_xml(data)
    
    def __str__(self):
        return smart_str("Node Object: %s (%s)" % (self.id, self.nod_name))

class Evis(object):
    """ Represents Evis on Eviscape """
    def __init__(self, id, node, member=None, evi_subject=None, evi_body=None,\
                 evi_type=None, evi_comment_count=None, evi_insert_date=None,\
                 evi_permalink=None, files=[], reverse_type_id=True):
        self.id = id
        self.node = node
        self.member = member
        self.evi_subject = evi_subject
        self.evi_body = evi_body
        self.evi_insert_date = evi_insert_date
        self.evi_type = evi_type
        self.evi_permalink = evi_permalink
        self.evi_comment_count = evi_comment_count
        self.files = files
        
        
    def get(self, access_token=None, per_page=10, page=1):
        """
        Get an Evis/Post/Article
        Usage: Evis(id=6369).get()
        Returns: An Evis Object
        Eviscape API Method: evis.get
        """
        method = "evis.get"
        if access_token is None:
            data = request_get(method, evi_id=self.id, nod_id=self.node.id,\
                               per_page=per_page, page=page)
        else:
            data = request_protected_get(method, access_token, evi_id=self.id,\
                                         nod_id=self.node.id, per_page=per_page, page=page)
        if FORMATTER == 'json':
            return _handle_evis_json(data)[0]
        else:
            return _handle_evis_xml(data)[0]
    
    def get_files(self, access_token=None, per_page=10, page=1):
        """
        Get Files belongs to an Evis/Post/Article
        Usage: Evis(id=6369).get_files()
        Returns: A list of Files Object
        Eviscape API Method: evis.get_files
        """
        method = "evis.get_files"
        if access_token is None:
            data = request_get(method, evi_id=self.id, nod_id=self.node.id,\
                               per_page=per_page, page=page)
        else:
            data = request_protected_get(method, access_token, evi_id=self.id,\
                                         nod_id=self.node.id, per_page=per_page, page=page)
        if FORMATTER == 'json':
            self.files = _handle_file_json(data)
        else:
            self.files = _handle_file_xml(data)
        return self.files
        
    
    @classmethod
    def post(self, evi_subject, evi_body, evi_type, member, node, evis_tags,\
             access_token, evis_is_draft=False, per_page=10, page=1):
        """
        Posts an Evis/Post/Article
        Usage: Evis.post('Cool', 'I am feeling cool', 'text', Members(id=13), Nodes(id=17), 'cool test')
        Returns: An Evis Object
        Eviscape API Method: evis.post
        """
        method = "evis.post"
        data = request_protected_post(method, access_token, evi_subject=evi_subject,\
                                      evi_body=evi_body, evi_type=evi_type,\
                                      mem_id=member.id, nod_id=node.id,\
                                      evi_tags=evis_tags, evis_is_draft=evis_is_draft,\
                                      per_page=per_page, page=page)
        
        if FORMATTER == 'json':
            return _handle_evis_json(data)[0]
        else:
            return _handle_evis_xml(data)[0]
            
    @classmethod
    def timeline(self, member, node, access_token, per_page=10, page=1):
        """
        Get timeline for a member
        Usage: Evis.timeline(memberobj, nodeobj, 'token')
        Returns: List of evis
        Eviscape API method: evis.timeline
        """
        method = "evis.timeline"
        data = request_protected_get(method, access_token, mem_id=member.id,\
                                      nod_id=node.id, per_page=per_page, page=page)
        
        if FORMATTER == 'json':
            return _handle_evis_json(data)
        else:
            return _handle_evis_xml(data)
        
    
    @classmethod
    def xsearch(self, query, access_token=None, per_page=10, page=1):
        """
        Search an Evis/Post/Article
        Usage: Evis.search('bon jovi OR metallica')
        Returns: generator object containing evis
        Eviscape API Method: evis.search
        """
        method = "evis.search"
        if access_token is None:
            data = request_get(method, q=query, per_page=per_page, page=page)
        else:
            data = request_protected_get(method, access_token, q=query,\
                                         per_page=per_page, page=page)
        
        if FORMATTER == 'json':
            if isinstance(data.get('objects', None), list):
                for evi in data['objects']:
                    yield _parse_compact_evis(evi)
        else:
            if data.rsp.objects.__dict__.has_key('evis'):
                if isinstance(data.rsp.objects.evis, list):
                    for evi in data.rsp.objects.evis:
                        yield _parse_compact_evis(evi)
                else:
                    yield _parse_compact_evis(data.rsp.objects.evis)
    
    @classmethod
    def xsent(self, node, access_token=None, per_page=10, page=1):
        """
        Get all posted Evis/Post/Article of a Node/Profile/Evisite
        Usage: Evis.xsent(Nodes(id=17))
        Returns: A Generator with Evis Object
        Eviscape API Method: evis.sent
        """
        method = "evis.sent"
        if access_token is None:
            data = request_get(method, nod_id=node.id, per_page=per_page, page=page)
        else:
            data = request_protected_get(method, access_token, nod_id=node.id,\
                                         per_page=per_page, page=page)
        if FORMATTER == 'json':
            if isinstance(data.get('objects', None), list):
                for evi in data['objects']:
                    yield _parse_evis(evi)
        else:
            if data.rsp.objects.__dict__.has_key('evis'):
                if isinstance(data.rsp.objects.evis, list):
                    for evi in data.rsp.objects.evis:
                        yield _parse_evis(evi)
                else:
                    yield _parse_evis(data.rsp.objects.evis)
                
    @classmethod
    def xreceived(self, member, node, access_token=None, per_page=10, page=1):
        """
        Get all received Evis/Post/Article of a Node/Profile/Evisite
        Usage: Evis.xreceived(Member(id=13), Nodes(id=17))
        Returns: A Generator with Evis Object
        Eviscape API Method: evis.received
        """
        method = "evis.received"
        if access_token is None:
            data = request_get(method, mem_id=member.id, nod_id=node.id, per_page=per_page, page=page)
        else:
            data = request_protected_get(method, access_token, mem_id=member.id, nod_id=node.id,\
                                         per_page=per_page, page=page)
        if FORMATTER == 'json':
            if isinstance(data.get('objects', None), list):
                for evi in data['objects']:
                    yield _parse_compact_evis(evi)
        else:
            if data.rsp.objects.__dict__.has_key('evis'):
                if isinstance(data.rsp.objects.evis, list):
                    for evi in data.rsp.objects.evis:
                        yield _parse_compact_evis(evi)
                else:
                    yield _parse_compact_evis(data.rsp.objects.evis)
                
    @classmethod
    def xlatest(self, access_token=None, per_page=10, page=1):
        """
        Get all latest evis
        Usage: Evis.xlatest()
        Returns: A Generator with Evis Object
        Eviscape API Method: evis.latest
        """
        method = "evis.latest"
        if access_token is None:
            data = request_get(method, per_page=per_page, page=page)
        else:
            data = request_protected_get(method, access_token,\
                                         per_page=per_page, page=page)
        if FORMATTER == 'json':
            if isinstance(data.get('objects', None), list):
                for evi in data['objects']:
                    yield _parse_compact_evis(evi)
        else:
            if data.rsp.objects.__dict__.has_key('evis'):
                if isinstance(data.rsp.objects.evis, list):
                    for evi in data.rsp.objects.evis:
                        yield _parse_compact_evis(evi)
                else:
                    yield _parse_compact_evis(data.rsp.objects.evis)
                
    @classmethod
    def search(self, query, access_token=None, per_page=10, page=1):
        """
        Search an Evis/Post/Article
        Usage: Evis.search('bon jovi OR metallica')
        Returns: List of evis
        Eviscape API Method: evis.search
        """
        method = "evis.search"
        if access_token is None:
            data = request_get(method, q=query, per_page=per_page, page=page)
        else:
            data = request_protected_get(method, access_token, q=query,\
                                         per_page=per_page, page=page)
            
        if FORMATTER == 'json':
            return _handle_evis_json(data, compact=True)
        else:
            return _handle_evis_xml(data, compact=True)
    
    @classmethod
    def sent(self, node, access_token=None, per_page=100, page=1):
        """
        Get all posted Evis/Post/Article of a Node/Profile/Evisite
        Usage: Evis.sent(Nodes(id=17))
        Returns: A list of Evis Object
        Eviscape API Method: evis.sent
        """
        method = "evis.sent"
        if access_token is None:
            data = request_get(method, nod_id=node.id, per_page=per_page, page=page)
        else:
            data = request_protected_get(method, access_token, nod_id=node.id,\
                                         per_page=per_page, page=page)
        if FORMATTER == 'json':
            return _handle_evis_json(data)
        else:
            return _handle_evis_xml(data)
    
    @classmethod
    def received(self, member, node, access_token=None, per_page=10, page=1):
        """
        Get all received Evis/Post/Article of a Node/Profile/Evisite
        Usage: Evis.received(Member(id=13), Nodes(id=17))
        Returns: A list with Evis Object
        Eviscape API Method: evis.received
        """
        method = "evis.received"
        if access_token is None:
            data = request_get(method, mem_id=member.id, nod_id=node.id, per_page=per_page, page=page)
        else:
            data = request_protected_get(method, access_token, mem_id=member.id, nod_id=node.id,\
                                         per_page=per_page, page=page)
        if FORMATTER == 'json':
            return _handle_evis_json(data, compact=True)
        else:
            return _handle_evis_xml(data, compact=True)
    
    @classmethod
    def latest(self, access_token=None, per_page=10, page=1):
        """
        Get all latest Evis/Post/Article
        Usage: Evis.latest()
        Returns: A list with Evis Object
        Eviscape API Method: evis.latest
        """
        method = "evis.latest"
        if access_token is None:
            data = request_get(method, per_page=per_page, page=page)
        else:
            data = request_protected_get(method, access_token,\
                                         per_page=per_page, page=page)
        if FORMATTER == 'json':
            return _handle_evis_json(data, compact=True)
        else:
            return _handle_evis_xml(data, compact=True)
    
    def __str__(self):
        return smart_str("Evis Object: %s (%s)" % (self.id, self.evi_permalink))
    

def _handle_member_xml(data):
    "Handles xml data object for member"
    members = []
    if data.rsp.objects.__dict__.has_key('members'):
        if isinstance(data.rsp.objects.members, list):
            for m in data.rsp.objects.members:
                members.append(_parse_member(m))
        else:
            members = [_parse_member(data.rsp.objects.members)]
    return members

def _handle_node_xml(data):
    "Handles xml data for nodes"
    nodes = []
    if data.rsp.objects.__dict__.has_key('node'):
        if isinstance(data.rsp.objects.node, list):
            for n in data.rsp.objects.node:
                nodes.append(_parse_node(n))
        else:
            nodes = [_parse_node(data.rsp.objects.node)]
    return nodes

def _handle_evis_xml(data, compact=False):
    "Handles xml data for evis"
    evis = []
    if data.rsp.objects.__dict__.has_key('evis'):
        if isinstance(data.rsp.objects.evis, list):
            for evi in data.rsp.objects.evis:
                if compact:
                    evis.append(_parse_compact_evis(evi))
                else:
                    evis.append(_parse_evis(evi))
        else:
            if compact:
                evis = [_parse_compact_evis(data.rsp.objects.evis)]
            else:
                evis = [_parse_evis(data.rsp.objects.evis)]
        return evis
    return None

def _handle_comment_xml(data):
    comments = []
    if data.rsp.objects.__dict__.has_key('comment'):
        if isinstance(data.rsp.objects.comment, list):
            for c in data.rsp.objects.comment:
                comments.append(_parse_comment(c))
        else:
            comments = [_parse_comment(data.rsp.objects.comment)]
    return comments

def _handle_comment_json(data):
    comment = []
    if isinstance(data.get('objects', None), list):
        for c in data['objects']:
            comment.append(_parse_comment_json(c))
    return comment

def _handle_evis_json(data, compact=False):
    "Handles json data for evis"
    evis = []
    if isinstance(data.get('objects', None), list):
        for evi in data['objects']:
            if compact:
                evis.append(_parse_compact_evis_json(evi))
            else:
                evis.append(_parse_evis_json(evi))
    return evis

def _handle_file_xml(data):
    files=[]
    if data.rsp.objects.__dict__.has_key('files'):
        if isinstance(data.rsp.objects.files, list):
            for fle in data.rsp.objects.files:
                files.append(_parse_file(fle))
        else:
            files = [_parse_file(data.rsp.objects.files)]
    return files

def _handle_file_json(data):
    "Handles json data for file"
    files = []
    if isinstance(data.get('objects', None), list):
        for f in data['objects']:
            files.append(_parse_file_json(f))
    return files

def _handle_node_json(data):
    "Handles json data for nodes"
    nodes = []
    if isinstance(data.get('objects', None), list):
        for n in data['objects']:
            nodes.append(_parse_node_json(n))
    return nodes

def _handle_member_json(data):
    "Handle simplejson data object for member"
    member = []
    if isinstance(data.get('objects', None), list):
        for m in data['objects']:
            member.append(_parse_member_json(m))
    return member


def _parse_evis_json(e):
    evi = e.get('evis', {})
    m = Members(int(evi.get('mem_id', None)), evi.get('mem_name', None))
    n = Nodes(int(evi.get('nod_id', None)), evi.get('nod_name', None), m)
    return Evis(e.get('id', None),\
                n,\
                m,\
                evi.get('evi_subject', None),\
                evi.get('evi_body', None),\
                evi.get('typ_value', None),\
                evi.get('evi_comment_count', None),\
                parseDateTime(evi.get('evi_insert_date', None)),\
                e.get('ref', None)
    )

def _parse_compact_evis_json(e):
    evi = e.get('evis', {})
    m = Members(int(evi.get('mem_id', None)), evi.get('mem_name', None))
    n = Nodes(int(evi.get('nod_id', None)), evi.get('nod_name', None), m)
    return Evis(id=e.get('id', None),\
                node=n,\
                member=m,\
                evi_subject=evi.get('evi_subject', None),\
                evi_comment_count=evi.get('evi_comment_count', None),\
                evi_permalink=e.get('ref', None),\
                evi_insert_date=parseDateTime(evi.get('evi_insert_date', None)))

def _parse_member_json(m):
    mem = m.get('member', {})
    if mem.has_key('nod_id_primary'):
        n = Nodes(int(mem['nod_id_primary']))
    else:
        n = None
    return Members(m.get('id', None),\
                   mem.get('mem_name', None),\
                   mem.get('mem_full_name', None),\
                   mem.get('mem_pen_name', None),
                   n)


def _parse_node_json(n):
    nod = n.get('node', {})
    if nod.has_key('mem_id'):
        m = Members(int(nod['mem_id']))
    else:
        m = None
    return Nodes(n.get('id', None),\
                 nod.get('nod_name', None),\
                 m,\
                 n.get('ref', None),\
                 nod.get('nod_strict', None),\
                 nod.get('nod_logo_image', None),\
                 nod.get('nod_desc', None),\
                 nod.get('nod_listener_count', None)\
                )

def _parse_file_json(f):
    "Parse file response simplejson"
    file = f.get('nodes', {})
    if not f.get('ref', '').startswith('http'):
        ref = "http://www.eviscape.com%s" % f.get('ref', '')
    else:
        ref = f.get('ref', None)
    return Files(f.get('id', None),\
                 file.get('fle_title', None),\
                 ref)

def _parse_comment_json(c):
    "Parse comment response"
    comment= c.get('comment', {})
    n = Nodes(int(comment.get('nod_id', None)))
    return Comments(c.get('id', None),\
                    n,\
                    comment.get('ecm_comment', None),\
                    comment.get('mem_pen_name', None),\
                    comment.get('ecm_insert_date', None))
    
def _parse_member(member):
    "Parse member response"
    if hasattr(member, 'mem_pen_name') and hasattr(member.mem_pen_name, 'text'):
        mem_pen_name = member.mem_pen_name.text
    else:
        mem_pen_name = None
    if hasattr(member, 'nod_id_primary'):
        n = Nodes(int(member.nod_id_primary.text))
    else:
        n = None
    m = Members(member.id,\
                member.mem_name.text,\
                member.mem_full_name.text,\
                mem_pen_name,\
                n)
    return m

def _parse_node(node):
    "Parse Node response"
    if hasattr(node, 'nod_logo_image'):
        logo = node.nod_logo_image.text
    else:
        logo = None
    if hasattr(node, 'nod_desc'):
        desc = node.nod_desc.text
    else:
        desc = None
    
    if hasattr(node, 'nod_listener_count'):
        count = node.nod_listener_count
    else:
        count = None
    if hasattr(node, 'mem_id'):
        m = Members(int(node.mem_id.text))
    else:
        m = None
    n = Nodes(node.id, node.nod_name.text, m, node.ref, node.nod_strict.text,\
          logo, desc, count)
    return n

def _parse_evis(evis, reverse_type_id=True):
    "Parse Evis response"
    m = Members(int(evis.mem_id.text))
    n = Nodes(int(evis.nod_id.text))
    evi = Evis(evis.id, n, m, evis.evi_subject.text, evis.evi_body.text,\
             evis.type.text, evis.evi_comment_count.text, parseDateTime(evis.evi_insert_date.text), evis.ref,\
             reverse_type_id=reverse_type_id)
    return evi

def _parse_compact_evis(evis, reverse_type_id=True):
    "Parse less informative evis response"
    m = Members(int(evis.mem_id.text))
    n = Nodes(int(evis.nod_id.text))
    evis = Evis(id=evis.id, node=n, member=m, evi_subject=evis.evi_subject.text,\
                evi_comment_count=evis.evi_comment_count.text,\
                evi_permalink=evis.ref, evi_insert_date=parseDateTime(evis.evi_insert_date.text), reverse_type_id=reverse_type_id)
    return evis

def _parse_file(file):
    "Parse file response"
    if not file.ref.startswith('http'):
        ref = "http://www.eviscape.com%s" % file.ref
    else:
        ref = file.ref
    fle = Files(file.id, file.fle_title.text, ref)
    return fle

def _parse_comment(comment):
    "Parse comment response"
    n = Nodes(int(comment.nod_id.text))
    if not hasattr(comment, 'ecm_insert_date'):
        ecm_insert_date = ""
    else:
        ecm_insert_date = comment.ecm_insert_date.text
    if hasattr(comment, 'mem_pen_name') and hasattr(comment.mem_pen_name, 'text'):
        comm = Comments(comment.id, n, comment.ecm_comment.text, comment.mem_pen_name.text,\
                        ecm_insert_date)
    else:
        comm = Comments(comment.id, n, comment.ecm_comment.text, None,ecm_insert_date)
    return comm