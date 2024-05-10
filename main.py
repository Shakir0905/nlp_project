import urllib3
from uuid import UUID
from fastapi import Request
from pydantic import BaseModel
from functools import lru_cache
from elasticsearch import Elasticsearch
from fastapi import FastAPI, HTTPException
from transformers import GPT2LMHeadModel, GPT2Tokenizer

# Disable insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Initialize the FastAPI app
app = FastAPI()

# Configure the Elasticsearch connection
es = Elasticsearch(
    ["https://localhost:9200"],
    basic_auth=('elastic', 'lNT53B+PKBEvx1gjoCur'),
    verify_certs=False  # Set verify_certs to True and provide ca_certs in production for security
)

# Load GPT-2 model and tokenizer
tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
model = GPT2LMHeadModel.from_pretrained("gpt2")

# Define a Pydantic model for the document
class Document(BaseModel):
    id: UUID
    text: str

@app.post("/documents/")
def create_document(document: Document):
    """Creates a document in Elasticsearch."""
    try:
        doc = document.dict()
        res = es.index(index="documents", id=str(doc['id']), document=doc)
        return {"status": res['result'], "id": str(doc['id'])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to index document: {str(e)}")

@app.get("/documents/{document_id}")
def read_document(document_id: UUID):
    """Retrieves a document by ID from Elasticsearch."""
    try:
        res = es.get(index="documents", id=str(document_id))
        if res['found']:
            return {"id": document_id, "text": res['_source']['text']}
        else:
            raise HTTPException(status_code=404, detail="Document not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve document: {str(e)}")

@app.get("/search/")
def search_documents(query: str):
    """Performs a text search on the documents in Elasticsearch."""
    try:
        search_response = es.search(
            index="documents", 
            body={"size": 3, "query": {"match": {"text": query}}}
        )
        hits = search_response['hits']['hits']
        results = [{"id": hit["_id"], "text": hit["_source"]["text"]} for hit in hits]
        return {"query": query, "results": results, "total": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@lru_cache(maxsize=100)
def generate_response(prompt):
    """Generates a response to a query using the LLM (Language Model)."""
    input_ids = tokenizer.encode(prompt, return_tensors="pt", max_length=1024, truncation=True)
    output = model.generate(input_ids, max_length=100, num_return_sequences=1, early_stopping=True)
    response = tokenizer.decode(output[0], skip_special_tokens=True)
    return response

def clean_up_response(response_text):
    """ Simple function to clean up repeated sentences to make the response more coherent. """
    seen = set()
    output = []
    for sentence in response_text.split('. '):
        if sentence not in seen:
            seen.add(sentence)
            output.append(sentence)
    return '. '.join(output)

@app.post("/generate-answer/")
async def generate_answer(request: Request):
    data = await request.json()
    query = data.get('text', '')

    # Search for documents related to the query
    search_response = es.search(
        index="documents",
        body={"size": 5, "query": {"match": {"text": query}}}
    )

    documents_text = " ".join([hit['_source']['text'] for hit in search_response['hits']['hits']])

    if documents_text:
        generated_text = generate_response(documents_text)
        cleaned_text = clean_up_response(generated_text)
        return {"query": query, "generated_answer": cleaned_text}
    else:
        return {"query": query, "generated_answer": "No relevant documents found to generate an answer."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
