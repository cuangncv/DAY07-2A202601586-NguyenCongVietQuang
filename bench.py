"""
bench.py — Script đánh giá truy xuất (Retrieval Benchmark) cho Lab 7 (K4 E-commerce)
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from dotenv import load_dotenv

from ingest import build_knowledge_base
from src.chunking import RecursiveChunker, SentenceChunker, FixedSizeChunker
from src.embeddings import _mock_embed, LocalEmbedder
from src.agent import KnowledgeBaseAgent

# 1. Load môi trường (.env)
load_dotenv(dotenv_path=Path(".env"), override=False)

provider = os.getenv("EMBEDDING_PROVIDER", "mock").lower()
if provider == "local":
    try:
        embedder = LocalEmbedder()
        print("[INFO] Sử dụng Local Multilingual Embedder (SentenceTransformers)")
    except Exception as e:
        print(f"[WARN] Không tải được LocalEmbedder ({e}), fallback sang MockEmbedder")
        embedder = _mock_embed
else:
    print("[INFO] Sử dụng Mock Embedder")
    embedder = _mock_embed

# 2. Chọn chiến lược Chunking cá nhân
# ĐÂY LÀ DÒNG BẠN CÓ THỂ THAY ĐỔI THEO STRATEGY CỦA MÌNH:
chunker = RecursiveChunker(chunk_size=400)
strategy_name = "RecursiveChunker(chunk_size=400)"

# 3. Build Vector Store từ tập dữ liệu K4 E-commerce
data_dir = "data/k4_ecommerce"
store = build_knowledge_base(data_dir, embedder, chunker=chunker)
agent = KnowledgeBaseAgent(store=store, llm_fn=lambda prompt: f"[Agent Generated Response based on Context]")

print(f"\n==================================================")
print(f"BENCHMARK RETRIEVAL — Strategy: {strategy_name}")
print(f"Tổng số chunk đã nạp: {store.get_collection_size()}")
print(f"==================================================\n")

# 4. Tải danh sách 5 Benchmark Queries từ file JSON của nhóm K4
queries_json_path = Path("data/k4_ecommerce/benchmark_queries.json")
if queries_json_path.exists():
    with open(queries_json_path, "r", encoding="utf-8") as f:
        queries = json.load(f)
else:
    queries = []

# 5. Chạy từng Query và in kết quả Benchmark
for i, item in enumerate(queries, 1):
    q_id = item.get("id", f"q{i}")
    q_text = item["query"]
    q_filter = item.get("metadata_filter")
    q_gold = item.get("gold_answer", "")

    print(f"--- QUERY #{i} [{q_id}]: {q_text} ---")
    if q_filter:
        print(f"[FILTER]: {q_filter}")
        results = store.search_with_filter(q_text, top_k=3, metadata_filter=q_filter)
    else:
        results = store.search(q_text, top_k=3)

    if results:
        top1 = results[0]
        doc_id = top1.get("metadata", {}).get("doc_id", "N/A")
        score = top1.get("score", 0.0)
        content_preview = top1.get("content", "").replace("\n", " ")[:120]
        print(f"  [Top-1 Match] Score: {score:.4f} | Doc ID: {doc_id}")
        print(f"  [Content Preview]: {content_preview}...")
    else:
        print("  [WARN] Không tìm thấy chunk nào phù hợp!")

    answer = agent.answer(q_text, top_k=3)
    print(f"  [Gold Answer]: {q_gold}\n")

print("==================================================")
print("HOÀN THÀNH RUNNING BENCHMARK CHECKPOINT 5!")
print("==================================================")
