import csv
import io
import os
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import networkx as nx
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, Response, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

BASE = Path(__file__).resolve().parent
CSV_PATH = BASE / 'Edges.csv'
IMAGE_PATH = BASE / 'SachCayThuocGSDoTatLoi.jpg'
DEFAULT_ROWS = [
    ('Nhục quế', 'Trị', 'Tỳ vị hư hàn'),
    ('Nhục quế', 'Chữa_Triệu_Chứng', 'Đau bụng'),
    ('Phụ tử', 'Trị', 'Hàn thấp bại liệt'),
    ('Phụ tử', 'Chữa_Triệu_Chứng', 'Ho hen'),
]

def read_rows():
    if not CSV_PATH.exists():
        return [{'Head': h, 'Predicate': p, 'Tail': t} for h, p, t in DEFAULT_ROWS]
    with CSV_PATH.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or not {'Head', 'Predicate', 'Tail'}.issubset(reader.fieldnames):
            raise ValueError('Edges.csv phải có 3 cột Head, Predicate, Tail')
        return [{key: (row.get(key) or '').strip() for key in ('Head', 'Predicate', 'Tail')}
                for row in reader if row.get('Head') and row.get('Tail')]

def graph_from_rows(rows):
    graph = nx.Graph()
    predicates = {}
    for row in rows:
        h, t, p = row['Head'], row['Tail'], row['Predicate']
        graph.add_edge(h, t)
        predicates[(h, t)] = p
        predicates[(t, h)] = p
    return graph, predicates

app = FastAPI(title='Đồ thị tri thức cây thuốc - GS.TS. Đỗ Tất Lợi')
app.mount('/static', StaticFiles(directory=str(BASE / 'static')), name='static')
templates = Jinja2Templates(directory=str(BASE / 'templates'))

@app.get('/', response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, 'index.html', {'file_name': CSV_PATH.name})

@app.get('/api/edges')
def edges(head: str = 'All', tail: str = 'All'):
    try:
        rows = read_rows()
    except Exception as e:
        raise HTTPException(400, str(e))
    filtered = [r for r in rows if (not head or head.lower() == 'all' or r['Head'] == head)
                and (not tail or tail.lower() == 'all' or r['Tail'] == tail)]
    return {'rows': filtered, 'total': len(rows), 'heads': sorted({r['Head'] for r in rows}),
            'tails': sorted({r['Tail'] for r in rows}), 'file': CSV_PATH.name}

@app.get('/api/neighbours')
def neighbours(source: str = Query(min_length=1)):
    try:
        graph, predicates = graph_from_rows(read_rows())
    except Exception as e:
        raise HTTPException(400, str(e))
    if source not in graph:
        raise HTTPException(404, f"Node '{source}' không tồn tại trong đồ thị!")
    adjacent = list(graph.neighbors(source))
    return {'source': source, 'neighbours': [{'node': n, 'predicate': predicates.get((source, n), '')} for n in adjacent]}

@app.get('/api/neighbours/image')
def neighbours_image(source: str = Query(min_length=1)):
    try:
        graph, predicates = graph_from_rows(read_rows())
    except Exception as e:
        raise HTTPException(400, str(e))
    if source not in graph:
        raise HTTPException(404, f"Node '{source}' không tồn tại trong đồ thị!")
    sub = graph.subgraph([source, *graph.neighbors(source)])
    fig, ax = plt.subplots(figsize=(9, 6))
    try:
        pos = nx.spring_layout(sub, seed=42)
        nx.draw(sub, pos, ax=ax, with_labels=True,
                node_color=['orange' if n == source else 'lightblue' for n in sub.nodes],
                node_size=1200, font_size=9)
        nx.draw_networkx_edge_labels(sub, pos, ax=ax,
                                    edge_labels={(u, v): predicates.get((u, v), '') for u, v in sub.edges},
                                    font_size=8)
        fig.tight_layout()
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=130, bbox_inches='tight')
        return Response(buffer.getvalue(), media_type='image/png')
    finally:
        plt.close(fig)

@app.get('/api/paths')
def paths(k: int = Query(2, ge=0, le=8), limit: int = Query(3000, ge=1, le=10000)):
    try:
        graph, predicates = graph_from_rows(read_rows())
    except Exception as e:
        raise HTTPException(400, str(e))
    # Đồ thị vô hướng: loại bỏ đường đi trùng nhau khi đảo chiều.
    found = set()
    truncated = False
    for node in graph.nodes:
        queue = [[node]]
        while queue:
            path = queue.pop(0)
            if len(path) == k + 1:
                candidate = tuple(path)
                reverse = tuple(reversed(candidate))
                found.add(min(candidate, reverse))
                if len(found) >= limit:
                    truncated = True
                    break
                continue
            for neighbor in graph.neighbors(path[-1]):
                if neighbor not in path:
                    queue.append(path + [neighbor])
        if truncated:
            break
    results = []
    for path in sorted(found):
        parts = [path[0]]
        for u, v in zip(path, path[1:]):
            parts.append(f"--[{predicates.get((u, v), '')}]--> {v}")
        results.append(' '.join(parts))
    return {'k': k, 'paths': results, 'count': len(results), 'truncated': truncated}

@app.get('/api/book-image')
def book_image():
    if not IMAGE_PATH.is_file():
        raise HTTPException(404, 'Chưa có file SachCayThuocGSDoTatLoi.jpg trong project')
    return FileResponse(IMAGE_PATH, media_type='image/jpeg')
