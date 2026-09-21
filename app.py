import json
import queue
import threading
from flask import Flask, Response, render_template, request, stream_with_context
from pricing import lookup

app = Flask(__name__)

@app.get("/")
def index(): return render_template("index.html")

@app.get("/api/lookup")
def search():
    query = request.args.get("query", "").strip()
    if not query:
        return Response("event: result\ndata: {\"message\": \"Enter a skin name first.\"}\n\n", mimetype="text/event-stream")
    @stream_with_context
    def events():
        messages, completed = queue.Queue(), queue.Queue()
        worker = threading.Thread(target=lambda: completed.put(lookup(query, messages.put)), daemon=True)
        worker.start()
        while worker.is_alive() or not messages.empty():
            try:
                message = messages.get(timeout=0.5)
                yield "event: log\ndata: %s\n\n" % json.dumps({"message": message})
            except queue.Empty:
                yield ": still checking\n\n"
        yield "event: result\ndata: %s\n\n" % json.dumps(completed.get())
    return Response(events(), mimetype="text/event-stream", headers={"Cache-Control": "no-cache"})

if __name__ == "__main__": app.run(debug=True, threaded=True)
