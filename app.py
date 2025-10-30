from flask import Flask, render_template_string

app = Flask(__name__)

@app.route('/')
def home():
    return render_template_string(r"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>WELCOME TO YK TRICKS INDIA</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <link href="https://fonts.googleapis.com/css?family=Poppins:700,500,400&display=swap" rel="stylesheet" />
  <style>
    * { box-sizing: border-box; }
    body {
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
      position: relative;
      z-index: 1;
      max-width: 480px;
      margin: 40px auto 50px;
      padding: 24px;
      background: rgba(255, 255, 255, 0.08);
      border-radius: 20px;
      backdrop-filter: blur(16px);
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.37);
      border: 1px solid rgba(255, 255, 255, 0.18);
    }
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
    .premium-box:hover {
      background: linear-gradient(90deg, #ff4b2b, #ff416c);
      box-shadow: 0 8px 28px #ff416ccc;
    }
    .feature-row {
      display: flex;
      flex-direction: column;
      gap: 22px;
    }
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
    .feature-card:hover {
      box-shadow: 0 12px 48px rgba(255,71,110,0.7);
      transform: scale(1.05);
      border-color: #ff416c;
      background-color: rgba(255,255,255,0.12);
    }
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
    }
    .about-btn:hover {
      background: #ff5864;
      color: #fff;
      box-shadow: 0 8px 38px #ff5864cc;
    }
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
  <div class="container">
    <h1 class="main-title">WELCOME TO YK TRICKS INDIA</h1>
    <div class="premium-box" onclick="showFeatureModal()">EXPLORE PREMIUM FEATURES</div>
    <div class="feature-row">
      <div class="feature-card fb-card">FACEBOOK TOOLS</div>
      <div class="feature-card ig-card">INSTAGRAM TOOLS</div>
      <div class="feature-card wa-card">WHATSAPP TOOLS</div>
    </div>
    <button class="about-btn" onclick="showAboutModal()">ABOUT SYSTEM</button>
  </div>

  <!-- PREMIUM FEATURES MODAL -->
  <div id="modal" class="modal" tabindex="-1" aria-hidden="true" role="dialog" aria-modal="true">
    <div class="modal-content" role="document">
      <button class="close-btn" aria-label="Close modal" onclick="closeFeatureModal()">×</button>
      <div class="modal-title">PREMIUM FEATURES</div>
      <div class="feature-list-grid">
        <div class="modal-list-card" onclick="window.open('https://example.com/instagram-bot','_blank')">
          <div class="list-card-bg" style="background-image:url('https://i.imgur.com/ZYUdbZC.jpg');"></div>
          <div class="list-card-content">
            <div class="list-card-title">Instagram Chat Bot</div>
            <div class="list-card-desc">Automate Instagram chats, DMs, replies, and more.</div>
          </div>
        </div>
        <div class="modal-list-card" onclick="window.open('https://example.com/whatsapp-bot','_blank')">
          <div class="list-card-bg" style="background-image:url('https://cdn.pixabay.com/photo/2017/01/17/15/28/whatsapp-1984586_1280.png');"></div>
          <div class="list-card-content">
            <div class="list-card-title">WhatsApp Chat Bot</div>
            <div class="list-card-desc">Smart automation for WhatsApp chats and customers.</div>
          </div>
        </div>
        <div class="modal-list-card" onclick="window.open('https://example.com/telegram-bot','_blank')">
          <div class="list-card-bg" style="background-image:url('https://i.imgur.com/AJjoE9t.png');"></div>
          <div class="list-card-content">
            <div class="list-card-title">Telegram Chat Bot</div>
            <div class="list-card-desc">Broadcasts, replies, group management on Telegram.</div>
          </div>
        </div>
        <div class="modal-list-card" onclick="window.open('https://example.com/facebook-bot','_blank')">
          <div class="list-card-bg" style="background-image:url('https://cdn.pixabay.com/photo/2016/04/15/11/46/facebook-1327866_1280.png');"></div>
          <div class="list-card-content">
            <div class="list-card-title">Facebook Chat Bot</div>
            <div class="list-card-desc">Chat and automation for Facebook pages and groups.</div>
          </div>
        </div>
        <div class="modal-list-card" onclick="window.open('https://example.com/facebook-automation','_blank')">
          <div class="list-card-bg" style="background-image:url('https://i.imgur.com/EUj4c1H.jpg');"></div>
          <div class="list-card-content">
            <div class="list-card-title">Facebook Automation</div>
            <div class="list-card-desc">Auto-like, group post, comment scheduling tools.</div>
          </div>
        </div>
        <div class="modal-list-card" onclick="window.open('https://example.com/instagram-automation','_blank')">
          <div class="list-card-bg" style="background-image:url('https://i.imgur.com/vKraKOK.jpg');"></div>
          <div class="list-card-content">
            <div class="list-card-title">Instagram Automation</div>
            <div class="list-card-desc">Auto-follow, comment, story view and more.</div>
          </div>
        </div>
        <div class="modal-list-card" onclick="window.open('https://example.com/instagram-recovery','_blank')">
          <div class="list-card-bg" style="background-image:url('https://i.imgur.com/CKUfYYS.jpg');"></div>
          <div class="list-card-content">
            <div class="list-card-title">Instagram Account Recovery</div>
            <div class="list-card-desc">Fast Insta account recovery with full support.</div>
          </div>
        </div>
        <div class="modal-list-card" onclick="window.open('https://example.com/whatsapp-automation','_blank')">
          <div class="list-card-bg" style="background-image:url('https://cdn.pixabay.com/photo/2017/01/17/15/28/whatsapp-1984586_1280.png');"></div>
          <div class="list-card-content">
            <div class="list-card-title">WhatsApp Automation</div>
            <div class="list-card-desc">Bulk messages, scheduled text, replies, and more.</div>
          </div>
        </div>
        <div class="modal-list-card" onclick="window.open('https://example.com/telegram-automation','_blank')">
          <div class="list-card-bg" style="background-image:url('https://i.imgur.com/AJjoE9t.png');"></div>
          <div class="list-card-content">
            <div class="list-card-title">Telegram Automation</div>
            <div class="list-card-desc">Automate posting, group and user management.</div>
          </div>
        </div>
        <div class="modal-list-card" onclick="window.open('https://example.com/facebook-comment','_blank')">
          <div class="list-card-bg" style="background-image:url('https://cdn.pixabay.com/photo/2016/11/19/14/00/facebook-1834007_1280.jpg');"></div>
          <div class="list-card-content">
            <div class="list-card-title">Facebook Post Comment</div>
            <div class="list-card-desc">Auto-comment and reply for posts/groups.</div>
          </div>
        </div>
        <div class="modal-list-card" onclick="window.open('https://example.com/facebook-chat','_blank')">
          <div class="list-card-bg" style="background-image:url('https://cdn.pixabay.com/photo/2016/04/24/17/52/facebook-1349727_1280.png');"></div>
          <div class="list-card-content">
            <div class="list-card-title">Facebook Automation Chat</div>
            <div class="list-card-desc">Automate group chat and inbox responses fast.</div>
          </div>
        </div>
        <div class="modal-list-card" onclick="window.open('https://example.com/instagram-group','_blank')">
          <div class="list-card-bg" style="background-image:url('https://i.imgur.com/vKraKOK.jpg');"></div>
          <div class="list-card-content">
            <div class="list-card-title">Instagram Group Chat Automation</div>
            <div class="list-card-desc">Auto-moderate and engage Instagram groups.</div>
          </div>
        </div>
        <div class="modal-list-card" onclick="window.open('https://example.com/instagram-dm','_blank')">
          <div class="list-card-bg" style="background-image:url('https://i.imgur.com/tKQw9Id.jpg');"></div>
          <div class="list-card-content">
            <div class="list-card-title">Instagram Inbox DM</div>
            <div class="list-card-desc">Automate Instagram DMs for outreach/support.</div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- ABOUT MODAL -->
  <div id="aboutModal" class="about-modal" tabindex="-1" aria-hidden="true" role="dialog" aria-modal="true">
    <div class="about-modal-content" role="document">
      <button class="close-btn" aria-label="Close modal" onclick="closeAboutModal()">×</button>
      <h2 style="color:#ff6470; text-align:center; margin-bottom: 22px; font-weight: 900;">ABOUT SYSTEM</h2>
      <div style="text-align:center; font-size:1.05rem; line-height:1.5; color:#eee; margin-bottom: 18px;">
        Premium tool admin panel Version 2.0. Built for fast device linking, automated tasks, group management, chat automation, and more.
      </div>
      <div style="color:#ff7a85; font-weight: 600; text-align:center; line-height: 1.4; font-size: 1rem;">
        Developed by: <b>YK Tricks India</b><br />
        Contact: <b>yktricksindia@gmail.com</b><br />
        WhatsApp: <b>+91-99XXXXXXX</b><br />
        Instagram: <b>@yktricksindia</b><br />
        Website: <b>yktricksindia.com</b>
      </div>
    </div>
  </div>

  <script>
    function showFeatureModal() {
      const modal = document.getElementById('modal');
      modal.classList.add('show');
      document.body.style.overflowY = "hidden";
    }
    function closeFeatureModal() {
      const modal = document.getElementById('modal');
      modal.classList.remove('show');
      document.body.style.overflowY = "auto";
    }
    function showAboutModal() {
      const modal = document.getElementById('aboutModal');
      modal.classList.add('show');
      document.body.style.overflowY = "hidden";
    }
    function closeAboutModal() {
      const modal = document.getElementById('aboutModal');
      modal.classList.remove('show');
      document.body.style.overflowY = "auto";
    }

    // Accessibility: close modals on ESC key
    document.addEventListener('keydown', function(e) {
      if (e.key === "Escape") {
        closeFeatureModal();
        closeAboutModal();
      }
    });
  </script>
</body>
</html>
""")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    
