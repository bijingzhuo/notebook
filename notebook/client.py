"""
client.py: XML-RPC client for the notebook service.
Menu options:
  1. Add note (input topic and text; timestamp auto-generated)
  2. Query notes by topic
  3. Append Wikipedia info (input target topic and query; defaults to target topic)
  4. Exit
"""

import xmlrpc.client
import datetime

def print_menu():
    print("\n===== Notebook Client Menu =====")
    print("1. Add note")
    print("2. Query notes by topic")
    print("3. Append Wikipedia info")
    print("4. Exit")

def main():
    server_url = "http://localhost:8000"
    try:
        proxy = xmlrpc.client.ServerProxy(server_url, allow_none=True)
    except Exception as e:
        print("Error connecting to server:", e)
        return
    while True:
        print_menu()
        choice = input("Select an option (1-4): ").strip()
        if choice == "1":
            topic = input("Enter topic: ").strip()
            text = input("Enter note text: ").strip()
            timestamp = datetime.datetime.now().isoformat()
            result = proxy.add_note(topic, text, timestamp)
            print("Server response:", result)
        elif choice == "2":
            topic = input("Enter topic: ").strip()
            notes = proxy.get_notes(topic)
            if isinstance(notes, str):
                print("Error:", notes)
            elif not notes:
                print("No notes for this topic.")
            else:
                print(f"Notes for topic '{topic}':")
                for name, note_text, note_ts in notes:
                    print(f"Name: {name}")
                    print(f"Text: {note_text}")
                    print(f"Timestamp: {note_ts}")
                    print("---------------")
        elif choice == "3":
            target_topic = input("Enter target topic for Wikipedia info: ").strip()
            wiki_query = input("Enter Wikipedia query (leave blank to use topic): ").strip()
            if not wiki_query:
                wiki_query = target_topic
            result = proxy.append_wikipedia_info(target_topic, wiki_query)
            print("Server response:", result)
        elif choice == "4":
            print("Exiting client.")
            break
        else:
            print("Invalid option, try again.")

if __name__ == "__main__":
    main()
