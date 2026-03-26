import requests
from qdrant_client import QdrantClient

client = QdrantClient(url="http://localhost:6333")

points = client.scroll(
    collection_name="documents",
    limit=5
)

for p in points[0]:
    print(p.payload)
API_URL = "http://localhost:8000/chat"

def chat():
    print("=== RAG Chat Console ===")
    print("Type 'exit' to quit\n")

    doc_id = input("Enter doc_id (optional): ").strip()
    if doc_id == "":
        doc_id = None

    while True:
        question = input("\nYou: ")

        if question.lower() in ["exit", "quit"]:
            print("Bye 👋")
            break

        try:
            res = requests.post(
                API_URL,
                json={
                    "question": question,
                    "doc_id": doc_id
                },
                timeout=60
            )

            data = res.json()

            print("\nAI:", data.get("answer"))

            # show sources
            sources = data.get("sources", [])
            if sources:
                print("\nSources:")
                for s in sources:
                    print(f"- Doc: {s['doc_id']} | Page: {s['page']}")

        except Exception as e:
            print("Error:", str(e))


if __name__ == "__main__":
    chat()