"""
server.py: Multi-threaded XML-RPC server for a notebook service.
XML structure:
  - Root: <data>
  - Each topic: <topic name="...">
  - Each note: <note name="..."> with <text> and <timestamp> children

Functions:
  1. add_note: Add a note to a topic (create topic if needed)
  2. get_notes: Query notes by topic
  3. append_wikipedia_info: Use a query to fetch a Wikipedia link and append it to a topic
"""

import os
import xml.etree.ElementTree as ET
from xmlrpc.server import SimpleXMLRPCRequestHandler, SimpleXMLRPCServer
from socketserver import ThreadingMixIn
import threading
import requests

DB_FILE = "notebook_db.xml"
xml_lock = threading.Lock()

def init_db():
    # Create XML file with <data> root if not exists
    if not os.path.exists(DB_FILE):
        root = ET.Element("data")
        tree = ET.ElementTree(root)
        tree.write(DB_FILE, encoding='utf-8', xml_declaration=True)
        print("Initialized DB:", DB_FILE)

def add_note(topic, text, timestamp):
    print(f"[{threading.current_thread().name}] Processing add_note")
    with xml_lock:
        try:
            tree = ET.parse(DB_FILE)
            root = tree.getroot()
        except Exception as e:
            return "Error reading DB: " + str(e)
        # Find or create topic element
        topic_elem = None
        for t in root.findall("topic"):
            if t.get("name") == topic:
                topic_elem = t
                break
        if topic_elem is None:
            topic_elem = ET.SubElement(root, "topic", {"name": topic})
        # Create note with name = first 50 characters of text
        note_name = text.strip() if len(text.strip()) <= 50 else text.strip()[:50]
        note_elem = ET.SubElement(topic_elem, "note", {"name": note_name})
        # Add text and timestamp children
        text_elem = ET.SubElement(note_elem, "text")
        text_elem.text = text
        ts_elem = ET.SubElement(note_elem, "timestamp")
        ts_elem.text = timestamp
        try:
            tree.write(DB_FILE, encoding='utf-8', xml_declaration=True)
        except Exception as e:
            return "Error writing DB: " + str(e)
    return f"Note added to topic '{topic}'."

def get_notes(topic):
    print(f"[{threading.current_thread().name}] Processing get_notes")
    with xml_lock:
        try:
            tree = ET.parse(DB_FILE)
            root = tree.getroot()
        except Exception as e:
            return "Error reading DB: " + str(e)
        for t in root.findall("topic"):
            if t.get("name") == topic:
                notes = []
                for note in t.findall("note"):
                    name = note.get("name")
                    text_elem = note.find("text")
                    note_text = text_elem.text.strip() if text_elem is not None and text_elem.text is not None else ""
                    ts_elem = note.find("timestamp")
                    note_ts = ts_elem.text.strip() if ts_elem is not None and ts_elem.text is not None else ""
                    notes.append((name, note_text, note_ts))
                return notes
    return []

def append_wikipedia_info(topic, wiki_query):
    print(f"[{threading.current_thread().name}] Processing append_wikipedia_info")
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "opensearch",
        "search": wiki_query,
        "limit": "1",
        "namespace": "0",
        "format": "json"
    }
    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        if len(data) >= 4 and len(data[3]) > 0:
            wiki_link = data[3][0]
        else:
            wiki_link = "No Wikipedia link found."
    except Exception as e:
        wiki_link = "Error querying Wikipedia: " + str(e)
    with xml_lock:
        try:
            tree = ET.parse(DB_FILE)
            root = tree.getroot()
        except Exception as e:
            return "Error reading DB: " + str(e)
        # Find or create topic element
        topic_elem = None
        for t in root.findall("topic"):
            if t.get("name") == topic:
                topic_elem = t
                break
        if topic_elem is None:
            topic_elem = ET.SubElement(root, "topic", {"name": topic})
        # Append Wikipedia link as a note
        note_elem = ET.SubElement(topic_elem, "note", {"name": "WikipediaLink"})
        text_elem = ET.SubElement(note_elem, "text")
        text_elem.text = wiki_link
        ts_elem = ET.SubElement(note_elem, "timestamp")
        ts_elem.text = "Wikipedia"
        try:
            tree.write(DB_FILE, encoding='utf-8', xml_declaration=True)
        except Exception as e:
            return "Error writing DB: " + str(e)
    return f"Wikipedia info added to topic '{topic}'."

class ThreadedXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):
    pass

class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

def run_server(host="localhost", port=8000):
    init_db()
    with ThreadedXMLRPCServer((host, port), requestHandler=RequestHandler, allow_none=True) as server:
        server.register_introspection_functions()
        server.register_function(add_note, "add_note")
        server.register_function(get_notes, "get_notes")
        server.register_function(append_wikipedia_info, "append_wikipedia_info")
        print(f"Multi-threaded XML-RPC server started at {host}:{port}")
        server.serve_forever()

if __name__ == "__main__":
    run_server()

