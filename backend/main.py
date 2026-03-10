# ============================================================
#  StyleThread – RAG Chatbot Backend
#  Stack: FastAPI + LangChain + ChromaDB + Ollama (llama3)
# ============================================================

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import os

# LangChain pieces
from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.docstore.document import Document

# ──────────────────────────────────────────────────────────────
# 1.  YOUR STORE KNOWLEDGE BASE
#     ↓↓ Edit this section to describe YOUR products ↓↓
# ──────────────────────────────────────────────────────────────
STORE_KNOWLEDGE = """
STORE NAME: StyleThread Clothing Store

ABOUT US:
StyleThread is a premium clothing store specializing in modern, sustainable fashion for men and women.
We focus on tim
AI overview
AI Overvieweless pieces that combine comfort with elegance.

WOMEN'S COLLECTION:

1. Floral Summer Dress
   - Price: $89
   - Sizes: XS, S, M, L, XL
   - Colors: Rose Pink, Sky Blue, Sage Green
   - Fabric: 100% Cotton
   - Care: Machine wash cold
   - Description: A lightweight, breezy dress perfect for summer outings. Features a floral print, adjustable straps, and a midi length.

2. Classic White Button-Down Shirt
   - Price: $65
   - Sizes: XS, S, M, L, XL, XXL
   - Colors: White, Ivory, Light Blue
   - Fabric: 95% Cotton, 5% Elastane
   - Description: A wardrobe staple with a relaxed fit. Can be worn tucked or untucked. Great for office or casual settings.

3. High-Waist Straight Jeans
   - Price: $95
   - Sizes: 24 to 34 waist
   - Colors: Dark Indigo, Stone Wash, Black
   - Fabric: 98% Cotton, 2% Elastane
   - Description: Flattering high-rise cut with a straight leg. Durable denim with slight stretch for all-day comfort.

4. Cashmere Blend Sweater
   - Price: $145
   - Sizes: S, M, L, XL
   - Colors: Camel, Cream, Dusty Rose, Navy
   - Fabric: 70% Cashmere, 30% Merino Wool
   - Care: Dry clean only
   - Description: Ultra-soft, luxurious sweater for cooler months. Ribbed cuffs and hem, relaxed fit.

5. Linen Wide-Leg Trousers
   - Price: $110
   - Sizes: XS to XL
   - Colors: Sand, White, Terracotta
   - Fabric: 100% Linen
   - Description: Elegant wide-leg silhouette with a pleated front. Lightweight and breathable, ideal for summer.

MEN'S COLLECTION:

6. Slim Fit Chinos
   - Price: $85
   - Sizes: 28 to 38 waist, lengths 30/32/34
   - Colors: Khaki, Navy, Olive, Stone
   - Fabric: 97% Cotton, 3% Elastane
   - Description: Versatile slim-fit chinos suitable for smart-casual to business settings. Flat front, side pockets.

7. Oxford Button-Down Shirt
   - Price: $75
   - Sizes: S, M, L, XL, XXL
   - Colors: White, Blue, Pink, Green
   - Fabric: 100% Oxford Cotton
   - Description: Classic button-down collar shirt. Slightly relaxed fit, perfect for layering or wearing alone.

8. Premium Wool Blazer
   - Price: $220
   - Sizes: 36 to 48 (chest)
   - Colors: Charcoal, Navy, Camel
   - Fabric: 80% Wool, 20% Polyester
   - Care: Dry clean
   - Description: Tailored single-breasted blazer with notch lapels, two button front, and a ticket pocket.

9. Crew Neck Cotton Tee
   - Price: $35
   - Sizes: XS to XXL
   - Colors: White, Black, Grey, Navy, Olive, Rust
   - Fabric: 100% Combed Cotton
   - Description: Essential everyday tee with a clean silhouette. Pre-shrunk, durable, and incredibly soft.

10. Merino Wool Turtleneck
    - Price: $120
    - Sizes: S, M, L, XL
    - Colors: Cream, Charcoal, Forest Green, Burgundy
    - Fabric: 100% Merino Wool
    - Description: Slim-fitting turtleneck with temperature-regulating merino. Seamless collar, elegant finish.

SIZING GUIDE:
- XS: Bust 32", Waist 24", Hips 35"
- S:  Bust 34", Waist 26", Hips 37"
- M:  Bust 36", Waist 28", Hips 39"
- L:  Bust 38", Waist 30", Hips 41"
- XL: Bust 40", Waist 32", Hips 43"
- XXL: Bust 42", Waist 34", Hips 45"

SHIPPING & RETURNS:
- Free shipping on orders over $100
- Standard shipping: 5-7 business days ($8.99)
- Express shipping: 2-3 business days ($14.99)
- Free returns within 30 days (items must be unworn with tags)

PAYMENT:
- We accept Visa, MasterCard, American Express, PayPal, and Apple Pay.
- Installment payment available through Klarna (0% interest for 4 payments).

CARE TIPS:
- Most cotton items: Machine wash cold, tumble dry low
- Linen: Hand wash or gentle cycle, air dry to prevent shrinkage
- Wool/Cashmere: Dry clean or hand wash in cold water with wool detergent
- Always check the individual care label on each garment

STYLING TIPS:
- Pair the high-waist jeans with the classic white button-down for a chic casual look
- The linen trousers and cashmere sweater make a perfect smart-casual autumn outfit
- Layer the Oxford shirt under the wool blazer for a polished business look
- The floral summer dress pairs beautifully with white sneakers or sandals

STORE HOURS:
- Monday–Friday: 9 AM – 8 PM
- Saturday: 10 AM – 7 PM
- Sunday: 11 AM – 5 PM

CONTACT:
- Email: hello@stylethread.com
- Phone: +1 (555) 234-5678
- Address: 42 Fashion Avenue, New York, NY 10001
"""

# ──────────────────────────────────────────────────────────────
# 2.  BUILD THE VECTOR STORE (RAG knowledge index)
#     This runs once at startup and stores embeddings in memory
# ──────────────────────────────────────────────────────────────
def build_vector_store():
    """
    RAG Step 1 & 2:
      - Split the store knowledge into small chunks
      - Embed each chunk using Ollama's embedding model
      - Store embeddings in ChromaDB (in-memory vector database)
    """
    print("📚 Building knowledge base (RAG index)...")

    # Split text into overlapping chunks so context isn't lost at boundaries
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,       # characters per chunk
        chunk_overlap=80,     # overlap between chunks
    )
    chunks = splitter.split_text(STORE_KNOWLEDGE)

    # Wrap each chunk as a LangChain Document   
    docs = [Document(page_content=chunk) for chunk in chunks]

    # Create embeddings using Ollama's nomic-embed-text model
    embeddings = OllamaEmbeddings(model="nomic-embed-text")

    # Store all embeddings in ChromaDB (an in-memory vector database)
    vector_store = Chroma.from_documents(docs, embeddings)

    print(f"✅ Knowledge base ready with {len(docs)} chunks.")
    return vector_store


# ──────────────────────────────────────────────────────────────
# 3.  FASTAPI APPLICATION SETUP
# ──────────────────────────────────────────────────────────────
app = FastAPI(title="StyleThread Chat API")

# Allow requests from your React frontend (running on localhost:5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Build the vector store when the server starts
vector_store = build_vector_store()

# Connect to your local Llama 3 model via Ollama
llm = Ollama(
    model="llama3",
    temperature=0.7,      # 0 = deterministic, 1 = creative
    num_ctx=4096,         # context window size
)

# System prompt that shapes the assistant's personality
SYSTEM_PROMPT = """You are a friendly, knowledgeable fashion assistant for StyleThread clothing store.
Your job is to help customers find the perfect clothing items, answer questions about sizes, fabrics,
prices, shipping, and styling. Be warm, enthusiastic, and helpful.
Only answer questions based on the store information provided to you.
If you don't know the answer, politely say so and suggest contacting the store directly."""


# ──────────────────────────────────────────────────────────────
# 4.  REQUEST / RESPONSE MODELS
# ──────────────────────────────────────────────────────────────
class ChatMessage(BaseModel):
    role: str    # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []


# ──────────────────────────────────────────────────────────────
# 5.  CHAT ENDPOINT  (the one React calls)
# ──────────────────────────────────────────────────────────────
@app.post("/chat")
async def chat(request: ChatRequest):
    """
    RAG Pipeline on every message:
      1. Embed the user's question
      2. Search vector store for the most relevant store knowledge
      3. Inject that context into the prompt
      4. Send to Llama 3 and return the answer
    """
    try:
        # --- RAG Step 3: Retrieve relevant context ---
        retriever = vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 4}   # return top-4 most relevant chunks
        )
        relevant_docs = retriever.get_relevant_documents(request.message)
        context = "\n\n".join([doc.page_content for doc in relevant_docs])

        # --- Build conversation history string ---
        history_str = ""
        for msg in request.history[-6:]:   # only keep last 6 messages
            prefix = "Customer" if msg.role == "user" else "Assistant"
            history_str += f"{prefix}: {msg.content}\n"

        # --- Construct the full prompt ---
        full_prompt = f"""{SYSTEM_PROMPT}

--- STORE KNOWLEDGE (use this to answer) ---
{context}
--- END STORE KNOWLEDGE ---

--- CONVERSATION HISTORY ---
{history_str}
--- END HISTORY ---

Customer: {request.message}
Assistant:"""

        # --- RAG Step 4: Send to Llama 3 ---
        response = llm.invoke(full_prompt)

        return {"response": response.strip()}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────────────────────
# 6.  HEALTH CHECK ENDPOINT
# ──────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "model": "llama3", "store": "StyleThread"}


# ──────────────────────────────────────────────────────────────
# 7.  RUN THE SERVER
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)