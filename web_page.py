"""
HTML/CSS/JS template for the web app (index.py). Design only: every form field name,
route and template variable is the same as before, so behaviour is unchanged.

Design notes:
  * Dark by default, with a light theme toggle (remembered in this browser).
  * Motion: an animated iridescent "orb", word-by-word headline reveal, cards that fade
    up as they scroll into view, a cursor spotlight on cards, magnetic primary button,
    count-up metrics. All motion is switched off for people who prefer reduced motion.
  * Sound: tiny click/toggle/hover sounds synthesised with the Web Audio API (no audio
    files). On/off switch in the top bar, remembered in this browser.
"""

PAGE = r"""<!doctype html>
<html lang="en" data-theme="dark"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sprinto Outreach</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<script>
  // Apply the saved theme before the page paints (avoids a flash).
  try { var t = localStorage.getItem('theme'); if (t) document.documentElement.dataset.theme = t; } catch (e) {}
</script>
<style>
:root{
  --font: Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
  --mono: "JetBrains Mono", ui-monospace, SFMono-Regular, Consolas, monospace;
  --ease: cubic-bezier(.2,.8,.2,1); --spring: cubic-bezier(.34,1.56,.64,1);
  --r: 18px;
}
html[data-theme="dark"]{
  --bg:#0b0b0d; --bg2:#121215; --card:#141418; --card2:#1a1a1f; --ink:#f4f4f6; --mute:#8b8b95; --faint:#5a5a63;
  --line:rgba(255,255,255,.08); --line2:rgba(255,255,255,.14); --glass:rgba(20,20,24,.72);
  --acc:#9db4ff; --acc2:#c9a7ff; --ok:#6ee7a8; --okbg:rgba(110,231,168,.10); --bad:#ff8a8a; --badbg:rgba(255,138,138,.10);
  --warn:#ffd36e; --warnbg:rgba(255,211,110,.09); --shadow:0 10px 40px rgba(0,0,0,.45); --spot:rgba(157,180,255,.10);
}
html[data-theme="light"]{
  --bg:#f6f6f4; --bg2:#ffffff; --card:#ffffff; --card2:#f2f2ef; --ink:#121214; --mute:#6f6f78; --faint:#a3a3ab;
  --line:rgba(0,0,0,.07); --line2:rgba(0,0,0,.13); --glass:rgba(255,255,255,.75);
  --acc:#3d5af1; --acc2:#8a4dff; --ok:#13804a; --okbg:rgba(19,128,74,.08); --bad:#c02626; --badbg:rgba(192,38,38,.07);
  --warn:#9a6200; --warnbg:rgba(154,98,0,.08); --shadow:0 10px 40px rgba(20,20,40,.10); --spot:rgba(61,90,241,.07);
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 var(--font);-webkit-font-smoothing:antialiased;
  transition:background .5s var(--ease),color .5s var(--ease);overflow-x:hidden}
a{color:var(--ink);text-decoration:none}
::selection{background:var(--acc);color:#000}
code,pre,.mono{font-family:var(--mono)}
.grain{position:fixed;inset:0;pointer-events:none;z-index:0;opacity:.035;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")}

/* ---------- floating top bar ---------- */
.bar{position:fixed;top:16px;left:50%;transform:translateX(-50%);z-index:50;display:flex;gap:8px;align-items:center;
  animation:drop .8s var(--spring) both}
.pill{display:flex;align-items:center;gap:4px;padding:5px;border-radius:999px;background:var(--glass);
  border:1px solid var(--line);backdrop-filter:blur(16px) saturate(1.4);-webkit-backdrop-filter:blur(16px) saturate(1.4);box-shadow:var(--shadow)}
.brand{display:flex;align-items:center;gap:9px;padding:6px 14px 6px 8px;font-weight:600;font-size:14px;white-space:nowrap}
.brand i{width:22px;height:22px;border-radius:50%;background:conic-gradient(from 0deg,var(--acc),var(--acc2),#ffb3c7,var(--acc));
  animation:spin 6s linear infinite;box-shadow:0 0 18px var(--acc)}
.nav a{white-space:nowrap;padding:7px 13px;border-radius:999px;font-size:13.5px;color:var(--mute);position:relative;transition:color .25s,background .25s}
.nav a:hover,.nav a.on{color:var(--ink);background:var(--card2)}
.icon{width:38px;height:38px;border-radius:50%;display:grid;place-items:center;border:0;background:transparent;color:var(--ink);
  cursor:pointer;transition:background .25s,transform .3s var(--spring)}
.icon:hover{background:var(--card2);transform:scale(1.08)} .icon:active{transform:scale(.92)}
.icon svg{width:18px;height:18px}
.seg{white-space:nowrap;display:flex;align-items:center;gap:2px;font-size:12.5px;color:var(--mute);padding-left:10px}
.seg button{border:0;background:transparent;color:var(--mute);font:inherit;padding:6px 11px;border-radius:999px;cursor:pointer;transition:all .3s var(--ease)}
.seg button[aria-pressed="true"]{background:var(--ink);color:var(--bg)}
.chips{display:flex;gap:6px;flex-wrap:wrap;margin:22px 0 4px}
.chip{display:flex;align-items:center;gap:7px;padding:6px 12px;border-radius:999px;background:var(--glass);border:1px solid var(--line);
  backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);font-size:12px;color:var(--mute);white-space:nowrap}
.chip b{color:var(--ink);font-weight:500}
.dot{width:7px;height:7px;border-radius:50%;background:var(--warn);position:relative}
.dot.live{background:var(--ok)} .dot.live::after{content:"";position:absolute;inset:-4px;border-radius:50%;border:1px solid var(--ok);animation:ping 2s var(--ease) infinite}

/* ---------- layout ---------- */
main{position:relative;z-index:1;max-width:1080px;margin:0 auto;padding:110px 16px 120px}
.hero{display:grid;grid-template-columns:1.15fr .85fr;gap:32px;align-items:center;min-height:52vh;margin-bottom:28px}
h1{font-size:clamp(34px,5.4vw,60px);line-height:1.04;letter-spacing:-.035em;font-weight:600;margin:0 0 18px}
h1 .w{display:inline-block;opacity:0;transform:translateY(.45em) rotate(2deg);filter:blur(6px);animation:word .9s var(--ease) forwards}
h1 .soft{color:var(--faint)}
.lede{color:var(--mute);font-size:16.5px;max-width:520px;margin:0}
.eyebrow{display:inline-flex;align-items:center;gap:10px;font-size:13px;color:var(--mute);margin-bottom:14px}
.num{display:inline-grid;place-items:center;min-width:34px;height:26px;padding:0 9px;border-radius:999px;background:var(--card2);
  color:var(--ink);font:500 12px var(--mono);border:1px solid var(--line)}

/* ---------- orb (motion graphic) ---------- */
.orbwrap{position:relative;aspect-ratio:1;max-width:360px;width:100%;justify-self:center;perspective:800px}
.orb{position:absolute;inset:8%;border-radius:42% 58% 63% 37% / 41% 44% 56% 59%;
  background:
    radial-gradient(70% 55% at 32% 28%,rgba(255,255,255,.85),rgba(255,255,255,0) 60%),
    radial-gradient(85% 75% at 68% 78%,#07070d 18%,rgba(7,7,13,0) 62%),
    linear-gradient(160deg,#e7e9f5 0%,#9aa0bd 38%,#3b3d55 62%,#cfd3ea 100%);
  box-shadow:inset -18px -26px 60px rgba(0,0,0,.45),inset 14px 18px 40px rgba(255,255,255,.55),0 40px 90px -20px rgba(120,130,255,.35);
  animation:morph 14s var(--ease) infinite alternate,float 7s ease-in-out infinite;transform:rotateX(var(--rx,0deg)) rotateY(var(--ry,0deg));
  transition:transform .6s var(--ease)}
.orb::before{content:"";position:absolute;inset:-2px;border-radius:inherit;padding:3px;
  background:conic-gradient(from var(--a,0deg),transparent 0 55%,#ff9a62,#ffe66b,#6bd5ff,#a07bff,transparent 85%);
  -webkit-mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);-webkit-mask-composite:xor;mask-composite:exclude;
  filter:blur(1.5px);animation:hue 5s linear infinite}
.orb::after{content:"";position:absolute;inset:18% 30% 46% 18%;border-radius:50%;background:rgba(255,255,255,.55);filter:blur(18px)}
.orbshadow{position:absolute;left:18%;right:18%;bottom:-2%;height:12%;border-radius:50%;background:radial-gradient(rgba(0,0,0,.6),transparent 70%);
  filter:blur(8px);animation:shadow 7s ease-in-out infinite}
@property --a{syntax:"<angle>";initial-value:0deg;inherits:false}

/* ---------- cards ---------- */
.card{position:relative;background:var(--card);border:1px solid var(--line);border-radius:var(--r);padding:22px 22px;margin:0 0 18px;
  overflow:hidden;transition:border-color .35s,transform .45s var(--ease),box-shadow .45s var(--ease)}
.card::before{content:"";position:absolute;inset:0;pointer-events:none;opacity:0;transition:opacity .4s;
  background:radial-gradient(420px circle at var(--mx,50%) var(--my,50%),var(--spot),transparent 60%)}
.card:hover{border-color:var(--line2);box-shadow:var(--shadow)} .card:hover::before{opacity:1}
.card h2{font-size:19px;letter-spacing:-.01em;margin:0 0 14px;font-weight:600;display:flex;align-items:center;gap:12px}
.card h3{font-size:15px;margin:18px 0 10px;font-weight:600}
.mute{color:var(--mute);font-size:13.5px}
.reveal{opacity:0;transform:translateY(26px) scale(.985);transition:opacity .9s var(--ease),transform .9s var(--ease)}
.reveal.in{opacity:1;transform:none}

/* ---------- form ---------- */
.segctl{display:inline-flex;background:var(--card2);border:1px solid var(--line);border-radius:999px;padding:4px;gap:2px;margin-bottom:16px;position:relative}
.segctl input{position:absolute;opacity:0;pointer-events:none}
.segctl label{padding:8px 16px;border-radius:999px;cursor:pointer;font-size:13.5px;color:var(--mute);transition:all .35s var(--ease);user-select:none}
.segctl input:checked+label{background:var(--ink);color:var(--bg);box-shadow:0 4px 14px rgba(0,0,0,.25)}
.field{margin:0 0 14px}
.field>span{display:block;font-size:12.5px;color:var(--mute);margin-bottom:6px}
input[type=url],input[type=password],select{width:100%;padding:13px 15px;border:1px solid var(--line2);border-radius:12px;background:var(--bg2);
  color:var(--ink);font:inherit;outline:none;transition:border-color .25s,box-shadow .25s,transform .25s var(--ease);appearance:none;-webkit-appearance:none}
select{background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%238b8b95' stroke-width='1.6' fill='none'/%3E%3C/svg%3E");
  background-repeat:no-repeat;background-position:right 15px center;padding-right:40px}
input:focus,select:focus{border-color:var(--acc);box-shadow:0 0 0 4px color-mix(in srgb,var(--acc) 22%,transparent)}
.hide{display:none!important}
.toggle{display:flex;align-items:flex-start;gap:12px;margin:12px 0;cursor:pointer;font-size:14px;color:var(--ink)}
.toggle input{appearance:none;-webkit-appearance:none;flex:0 0 auto;width:38px;height:22px;border-radius:999px;background:var(--card2);
  border:1px solid var(--line2);position:relative;cursor:pointer;transition:background .3s var(--ease);margin:1px 0 0}
.toggle input::after{content:"";position:absolute;top:2px;left:2px;width:16px;height:16px;border-radius:50%;background:var(--mute);
  transition:transform .4s var(--spring),background .3s}
.toggle input:checked{background:var(--acc)} .toggle input:checked::after{transform:translateX(16px);background:#fff}
.toggle small{display:block;color:var(--mute);font-size:12.5px}
.btn{position:relative;display:inline-flex;align-items:center;gap:10px;border:0;border-radius:999px;padding:14px 24px;font:600 15px var(--font);
  cursor:pointer;color:var(--bg);background:var(--ink);overflow:hidden;transition:transform .35s var(--spring),box-shadow .35s;
  box-shadow:0 8px 30px -8px color-mix(in srgb,var(--acc) 60%,transparent)}
.btn::after{content:"";position:absolute;inset:0;background:linear-gradient(110deg,transparent 30%,rgba(255,255,255,.45) 50%,transparent 70%);
  transform:translateX(-120%);transition:transform .8s var(--ease)}
.btn:hover::after{transform:translateX(120%)} .btn:active{transform:scale(.96)!important}
.btn .arr{transition:transform .35s var(--spring)} .btn:hover .arr{transform:translateX(4px)}
.btn[disabled]{opacity:.6;cursor:progress}
.ghost{background:transparent;color:var(--ink);border:1px solid var(--line2);box-shadow:none}

/* ---------- results ---------- */
.status{border-radius:var(--r);padding:26px;margin-bottom:18px;border:1px solid var(--line);position:relative;overflow:hidden}
.status .big{font-size:clamp(30px,5vw,48px);font-weight:700;letter-spacing:-.03em;line-height:1}
.status .sum{color:var(--mute);margin-top:8px}
.status.ok{background:linear-gradient(135deg,var(--okbg),transparent 70%)} .status.ok .big{color:var(--ok)}
.status.bad{background:linear-gradient(135deg,var(--badbg),transparent 70%)} .status.bad .big{color:var(--bad)}
.status.warn{background:linear-gradient(135deg,var(--warnbg),transparent 70%)} .status.warn .big{color:var(--warn)}
.status .rank{display:inline-grid;place-items:center;width:46px;height:46px;border-radius:14px;margin-left:12px;vertical-align:middle;
  font-size:22px;background:var(--card2);color:var(--ink);border:1px solid var(--line2);animation:pop .7s .4s var(--spring) both}
.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-top:20px}
.metric{background:var(--card2);border:1px solid var(--line);border-radius:14px;padding:12px 14px;transition:transform .35s var(--spring)}
.metric:hover{transform:translateY(-3px)}
.metric>span{display:block;font-size:12px;color:var(--mute)} .metric b{font-size:20px;font-weight:600;letter-spacing:-.01em}
.box{padding:11px 14px;border-radius:12px;margin:8px 0;font-size:14px;border:1px solid var(--line)}
.box.ok{background:var(--okbg);color:var(--ok)} .box.bad{background:var(--badbg);color:var(--bad)} .box.warn{background:var(--warnbg);color:var(--warn)}
.scroll{overflow-x:auto;border:1px solid var(--line);border-radius:14px}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{padding:10px 12px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line)}
th{color:var(--mute);font-weight:500;font-size:12px;text-transform:uppercase;letter-spacing:.04em;background:var(--card2);position:sticky;top:0}
tr:last-child td{border-bottom:0}
tbody tr{transition:background .2s} tbody tr:hover{background:var(--card2)}
td a{color:var(--acc);background:linear-gradient(currentColor,currentColor) 0 100%/0 1px no-repeat;transition:background-size .35s var(--ease)}
td a:hover{background-size:100% 1px}
.tag{display:inline-block;padding:2px 9px;border-radius:999px;font-size:11.5px;border:1px solid var(--line2);color:var(--mute)}
.tag.yes{color:var(--ok);border-color:color-mix(in srgb,var(--ok) 40%,transparent)} .tag.no{color:var(--bad);border-color:color-mix(in srgb,var(--bad) 40%,transparent)}
details{border-top:1px solid var(--line);padding:12px 0} details:first-of-type{border-top:0;padding-top:0}
summary{cursor:pointer;font-weight:500;list-style:none;display:flex;align-items:center;gap:10px}
summary::-webkit-details-marker{display:none}
summary::before{content:"+";display:grid;place-items:center;width:22px;height:22px;border-radius:50%;background:var(--card2);font:500 14px var(--mono);
  transition:transform .4s var(--spring)}
details[open] summary::before{transform:rotate(45deg)}
pre{white-space:pre-wrap;background:var(--bg2);border:1px solid var(--line);padding:12px 14px;border-radius:12px;font-size:12.5px;max-height:420px;overflow:auto}
.mail{background:var(--bg2);border:1px solid var(--line2);border-radius:16px;overflow:hidden}
.mail .hd{padding:14px 18px;border-bottom:1px solid var(--line);display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}
.mail .hd span{color:var(--mute);font-size:12.5px} .mail .bd{padding:18px;white-space:pre-wrap;font-size:14.5px;line-height:1.7}
.pain{list-style:none;padding:0;margin:0;display:grid;gap:10px}
.pain>li{background:var(--card2);border:1px solid var(--line);border-radius:14px;padding:14px 16px;transition:transform .35s var(--spring),border-color .3s}
.pain>li:hover{transform:translateX(4px);border-color:var(--line2)}
.pain ul{margin:8px 0 0;padding-left:18px;color:var(--mute);font-size:13px}
footer{text-align:center;color:var(--faint);font-size:12.5px;margin-top:40px}

/* ---------- loading overlay ---------- */
.loading{position:fixed;inset:0;z-index:100;display:grid;place-items:center;background:color-mix(in srgb,var(--bg) 82%,transparent);
  backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);opacity:0;pointer-events:none;transition:opacity .5s var(--ease)}
.loading.on{opacity:1;pointer-events:auto}
.loading .inner{text-align:center;max-width:420px;padding:16px}
.loading .orbwrap{width:180px;margin:0 auto 22px}
.loading .orb{animation:morph 3s var(--ease) infinite alternate,float 2.4s ease-in-out infinite}
.term{text-align:left;font:13px/1.9 var(--mono);color:var(--mute);background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px}
.term div{opacity:.35;transition:opacity .4s,color .4s} .term div.on{opacity:1;color:var(--ink)} .term div.on::after{content:"▍";animation:blink 1s steps(1) infinite;margin-left:4px}
.elapsed{margin-top:12px;color:var(--mute);font:12.5px var(--mono)}
.toast{position:fixed;top:78px;left:50%;transform:translate(-50%,-10px);opacity:0;z-index:60;padding:8px 14px;border-radius:999px;
  background:var(--ink);color:var(--bg);font-size:13px;transition:all .45s var(--spring);pointer-events:none}
.toast.on{opacity:1;transform:translate(-50%,0)}

@keyframes spin{to{transform:rotate(360deg)}}
@keyframes hue{to{--a:360deg}}
@keyframes ping{0%{transform:scale(.6);opacity:1}100%{transform:scale(2.2);opacity:0}}
@keyframes drop{from{opacity:0;transform:translate(-50%,-30px)}}
@keyframes rise{from{opacity:0;transform:translate(-50%,30px)}}
@keyframes word{to{opacity:1;transform:none;filter:none}}
@keyframes pop{from{opacity:0;transform:scale(.4) rotate(-12deg)}}
@keyframes blink{50%{opacity:0}}
@keyframes float{0%,100%{translate:0 0}50%{translate:0 -14px}}
@keyframes shadow{0%,100%{transform:scale(1);opacity:.9}50%{transform:scale(.82);opacity:.55}}
@keyframes morph{
  0%{border-radius:42% 58% 63% 37% / 41% 44% 56% 59%}
  33%{border-radius:58% 42% 38% 62% / 55% 37% 63% 45%}
  66%{border-radius:37% 63% 52% 48% / 62% 58% 42% 38%}
  100%{border-radius:50% 50% 44% 56% / 38% 61% 39% 62%}}
@media (max-width:820px){.hero{grid-template-columns:1fr;min-height:auto}.orbwrap{max-width:220px;order:-1}.nav a{padding:7px 9px}.brand span{display:none}}
@media (max-width:560px){.seg>span{display:none}main{padding-top:96px}}
@media (prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important}
  .reveal,h1 .w{opacity:1!important;transform:none!important;filter:none!important}}
</style></head>
<body>
<div class="grain"></div>

{% macro runform() %}<div class="card reveal" id="runcard"><h2><span class="num">01</span>{{ 'Run another company' if view == 'result' else 'Research a company' }}</h2>
<form method="post" action="/run" id="runform">
  <div class="segctl" role="radiogroup">
    <input type="radio" id="src-url" name="source" value="url" {{ '' if form.get('source')=='demo' else 'checked' }}><label for="src-url" data-sound="toggle">Real website</label>
    <input type="radio" id="src-demo" name="source" value="demo" {{ 'checked' if form.get('source')=='demo' else '' }}><label for="src-demo" data-sound="toggle">Demo company</label>
  </div>
  <label class="field" id="f-url"><span>Company website</span><input type="url" name="url" placeholder="https://example.com" value="{{ form.get('url','') }}"></label>
  <label class="field" id="f-demo"><span>Demo company (offline, fictional)</span><select name="demo">{% for d in demos %}<option {{ 'selected' if form.get('demo')==d else '' }}>{{ d }}</option>{% endfor %}</select></label>
  <label class="toggle"><input type="checkbox" name="outreach" value="1" {{ 'checked' if form.get('outreach') else '' }} data-sound="toggle">
    <span>Also find a decision-maker and draft the email<small>Only runs if the company qualifies.</small></span></label>
  <label class="toggle"><input type="checkbox" name="approve_review" value="1" {{ 'checked' if form.get('approve_review') else '' }} data-sound="toggle">
    <span>If the result is MANUAL_REVIEW, I approve drafting anyway<small>A human has checked the company.</small></span></label>
  <div style="display:flex;gap:14px;align-items:center;flex-wrap:wrap;margin-top:18px">
    <button class="btn magnetic" id="runbtn" data-sound="click">Run research <span class="arr">→</span></button>
    <span class="mute">Takes about 1–3 minutes.</span>
  </div>
</form>
<p class="mute" style="margin:18px 0 0">Limits: max {{ limits[0] }} fetches beyond the homepage, max {{ limits[1] }} stage-related, no duplicate URLs.
Evidence Map: certified → disqualify · not B2B SaaS → disqualify, unclear → manual review · stage evidence → rank A, unknown → rank B.</p>
{% if on_vercel %}<p class="mute" style="margin:6px 0 0">Email sending is switched off in this hosted version. Drafts are shown for review only.</p>{% endif %}</div>
{% endmacro %}
{% macro chips() %}<div class="chips reveal">
{% for name, mode in modes.items() %}<span class="chip" title="{{ name }}: {{ mode }}"><i class="dot {{ 'live' if mode.startswith(('LIVE','configured')) else '' }}"></i>{{ name.split(' (')[0] }} <b>{{ mode.split(' - ')[0] }}</b></span>{% endfor %}
</div>{% endmacro %}
<div class="bar">
  <div class="pill">
    <a class="brand" href="/" data-sound="click"><i></i><span>Sprinto Outreach</span></a>
    {% if view not in ('login','locked') %}
    <nav class="nav" style="display:flex;gap:2px">
      <a href="/" class="{{ 'on' if view in ('form','result') else '' }}" data-sound="click">New run</a>
      <a href="/history" class="{{ 'on' if view == 'history' else '' }}" data-sound="click">History</a>
      {% if has_password %}<a href="/logout" data-sound="click">Log out</a>{% endif %}
    </nav>{% endif %}
  </div>
  <div class="pill">
    <button class="icon" id="themeBtn" type="button" aria-label="Switch light/dark theme" title="Theme">
      <svg id="sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
      <svg id="moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>
    </button>
    <div class="seg" role="group" aria-label="Interface sounds">
      <span>Sound</span>
      <button type="button" data-snd="on" aria-pressed="true">On</button>
      <button type="button" data-snd="off" aria-pressed="false">Off</button>
    </div>
  </div>
</div>
<div class="toast" id="toast"></div>

<main>

{% if view == 'locked' %}
<div class="card reveal" style="max-width:520px;margin:12vh auto 0"><h2><span class="num">!</span>App locked</h2>
<div class="box bad">{{ locked }}</div>
<p class="mute">In Vercel: Project → Settings → Environment Variables → add <code>APP_PASSWORD</code>, then redeploy.</p></div>

{% elif view == 'login' %}
<div class="card reveal" style="max-width:420px;margin:12vh auto 0"><h2><span class="num">→</span>Sign in</h2>
{% if locked %}<div class="box bad">{{ locked }}</div>{% elif not has_password %}<p>No password is set. <a href="/" style="color:var(--acc)">Continue</a></p>
{% else %}<form method="post"><div class="field"><input type="password" name="password" placeholder="App password" autofocus required></div>
{% if error %}<div class="box bad">{{ error }}</div>{% endif %}<button class="btn" data-sound="click">Sign in <span class="arr">→</span></button></form>{% endif %}</div>

{% elif view == 'history' %}
<div class="eyebrow reveal"><span class="num">H</span>Saved runs</div>
<div class="card reveal"><h2>Recent runs</h2>
{% if on_vercel and persistent %}<p class="mute">Saved in SQLite and kept between visits with Vercel Blob storage{% if storage and storage not in ('loaded',) %} ({{ storage }}){% endif %}.</p>
{% elif on_vercel %}<p class="mute">History is temporary here: no Vercel Blob store is connected, so it is wiped when Vercel starts a fresh server.</p>{% endif %}
{% if runs %}<div class="scroll"><table><thead><tr>{% for k in runs[0].keys() %}<th>{{ k }}</th>{% endfor %}</tr></thead><tbody>
{% for r in runs %}<tr>{% for v in r.values() %}<td>{{ v }}</td>{% endfor %}</tr>{% endfor %}</tbody></table></div>
{% else %}<p>No runs saved yet.</p>{% endif %}</div>

{% else %}
{% if view == 'form' %}
<section class="hero">
  <div>
    <div class="eyebrow"><span class="num">AI</span>Mesa School · Sprinto cold outreach at scale</div>
    <h1 data-words>Research a company. <span class="soft">Qualify it on evidence. Draft the email.</span></h1>
    <p class="lede reveal">The AI reads the website and quotes it; plain code applies the Evidence Map. Every claim links back to the page it came from.</p>
    {{ chips() }}
  </div>
  <div class="orbwrap" id="orbwrap"><div class="orbshadow"></div><div class="orb" id="orb"></div></div>
</section>
{% endif %}

{% if view == 'form' %}{{ runform() }}{% endif %}
{% endif %}

{% if view == 'result' %}
{{ chips() }}
{% if error %}<div class="box bad reveal">{{ error }}</div>{% endif %}
{% if research %}{% set d = research.decision %}
<div class="eyebrow reveal" style="margin-top:22px"><span class="num">02</span>Decision</div>
<div class="status reveal {{ {'QUALIFIED':'ok','DISQUALIFIED':'bad'}.get(d.status,'warn') }}">
  <div class="big">{{ d.status }}{% if d.rank %}<span class="rank">{{ d.rank }}</span>{% endif %}</div>
  <div class="sum">{{ d.summary }}</div>
  <div class="metrics">
    <div class="metric"><span>Company</span><b>{{ research.company_name or research.domain }}</b></div>
    <div class="metric"><span>AI mode</span><b>{{ research.llm_mode|upper }}</b></div>
    <div class="metric"><span>Extra fetches</span><b><span class="count" data-to="{{ research.extra_fetches }}">{{ research.extra_fetches }}</span> / {{ limits[0] }}</b></div>
    <div class="metric"><span>Stage fetches</span><b><span class="count" data-to="{{ research.stage_fetches }}">{{ research.stage_fetches }}</span> / {{ limits[1] }}</b></div>
  </div>
  <p class="mute" style="margin:14px 0 0">Stop reason: {{ research.stop_reason }}</p>
</div>
{% if research.llm_mode == 'mock' %}<div class="box warn reveal">MOCK AI: evidence was found by keyword rules, not by an AI model. Treat as a demo.</div>{% endif %}
{% for f in d.flags %}<div class="box warn reveal">🚩 {{ f }}</div>{% endfor %}

<div class="card reveal"><h2><span class="num">03</span>Evidence Map</h2><div class="scroll"><table>
{% if d.steps %}<thead><tr>{% for k in d.steps[0].keys() %}<th>{{ k }}</th>{% endfor %}</tr></thead>{% endif %}<tbody>
{% for s in d.steps %}<tr>{% for v in s.values() %}<td>{{ v }}</td>{% endfor %}</tr>{% endfor %}</tbody></table></div></div>

<div class="card reveal"><h2><span class="num">04</span>Findings</h2>
<p class="mute" style="margin-top:-6px">kind = fact (stated on the page) or inference. Only verified findings (quote found on the page) are used in decisions.</p>
<div class="scroll"><table><thead><tr><th>id</th><th>field</th><th>value</th><th>kind</th><th>conf.</th><th>verified</th><th>quote</th><th>source</th></tr></thead><tbody>
{% for f in findings %}<tr{% if not f.verified %} style="opacity:.5"{% endif %}><td class="mono">{{ f.id }}</td><td>{{ f.field }}</td><td>{{ f.value }}</td><td><span class="tag">{{ f.kind }}</span></td>
<td>{{ f.confidence }}</td><td>{% if f.verified %}<span class="tag yes">✓ yes</span>{% else %}<span class="tag no">✗ no</span>{% endif %}</td><td>{{ f.quote }}</td><td><a href="{{ f.source_url }}" target="_blank" rel="noopener noreferrer">link ↗</a></td></tr>
{% else %}<tr><td colspan="8">No findings.</td></tr>{% endfor %}</tbody></table></div></div>

<div class="card reveal"><h2><span class="num">05</span>Agent trail</h2>
<details><summary data-sound="toggle">Agent log ({{ research.log|length }} steps)</summary>
{% for step in research.log %}<pre>{{ loop.index }}. {{ step|tojson(indent=1) }}</pre>{% endfor %}</details>
<details><summary data-sound="toggle">Pages fetched ({{ research.pages|length }})</summary>
{% for p in research.pages %}<p><b>{{ p.url }}</b> — {{ p.get('purpose') }} — {{ p.status }}{% if p.get('counted_as_stage') %} — counted as stage fetch{% endif %}</p>
{% if p.get('errors') %}<p class="mute">{{ p.errors|join('; ') }}</p>{% endif %}<pre>{{ (p.get('text') or '')[:1500] }}</pre>{% endfor %}</details></div>
{% endif %}

{% if outreach %}
<div class="card reveal"><h2><span class="num">06</span>Outreach</h2>
{% if outreach.get('error') %}<div class="box bad">{{ outreach.error }}</div>{% endif %}
{% if outreach.get('skipped') %}<div class="box warn">{{ outreach.skipped }}</div>{% endif %}
{% if outreach.get('contacts') %}<h3>Contacts {{ '(MOCK — not real people)' if outreach.mode == 'mock' else '(' ~ outreach.mode ~ ')' }}</h3>
<div class="scroll"><table><thead><tr><th>name</th><th>position</th><th>email</th><th>confidence</th><th>source</th></tr></thead><tbody>
{% for c in outreach.contacts %}<tr><td>{{ c.full_name }}</td><td>{{ c.position }}</td><td>{{ c.email }}</td><td>{{ c.confidence }}</td><td>{{ c.source }}</td></tr>{% endfor %}</tbody></table></div>
<p><b>Chosen:</b> {{ outreach.reason }}</p>{% endif %}
{% set e = outreach.get('email') %}{% if e %}
<h3>Email draft <span class="tag" style="margin-left:6px">{{ e.status }}</span></h3>
{% for i in e.issues %}<div class="box warn">{{ i }}</div>{% endfor %}
<div class="mail"><div class="hd"><span>Subject</span><b>{{ e.subject }}</b></div><div class="bd">{{ e.body }}</div></div>
<h3>Pain points and their evidence</h3><ul class="pain">
{% for p in e.pain_points %}<li><b>{{ p.pain_point }}</b> <span class="mute">— {{ p.reasoning }}</span><ul>
{% for i in p.evidence_ids %}{% set ev = evidence.get(i) %}<li>{% if ev %}<span class="mono">{{ i }}</span>: "{{ ev.quote }}" ({{ ev.kind }}, {{ ev.source_url }}){% else %}{{ i }}: ⚠ unknown ID{% endif %}</li>{% endfor %}</ul></li>{% endfor %}</ul>
<div class="box warn" style="margin-top:14px">Not sent. {% if on_vercel %}Sending is off in the hosted version; use the local app (streamlit_app.py) to send a TEST to your own inbox after approval.{% else %}Use the local Streamlit app to send a TEST to your own inbox after approval.{% endif %}</div>
{% endif %}</div>
{% endif %}
{% endif %}

{% if view == 'result' %}<div style="margin-top:28px">{{ runform() }}</div>{% endif %}
<footer class="reveal">AI extracts and quotes · code decides · nothing is emailed to prospects</footer>
</main>

<div class="loading" id="loading" aria-live="polite">
  <div class="inner">
    <div class="orbwrap"><div class="orbshadow"></div><div class="orb"></div></div>
    <div class="term" id="term">
      <div>$ scrape homepage</div><div>$ extract evidence with AI</div><div>$ verify every quote</div>
      <div>$ apply the Evidence Map</div><div>$ fetch missing pages (max 4)</div><div>$ draft the email if qualified</div>
    </div>
    <div class="elapsed">This can take 1–3 minutes · <span id="secs">0</span>s</div>
  </div>
</div>

<script>
(function(){
  var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  function store(k, v){ try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch(e){ return null; } }

  /* ---- sound (Web Audio, no files) ---- */
  var ctx = null, soundOn = store('sound') !== 'off';
  function tone(freq, dur, type, vol, slide){
    if (!soundOn) return;
    try {
      ctx = ctx || new (window.AudioContext || window.webkitAudioContext)();
      if (ctx.state === 'suspended') ctx.resume();
      var t = ctx.currentTime, o = ctx.createOscillator(), g = ctx.createGain();
      o.type = type || 'sine'; o.frequency.setValueAtTime(freq, t);
      if (slide) o.frequency.exponentialRampToValueAtTime(slide, t + dur);
      g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(vol || 0.08, t + 0.008);
      g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
      o.connect(g).connect(ctx.destination); o.start(t); o.stop(t + dur + 0.02);
    } catch(e){}
  }
  var sounds = {
    click: function(){ tone(520, .09, 'sine', .09, 260); },
    toggle: function(){ tone(700, .05, 'triangle', .05); setTimeout(function(){ tone(1050, .06, 'triangle', .04); }, 45); },
    hover: function(){ tone(1400, .025, 'sine', .012); },
    on: function(){ tone(440, .08, 'sine', .07); setTimeout(function(){ tone(660, .1, 'sine', .07); }, 70); },
    done: function(){ [523, 659, 784].forEach(function(f, i){ setTimeout(function(){ tone(f, .18, 'sine', .05); }, i * 90); }); }
  };
  document.addEventListener('click', function(e){
    var el = e.target.closest('[data-sound]'); if (el) (sounds[el.dataset.sound] || sounds.click)();
  });
  var lastHover = 0;
  document.addEventListener('mouseover', function(e){
    var el = e.target.closest('.btn, .icon, .nav a, .segctl label, summary');
    if (el && Date.now() - lastHover > 60) { lastHover = Date.now(); sounds.hover(); }
  });
  var toastEl = document.getElementById('toast'), toastT;
  function toast(msg){ toastEl.textContent = msg; toastEl.classList.add('on'); clearTimeout(toastT); toastT = setTimeout(function(){ toastEl.classList.remove('on'); }, 1400); }
  function paintSound(){ document.querySelectorAll('[data-snd]').forEach(function(b){ b.setAttribute('aria-pressed', String((b.dataset.snd === 'on') === soundOn)); }); }
  document.querySelectorAll('[data-snd]').forEach(function(b){
    b.addEventListener('click', function(){ soundOn = b.dataset.snd === 'on'; store('sound', soundOn ? 'on' : 'off'); paintSound(); if (soundOn) sounds.on(); toast(soundOn ? 'Sound on' : 'Sound off'); });
  });
  paintSound();

  /* ---- theme ---- */
  var root = document.documentElement;
  function paintTheme(){ var dark = root.dataset.theme !== 'light';
    document.getElementById('sun').style.display = dark ? 'block' : 'none'; document.getElementById('moon').style.display = dark ? 'none' : 'block'; }
  document.getElementById('themeBtn').addEventListener('click', function(){
    root.dataset.theme = root.dataset.theme === 'light' ? 'dark' : 'light'; store('theme', root.dataset.theme); paintTheme();
    sounds.toggle(); toast(root.dataset.theme === 'light' ? 'Light mode' : 'Dark mode');
  });
  paintTheme();

  /* ---- headline word reveal ---- */
  document.querySelectorAll('[data-words]').forEach(function(h){
    var i = 0;
    (function walk(node){
      Array.prototype.slice.call(node.childNodes).forEach(function(n){
        if (n.nodeType === 3) {
          var frag = document.createDocumentFragment();
          n.textContent.split(/(\s+)/).forEach(function(w){
            if (!w.trim()) { frag.appendChild(document.createTextNode(w)); return; }
            var s = document.createElement('span'); s.className = 'w'; s.textContent = w; s.style.animationDelay = (0.15 + i++ * 0.07) + 's'; frag.appendChild(s);
          });
          n.parentNode.replaceChild(frag, n);
        } else walk(n);
      });
    })(h);
  });

  /* ---- reveal on scroll ---- */
  var io = 'IntersectionObserver' in window ? new IntersectionObserver(function(es){
    es.forEach(function(en){ if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); } });
  }, {threshold: .08, rootMargin: '0px 0px -40px 0px'}) : null;
  document.querySelectorAll('.reveal').forEach(function(el, i){
    el.style.transitionDelay = Math.min(i * 0.06, 0.4) + 's';
    if (io && !reduce) io.observe(el); else el.classList.add('in');
  });

  /* ---- cursor spotlight on cards ---- */
  document.addEventListener('pointermove', function(e){
    var c = e.target.closest('.card'); if (!c) return;
    var r = c.getBoundingClientRect(); c.style.setProperty('--mx', (e.clientX - r.left) + 'px'); c.style.setProperty('--my', (e.clientY - r.top) + 'px');
  });

  /* ---- orb follows the cursor (tilt) ---- */
  var orb = document.getElementById('orb');
  if (orb && !reduce) document.addEventListener('pointermove', function(e){
    var x = e.clientX / innerWidth - .5, y = e.clientY / innerHeight - .5;
    orb.style.setProperty('--ry', (x * 22) + 'deg'); orb.style.setProperty('--rx', (-y * 22) + 'deg');
  });

  /* ---- magnetic primary button ---- */
  document.querySelectorAll('.magnetic').forEach(function(b){
    if (reduce) return;
    b.addEventListener('pointermove', function(e){ var r = b.getBoundingClientRect();
      b.style.transform = 'translate(' + ((e.clientX - r.left - r.width / 2) * .18) + 'px,' + ((e.clientY - r.top - r.height / 2) * .28) + 'px)'; });
    b.addEventListener('pointerleave', function(){ b.style.transform = ''; });
  });

  /* ---- count-up metrics ---- */
  document.querySelectorAll('.count').forEach(function(el){
    var to = +el.dataset.to; if (reduce || !to) return; var n = 0; el.textContent = '0';
    var t = setInterval(function(){ n++; el.textContent = n; if (n >= to) clearInterval(t); }, 160);
  });

  /* ---- form: show the field for the chosen source ---- */
  var form = document.getElementById('runform');
  if (form) {
    function paintSource(){ var demo = form.querySelector('#src-demo').checked;
      document.getElementById('f-url').classList.toggle('hide', demo); document.getElementById('f-demo').classList.toggle('hide', !demo); }
    form.querySelectorAll('input[name=source]').forEach(function(r){ r.addEventListener('change', paintSource); });
    paintSource();

    /* loading overlay while the server works (the request itself is unchanged) */
    form.addEventListener('submit', function(){
      var btn = document.getElementById('runbtn'); btn.disabled = true; btn.firstChild.textContent = 'Running… ';
      var ov = document.getElementById('loading'); ov.classList.add('on');
      var lines = document.querySelectorAll('#term div'), k = 0, s = 0;
      lines[0].classList.add('on');
      setInterval(function(){ s++; document.getElementById('secs').textContent = s;
        if (s % 9 === 0 && k < lines.length - 1) { lines[k].classList.remove('on'); k++; lines[k].classList.add('on'); sounds.hover(); } }, 1000);
    });
  }

  /* ---- a soft chime when results appear (only if sound is on and the browser allows it) ---- */
  if (document.querySelector('.status')) setTimeout(function(){ sounds.done(); }, 500);
})();
</script>
</body></html>
"""
