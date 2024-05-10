import requests
import uuid

# Set the base URL for the API
BASE_URL = "http://127.0.0.1:8000"

def format_document(document):
    """Format a document for display, ensuring graceful handling of missing data."""
    doc_id = document.get('id', 'No ID provided')
    doc_text = document.get('text', 'No text provided')
    return f"ID: {doc_id}\nText: {doc_text}\n"

def create_sample_documents(session):
    """Create a variety of sample documents to populate the database and facilitate diverse test cases."""
    texts = [
        "This is a sample document for testing the FastAPI server.",
        "Exploring Elasticsearch with a sample dataset reveals many insights.",
        "Sample data can significantly improve development speed.",
        "Here's another sample text to populate our database.",
        "Using sample queries helps illustrate the power of search engines."
    ]
    for text in texts:
        document_id = str(uuid.uuid4())
        document = {"id": document_id, "text": text}
        response = session.post(f"{BASE_URL}/documents/", json=document)
        print(f"Document created: ID: {document_id}, Status: {response.json().get('status')}")

def test_create_document(session, text):
    """Test the document creation endpoint and handle responses appropriately."""
    document_id = str(uuid.uuid4())
    response = session.post(f"{BASE_URL}/documents/", json={"id": document_id, "text": text})
    print(response.json())  # Debugging output
    if response.status_code == 200:
        print("Create Document Response:", format_document(response.json()))
    else:
        print(f"Failed to create document: {response.status_code}, {response.text}")

def test_read_document(session, document_id):
    """Test the document retrieval endpoint by document ID."""
    response = session.get(f"{BASE_URL}/documents/{document_id}")
    if response.status_code == 200:
        print("Read Document Response:", format_document(response.json()))
    else:
        print(f"Failed to read document: {response.status_code}, {response.text}")

def test_search_documents(session, query):
    """Test the search functionality by querying documents containing a specific text."""
    response = session.get(f"{BASE_URL}/search/", params={"query": query})
    if response.status_code == 200:
        result = response.json()
        formatted_results = "\n".join(format_document(doc) for doc in result['results'])
        print(f"Search Response:\nQuery: {result['query']}\nResults:\n{formatted_results}\nTotal Results: {result['total']}")
    else:
        print(f"Failed to search documents: {response.status_code}, {response.text}")

def test_generate_answer(session, query):
    """Test the generate-answer endpoint to receive a detailed answer based on a query."""
    response = session.post(f"{BASE_URL}/generate-answer/", json={"text": query})
    if response.status_code == 200:
        result = response.json()
        print(f"Generated Answer Response:\nQuery: {query}\nAnswer: {result['generated_answer']}")
    else:
        print(f"Failed to generate answer: {response.status_code}, {response.text}")

def main():
    """Main function to coordinate the testing of document creation, retrieval, and search."""
    session = requests.Session()
    create_sample_documents(session)
    doc = test_create_document(session, "This is a sample document for testing the FastAPI server.")
    if doc and 'id' in doc:
        test_read_document(session, doc['id'])
    test_search_documents(session, "sample")
    test_generate_answer(session, "How can sample data improve development speed?")

if __name__ == "__main__":
    main()
