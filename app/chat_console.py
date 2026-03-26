import requests

API_URL = "http://localhost:8000/chat"

def chat():
    print("=== RAG Chat Console ===")
    print("Type 'exit' to quit\n")

    doc_id = input("Enter doc_id (optional): ").strip()
    if doc_id == "":
        doc_id = None

    while True:
        question = input("\nYou: ").strip()
        if question.lower() in {"exit", "quit"}:
            print("Bye")
            break

        try:
            res = requests.post(
                API_URL,
                json={
                    "question": question,
                    "doc_id": doc_id,
                },
                timeout=120,
            )

            print(f"\nSTATUS: {res.status_code}")
            print(f"RAW: {res.text}\n")

            res.raise_for_status()
            data = res.json()

            print("AI:", data.get("answer"))

            sources = data.get("sources", [])
            if sources:
                print("\nSources:")
                for s in sources:
                    print(f"- Doc: {s.get('doc_id')} | Page: {s.get('page')}")

        except Exception as e:
            print("Error:", str(e))


if __name__ == "__main__":
    chat()