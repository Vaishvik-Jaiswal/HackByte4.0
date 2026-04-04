from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import os
from app.graph.workflow import build_graph

app = FastAPI(title="Email Classification Agent API", description="API for processing emails through classification and summarization agents")

# Initialize the graph
graph = build_graph()

class EmailRequest(BaseModel):
    id: str
    content: str

class EmailResponse(BaseModel):
    id: str
    content: str
    category: str
    summary: str
    suggested_tone: str
    tone_reason: str
    reply: str

@app.post("/process-email", response_model=EmailResponse)
async def process_email(email: EmailRequest):
    """
    Process an email through the agent workflow.
    Returns classification, summary, and generated reply.
    """
    try:
        result = graph.invoke({"email": {"id": email.id, "content": email.content}})
        return EmailResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing email: {str(e)}")

@app.get("/results/{email_id}")
async def get_result(email_id: str):
    """
    Get the stored results for a processed email.
    """
    output_file = os.path.join("outputs", f"{email_id}.json")
    if not os.path.exists(output_file):
        raise HTTPException(status_code=404, detail="Email result not found")

    try:
        with open(output_file, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading result: {str(e)}")

@app.get("/results")
async def list_results():
    """
    List all processed email IDs.
    """
    if not os.path.exists("outputs"):
        return {"emails": []}

    try:
        files = os.listdir("outputs")
        email_ids = [f.replace(".json", "") for f in files if f.endswith(".json")]
        return {"emails": email_ids}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing results: {str(e)}")

@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy", "message": "Email Classification Agent API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.0", port=8000)