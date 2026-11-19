"""
HTML/CSS/JS template for the web app (index.py). Design only: routes, form field names
and decisions are unchanged.

  * Dark by default, light toggle (remembered per browser). Interface sounds on/off.
  * Ticker of recent runs, home-page stats, rich result insights (insights.py).
  * Motion: orb, word reveal, scroll reveals, cursor spotlight, magnetic button, count-ups.
    All motion is off for people who prefer reduced motion.
  * Everything that's about the assignment itself lives in the footer.
"""

PAGE = r"""<!doctype html>
<html lang="en" data-theme="dark"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sprinto Lead Radar</title>
<meta name="description" content="Type a company. Get an evidence-backed verdict on whether it's ready for Sprinto, and a cold email built only from what's on its website.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<script>try{var t=localStorage.getItem('theme');if(t)document.documentElement.dataset.theme=t;}catch(e){}</script>
<style>
:root{--font:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;--mono:"JetBrains Mono",ui-monospace,Consolas,monospace;
  --ease:cubic-bezier(.2,.8,.2,1);--spring:cubic-bezier(.34,1.56,.64,1);--r:20px}
html[data-theme="dark"]{--bg:#09090b;--bg2:#101013;--card:#121216;--card2:#18181d;--ink:#f5f5f7;--mute:#8e8e99;--faint:#55555f;
  --line:rgba(255,255,255,.07);--line2:rgba(255,255,255,.13);--glass:rgba(16,16,20,.7);
  --acc:#a3b8ff;--acc2:#d0a9ff;--ok:#6ee7a8;--okbg:rgba(110,231,168,.09);--bad:#ff8a8a;--badbg:rgba(255,138,138,.09);
  --warn:#ffd36e;--warnbg:rgba(255,211,110,.08);--shadow:0 20px 60px -20px rgba(0,0,0,.7);--spot:rgba(163,184,255,.09);--glow:rgba(140,155,255,.22)}
html[data-theme="light"]{--bg:#f7f7f5;--bg2:#fff;--card:#fff;--card2:#f3f3f0;--ink:#111114;--mute:#6d6d76;--faint:#a5a5ad;
  --line:rgba(0,0,0,.07);--line2:rgba(0,0,0,.13);--glass:rgba(255,255,255,.78);
  --acc:#3d5af1;--acc2:#8a4dff;--ok:#12804a;--okbg:rgba(18,128,74,.08);--bad:#c02626;--badbg:rgba(192,38,38,.07);
  --warn:#9a6200;--warnbg:rgba(154,98,0,.08);--shadow:0 20px 50px -24px rgba(20,20,50,.25);--spot:rgba(61,90,241,.07);--glow:rgba(61,90,241,.15)}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 var(--font);-webkit-font-smoothing:antialiased;overflow-x:hidden;
  transition:background .5s var(--ease),color .5s var(--ease)}
body::before{content:"";position:fixed;inset:-20% -10% auto;height:70vh;pointer-events:none;z-index:0;
  background:radial-gradient(50% 60% at 50% 0%,var(--glow),transparent 70%)}
a{color:inherit;text-decoration:none}::selection{background:var(--acc);color:#000}
code,.mono{font-family:var(--mono)}
.grain{position:fixed;inset:0;pointer-events:none;z-index:0;opacity:.03;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")}

/* top bar + ticker */
.top{position:fixed;top:0;left:0;right:0;z-index:50}
.bar{display:flex;justify-content:center;gap:8px;padding:14px 16px 10px;animation:drop .8s var(--spring) both}
.pill{display:flex;align-items:center;gap:4px;padding:5px;border-radius:999px;background:var(--glass);border:1px solid var(--line);
  backdrop-filter:blur(18px) saturate(1.4);-webkit-backdrop-filter:blur(18px) saturate(1.4);box-shadow:var(--shadow)}
.brand{display:flex;align-items:center;gap:9px;padding:6px 14px 6px 8px;font-weight:600;font-size:14px;white-space:nowrap;letter-spacing:-.01em}
.brand i{width:22px;height:22px;border-radius:50%;background:conic-gradient(from 0deg,var(--acc),var(--acc2),#ffb3c7,var(--acc));animation:spin 6s linear infinite;box-shadow:0 0 16px var(--acc)}
.nav a{white-space:nowrap;padding:7px 13px;border-radius:999px;font-size:13.5px;color:var(--mute);transition:color .25s,background .25s}
.nav a:hover,.nav a.on{color:var(--ink);background:var(--card2)}
.icon{width:38px;height:38px;border-radius:50%;display:grid;place-items:center;border:0;background:transparent;color:var(--ink);cursor:pointer;transition:background .25s,transform .3s var(--spring)}
.icon:hover{background:var(--card2);transform:scale(1.08)}.icon:active{transform:scale(.92)}.icon svg{width:18px;height:18px}
.seg{white-space:nowrap;display:flex;align-items:center;gap:2px;font-size:12.5px;color:var(--mute);padding-left:10px}
.seg button{border:0;background:transparent;color:var(--mute);font:inherit;padding:6px 11px;border-radius:999px;cursor:pointer;transition:all .3s var(--ease)}
.seg button[aria-pressed="true"]{background:var(--ink);color:var(--bg)}
.ticker{overflow:hidden;border-top:1px solid var(--line);border-bottom:1px solid var(--line);background:var(--glass);
  backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);-webkit-mask:linear-gradient(90deg,transparent,#000 8%,#000 92%,transparent);
  mask:linear-gradient(90deg,transparent,#000 8%,#000 92%,transparent)}
.track{display:flex;gap:34px;width:max-content;padding:8px 0;animation:marquee 45s linear infinite;font:12.5px var(--mono);color:var(--mute)}
.ticker:hover .track{animation-play-state:paused}
.tk{display:flex;align-items:center;gap:8px;white-space:nowrap}.tk b{color:var(--ink);font-weight:500}
.tk .st{padding:1px 8px;border-radius:999px;font-size:11px;border:1px solid currentColor}
.st.QUALIFIED{color:var(--ok)}.st.DISQUALIFIED{color:var(--bad)}.st.MANUAL_REVIEW,.st.FETCH_FAILED{color:var(--warn)}
.toast{position:fixed;top:110px;left:50%;transform:translate(-50%,-10px);opacity:0;z-index:60;padding:8px 14px;border-radius:999px;background:var(--ink);color:var(--bg);font-size:13px;transition:all .45s var(--spring);pointer-events:none}
.toast.on{opacity:1;transform:translate(-50%,0)}

/* layout */
main{position:relative;z-index:1;max-width:1120px;margin:0 auto;padding:150px 16px 40px}
h1{font-size:clamp(36px,6vw,68px);line-height:1.02;letter-spacing:-.04em;font-weight:600;margin:0 0 18px}
h1 .w{display:inline-block;opacity:0;transform:translateY(.45em) rotate(2deg);filter:blur(6px);animation:word .9s var(--ease) forwards}
h1 .soft{color:var(--faint)}
.lede{color:var(--mute);font-size:17px;max-width:560px;margin:0}
.eyebrow{display:inline-flex;align-items:center;gap:10px;font-size:13px;color:var(--mute);margin:0 0 14px}
.num{display:inline-grid;place-items:center;min-width:30px;height:24px;padding:0 9px;border-radius:999px;background:var(--card2);color:var(--ink);font:500 11.5px var(--mono);border:1px solid var(--line)}
.sec{display:flex;align-items:baseline;justify-content:space-between;gap:12px;margin:44px 0 14px}
.sec h2{font-size:22px;letter-spacing:-.02em;margin:0;font-weight:600}.sec p{margin:0;color:var(--mute);font-size:13.5px}
.grid{display:grid;gap:14px}.g2{grid-template-columns:repeat(2,1fr)}.g3{grid-template-columns:repeat(3,1fr)}.g4{grid-template-columns:repeat(4,1fr)}
.span2{grid-column:span 2}
@media (max-width:900px){.g3,.g4{grid-template-columns:repeat(2,1fr)}}
@media (max-width:640px){.g2,.g3,.g4{grid-template-columns:1fr}.span2{grid-column:auto}}

/* hero */
.hero{display:grid;grid-template-columns:1.25fr .75fr;gap:28px;align-items:center;margin-bottom:8px}
.orbwrap{position:relative;aspect-ratio:1;max-width:330px;width:100%;justify-self:center;perspective:800px}
.orb{position:absolute;inset:8%;border-radius:42% 58% 63% 37%/41% 44% 56% 59%;
  background:radial-gradient(70% 55% at 32% 28%,rgba(255,255,255,.85),rgba(255,255,255,0) 60%),radial-gradient(85% 75% at 68% 78%,#07070d 18%,rgba(7,7,13,0) 62%),linear-gradient(160deg,#e7e9f5 0%,#9aa0bd 38%,#3b3d55 62%,#cfd3ea 100%);
  box-shadow:inset -18px -26px 60px rgba(0,0,0,.45),inset 14px 18px 40px rgba(255,255,255,.55),0 40px 90px -20px rgba(120,130,255,.35);
  animation:morph 14s var(--ease) infinite alternate,float 7s ease-in-out infinite;transform:rotateX(var(--rx,0deg)) rotateY(var(--ry,0deg));transition:transform .6s var(--ease)}
.orb::before{content:"";position:absolute;inset:-2px;border-radius:inherit;padding:3px;background:conic-gradient(from var(--a,0deg),transparent 0 55%,#ff9a62,#ffe66b,#6bd5ff,#a07bff,transparent 85%);
  -webkit-mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);-webkit-mask-composite:xor;mask-composite:exclude;filter:blur(1.5px);animation:hue 5s linear infinite}
.orb::after{content:"";position:absolute;inset:18% 30% 46% 18%;border-radius:50%;background:rgba(255,255,255,.55);filter:blur(18px)}
.orbshadow{position:absolute;left:18%;right:18%;bottom:-2%;height:12%;border-radius:50%;background:radial-gradient(rgba(0,0,0,.6),transparent 70%);filter:blur(8px);animation:shadow 7s ease-in-out infinite}
@property --a{syntax:"<angle>";initial-value:0deg;inherits:false}

/* search */
.search{margin-top:28px;background:var(--card);border:1px solid var(--line2);border-radius:22px;padding:8px;box-shadow:var(--shadow);transition:border-color .3s,box-shadow .3s}
.search:focus-within{border-color:var(--acc);box-shadow:0 0 0 5px color-mix(in srgb,var(--acc) 16%,transparent),var(--shadow)}
.srow{display:flex;gap:8px;align-items:center}
.srow svg{width:20px;height:20px;color:var(--mute);margin-left:12px;flex:0 0 auto}
.srow input{flex:1;min-width:0;border:0;background:transparent;color:var(--ink);font:500 17px var(--font);padding:14px 6px;outline:none}
.opts{display:flex;flex-wrap:wrap;gap:6px 18px;padding:8px 12px 6px;border-top:1px solid var(--line);margin-top:6px}
.chipbtn{border:1px solid var(--line2);background:var(--card2);color:var(--ink);font:500 12.5px var(--font);padding:7px 12px;border-radius:999px;cursor:pointer;transition:transform .3s var(--spring),border-color .25s,background .25s}
.chipbtn:hover{transform:translateY(-2px);border-color:var(--acc)}
.demos{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:14px;font-size:13px;color:var(--mute)}
.toggle{display:flex;align-items:center;gap:10px;cursor:pointer;font-size:13px;color:var(--mute)}
.toggle input{appearance:none;-webkit-appearance:none;flex:0 0 auto;width:34px;height:20px;border-radius:999px;background:var(--card2);border:1px solid var(--line2);position:relative;cursor:pointer;transition:background .3s var(--ease);margin:0}
.toggle input::after{content:"";position:absolute;top:2px;left:2px;width:14px;height:14px;border-radius:50%;background:var(--mute);transition:transform .4s var(--spring),background .3s}
.toggle input:checked{background:var(--acc)}.toggle input:checked::after{transform:translateX(14px);background:#fff}
.btn{position:relative;display:inline-flex;align-items:center;justify-content:center;gap:10px;border:0;border-radius:16px;padding:14px 22px;font:600 15px var(--font);white-space:nowrap;
  cursor:pointer;color:var(--bg);background:var(--ink);overflow:hidden;transition:transform .35s var(--spring),box-shadow .35s;box-shadow:0 8px 30px -8px color-mix(in srgb,var(--acc) 60%,transparent)}
.btn::after{content:"";position:absolute;inset:0;background:linear-gradient(110deg,transparent 30%,rgba(255,255,255,.45) 50%,transparent 70%);transform:translateX(-120%);transition:transform .8s var(--ease)}
.btn:hover::after{transform:translateX(120%)}.btn:active{transform:scale(.96)!important}
.btn .arr{transition:transform .35s var(--spring)}.btn:hover .arr{transform:translateX(4px)}.btn[disabled]{opacity:.6;cursor:progress}
.ghost{background:transparent;color:var(--ink);border:1px solid var(--line2);box-shadow:none}

/* cards */
.card{position:relative;background:var(--card);border:1px solid var(--line);border-radius:var(--r);padding:20px;overflow:hidden;transition:border-color .35s,transform .45s var(--ease),box-shadow .45s var(--ease)}
.card::before{content:"";position:absolute;inset:0;pointer-events:none;opacity:0;transition:opacity .4s;background:radial-gradient(420px circle at var(--mx,50%) var(--my,50%),var(--spot),transparent 60%)}
.card:hover{border-color:var(--line2);box-shadow:var(--shadow)}.card:hover::before{opacity:1}
.card h3{font-size:14px;margin:0 0 12px;font-weight:600;color:var(--mute);letter-spacing:.01em}
.k{font-size:12px;color:var(--mute);text-transform:uppercase;letter-spacing:.06em}
.big{font-size:34px;font-weight:600;letter-spacing:-.03em;line-height:1.1}
.mute{color:var(--mute);font-size:13.5px}
.reveal{opacity:0;transform:translateY(24px) scale(.985);transition:opacity .9s var(--ease),transform .9s var(--ease)}.reveal.in{opacity:1;transform:none}
.steps4 .card{padding:18px}.steps4 .n{font:500 12px var(--mono);color:var(--acc)}.steps4 b{display:block;margin:6px 0 4px;font-size:15px}
.rules li{margin:0 0 10px;padding-left:28px;position:relative;list-style:none;font-size:14px}
.rules li span:first-child{position:absolute;left:0;top:1px;width:20px;height:20px;border-radius:50%;display:grid;place-items:center;font:500 11px var(--mono);background:var(--card2);border:1px solid var(--line2)}
.rules{padding:0;margin:0}
.recent{display:grid;gap:8px}
.rrow{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:10px 12px;border-radius:12px;background:var(--card2);border:1px solid var(--line);font-size:13.5px;transition:transform .3s var(--spring)}
.rrow:hover{transform:translateX(4px)}.rrow .mono{font-size:12.5px}

/* results */
.banner{display:flex;gap:12px;align-items:center;flex-wrap:wrap;padding:12px 16px;border-radius:14px;background:var(--card);border:1px dashed var(--line2);font-size:14px;margin-bottom:14px}
.verdict{border-radius:24px;padding:28px;border:1px solid var(--line);position:relative;overflow:hidden}
.verdict.ok{background:linear-gradient(135deg,var(--okbg),transparent 65%),var(--card)}.verdict.bad{background:linear-gradient(135deg,var(--badbg),transparent 65%),var(--card)}
.verdict.warn{background:linear-gradient(135deg,var(--warnbg),transparent 65%),var(--card)}
.vtop{display:flex;justify-content:space-between;gap:20px;flex-wrap:wrap;align-items:flex-start}
.vstatus{font-size:clamp(34px,6vw,58px);font-weight:700;letter-spacing:-.04em;line-height:1;display:flex;align-items:center;gap:14px}
.ok .vstatus{color:var(--ok)}.bad .vstatus{color:var(--bad)}.warn .vstatus{color:var(--warn)}
.rank{display:inline-grid;place-items:center;width:50px;height:50px;border-radius:15px;font-size:24px;background:var(--card2);color:var(--ink);border:1px solid var(--line2);animation:pop .7s .4s var(--spring) both}
.vco{text-align:right}.vco b{display:block;font-size:20px;letter-spacing:-.01em}.vco a{color:var(--acc);font-size:13px}
.why{font-size:17px;margin:16px 0 4px;max-width:760px}
.next{display:inline-flex;gap:8px;align-items:center;margin-top:12px;padding:8px 14px;border-radius:999px;background:var(--card2);border:1px solid var(--line2);font-size:13.5px}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:22px}
@media (max-width:760px){.kpis{grid-template-columns:repeat(2,1fr)}.vco{text-align:left}}
.kpi{background:color-mix(in srgb,var(--card2) 70%,transparent);border:1px solid var(--line);border-radius:14px;padding:12px 14px;transition:transform .35s var(--spring)}
.kpi:hover{transform:translateY(-3px)}.kpi b{display:block;font-size:22px;font-weight:600;letter-spacing:-.02em}.kpi span{font-size:12px;color:var(--mute)}
.stepper{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
@media (max-width:760px){.stepper{grid-template-columns:1fr}}
.step{position:relative;padding:18px;border-radius:18px;background:var(--card);border:1px solid var(--line)}
.step .ic{width:30px;height:30px;border-radius:50%;display:grid;place-items:center;font-weight:700;margin-bottom:10px;background:var(--card2)}
.step.good .ic{background:var(--okbg);color:var(--ok)}.step.bad .ic{background:var(--badbg);color:var(--bad)}.step.warn .ic{background:var(--warnbg);color:var(--warn)}
.step.skip{opacity:.45}.step b{display:block;font-size:15px}.step .a{font:500 12px var(--mono);margin:4px 0 8px;display:inline-block}
.good .a{color:var(--ok)}.bad .a{color:var(--bad)}.warn .a{color:var(--warn)}
.sig{position:relative;padding:16px;border-radius:16px;background:var(--card);border:1px solid var(--line);transition:transform .35s var(--spring),border-color .3s;min-height:118px;outline:none}
.sig:hover,.sig:focus{transform:translateY(-3px);border-color:var(--line2)}
.sig .k{display:flex;justify-content:space-between;align-items:center}
.sig .v{font-size:16px;font-weight:600;margin:8px 0 4px;letter-spacing:-.01em;overflow-wrap:anywhere}
.sig .h{font-size:12.5px;color:var(--mute)}
.dotg{width:8px;height:8px;border-radius:50%;background:var(--faint)}.sig.good .dotg{background:var(--ok);box-shadow:0 0 10px var(--ok)}.sig.bad .dotg{background:var(--bad);box-shadow:0 0 10px var(--bad)}
.sig .q{position:absolute;left:10px;right:10px;bottom:calc(100% + 8px);padding:10px 12px;border-radius:12px;background:var(--ink);color:var(--bg);font-size:12.5px;line-height:1.5;
  opacity:0;transform:translateY(6px);pointer-events:none;transition:all .3s var(--ease);z-index:5;box-shadow:var(--shadow)}
.sig:hover .q,.sig:focus .q{opacity:1;transform:none}
.ring{--p:0;width:120px;height:120px;border-radius:50%;display:grid;place-items:center;flex:0 0 auto;background:conic-gradient(var(--ok) calc(var(--p)*1%),var(--card2) 0);transition:--p 1.2s var(--ease)}
@property --p{syntax:"<number>";initial-value:0;inherits:false}
.ring div{width:94px;height:94px;border-radius:50%;background:var(--card);display:grid;place-items:center;text-align:center}
.ring b{font-size:24px;line-height:1}.ring span{font-size:11px;color:var(--mute)}
.bar2{height:8px;border-radius:999px;background:var(--card2);overflow:hidden;display:flex;margin:8px 0 4px}
.bar2 i{display:block;height:100%;width:0;transition:width 1.2s var(--ease)}
.meter{margin:12px 0}.meter .lbl{display:flex;justify-content:space-between;font-size:13px}
.cells{display:flex;gap:6px;margin-top:6px}.cells i{flex:1;height:10px;border-radius:4px;background:var(--card2);border:1px solid var(--line)}
.cells i.on{background:linear-gradient(90deg,var(--acc),var(--acc2));border-color:transparent}
.src{display:flex;flex-direction:column;gap:6px;margin-top:10px}.src a{font:12.5px var(--mono);color:var(--acc);overflow-wrap:anywhere}
.timeline{position:relative;padding-left:26px}
.timeline::before{content:"";position:absolute;left:9px;top:6px;bottom:6px;width:2px;background:linear-gradient(var(--acc),var(--line))}
.tl{position:relative;padding:0 0 16px}.tl .ic{position:absolute;left:-26px;top:1px;width:20px;height:20px;border-radius:50%;display:grid;place-items:center;font-size:11px;background:var(--card2);border:1px solid var(--line2)}
.tl.good .ic{color:var(--ok)}.tl.warn .ic{color:var(--warn)}.tl b{font-size:14px;font-weight:500}.tl p{margin:2px 0 0;font-size:12.5px;color:var(--mute);overflow-wrap:anywhere}
.box{padding:11px 14px;border-radius:12px;margin:8px 0;font-size:14px;border:1px solid var(--line)}
.box.ok{background:var(--okbg);color:var(--ok)}.box.bad{background:var(--badbg);color:var(--bad)}.box.warn{background:var(--warnbg);color:var(--warn)}
.scroll{overflow-x:auto;border:1px solid var(--line);border-radius:14px}
table{border-collapse:collapse;width:100%;font-size:13px}th,td{padding:10px 12px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line)}
th{color:var(--mute);font-weight:500;font-size:11.5px;text-transform:uppercase;letter-spacing:.05em;background:var(--card2);position:sticky;top:0}
tr:last-child td{border-bottom:0}tbody tr{transition:background .2s}tbody tr:hover{background:var(--card2)}
td a{color:var(--acc)}
.tag{display:inline-block;padding:2px 9px;border-radius:999px;font-size:11.5px;border:1px solid var(--line2);color:var(--mute);white-space:nowrap}
.tag.yes{color:var(--ok);border-color:color-mix(in srgb,var(--ok) 40%,transparent)}.tag.no{color:var(--bad);border-color:color-mix(in srgb,var(--bad) 40%,transparent)}
details{border:1px solid var(--line);border-radius:16px;padding:14px 18px;background:var(--card);margin-top:12px}
summary{cursor:pointer;font-weight:500;list-style:none;display:flex;align-items:center;gap:10px}summary::-webkit-details-marker{display:none}
summary::before{content:"+";display:grid;place-items:center;width:22px;height:22px;border-radius:50%;background:var(--card2);font:500 14px var(--mono);transition:transform .4s var(--spring)}
details[open] summary::before{transform:rotate(45deg)}details[open] summary{margin-bottom:12px}
pre{white-space:pre-wrap;background:var(--bg2);border:1px solid var(--line);padding:12px 14px;border-radius:12px;font-size:12.5px;max-height:360px;overflow:auto}
.contact{display:flex;gap:14px;align-items:center;margin-bottom:10px}
.avatar{width:48px;height:48px;border-radius:50%;display:grid;place-items:center;font-weight:600;background:linear-gradient(135deg,var(--acc),var(--acc2));color:#0b0b10;flex:0 0 auto}
.mail{background:var(--bg2);border:1px solid var(--line2);border-radius:18px;overflow:hidden}
.mail .hd{padding:14px 18px;border-bottom:1px solid var(--line);font-size:13px;color:var(--mute);display:grid;gap:4px}
.mail .hd b{color:var(--ink);font-size:15px}.mail .bd{padding:18px;white-space:pre-wrap;font-size:14.5px;line-height:1.75}
.pain{list-style:none;padding:0;margin:0;display:grid;gap:10px}
.pain>li{background:var(--card2);border:1px solid var(--line);border-radius:14px;padding:14px 16px;transition:transform .35s var(--spring)}
.pain>li:hover{transform:translateX(4px)}.pain ul{margin:8px 0 0;padding-left:18px;color:var(--mute);font-size:13px}
.field{display:block;margin:0 0 12px}.field>span{display:block;font-size:12.5px;color:var(--mute);margin-bottom:6px}
select,input[type=password]{width:100%;padding:12px 14px;border:1px solid var(--line2);border-radius:12px;background:var(--bg2);color:var(--ink);font:inherit;outline:none;appearance:none;-webkit-appearance:none}
select{background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%238e8e99' stroke-width='1.6' fill='none'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 14px center;padding-right:38px}

/* footer */
footer{position:relative;z-index:1;border-top:1px solid var(--line);margin-top:70px;padding:34px 16px 46px;background:var(--bg2)}
.fwrap{max-width:1120px;margin:0 auto;display:grid;grid-template-columns:1.3fr 1fr 1fr;gap:28px;font-size:13px;color:var(--mute)}
@media (max-width:760px){.fwrap{grid-template-columns:1fr}}
.fwrap h4{margin:0 0 10px;color:var(--ink);font-size:13px;font-weight:600}.fwrap p{margin:0 0 8px}.fwrap a{color:var(--acc)}
.chips{display:flex;gap:6px;flex-wrap:wrap}
.chip{display:flex;align-items:center;gap:7px;padding:5px 11px;border-radius:999px;background:var(--card);border:1px solid var(--line);font-size:12px;white-space:nowrap}
.chip b{color:var(--ink);font-weight:500}.dot{width:7px;height:7px;border-radius:50%;background:var(--warn);position:relative}
.dot.live{background:var(--ok)}.dot.live::after{content:"";position:absolute;inset:-4px;border-radius:50%;border:1px solid var(--ok);animation:ping 2s var(--ease) infinite}

/* loading */
.loading{position:fixed;inset:0;z-index:100;display:grid;place-items:center;background:color-mix(in srgb,var(--bg) 84%,transparent);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);opacity:0;pointer-events:none;transition:opacity .5s var(--ease)}
.loading.on{opacity:1;pointer-events:auto}.loading .inner{text-align:center;max-width:430px;padding:16px;width:100%}
.loading .orbwrap{width:170px;margin:0 auto 22px}.loading .orb{animation:morph 3s var(--ease) infinite alternate,float 2.4s ease-in-out infinite}
.term{text-align:left;font:13px/1.9 var(--mono);color:var(--mute);background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px}
.term div{opacity:.35;transition:opacity .4s,color .4s}.term div.on{opacity:1;color:var(--ink)}.term div.on::after{content:"▍";animation:blink 1s steps(1) infinite;margin-left:4px}
.term div.done{opacity:.7}.term div.done::before{content:"✓ ";color:var(--ok)}
.elapsed{margin-top:12px;color:var(--mute);font:12.5px var(--mono)}

@keyframes spin{to{transform:rotate(360deg)}}@keyframes hue{to{--a:360deg}}
@keyframes ping{0%{transform:scale(.6);opacity:1}100%{transform:scale(2.2);opacity:0}}
@keyframes drop{from{opacity:0;transform:translateY(-30px)}}@keyframes word{to{opacity:1;transform:none;filter:none}}
@keyframes pop{from{opacity:0;transform:scale(.4) rotate(-12deg)}}@keyframes blink{50%{opacity:0}}
@keyframes marquee{to{transform:translateX(-50%)}}
@keyframes float{0%,100%{translate:0 0}50%{translate:0 -14px}}@keyframes shadow{0%,100%{transform:scale(1);opacity:.9}50%{transform:scale(.82);opacity:.55}}
@keyframes morph{0%{border-radius:42% 58% 63% 37%/41% 44% 56% 59%}33%{border-radius:58% 42% 38% 62%/55% 37% 63% 45%}66%{border-radius:37% 63% 52% 48%/62% 58% 42% 38%}100%{border-radius:50% 50% 44% 56%/38% 61% 39% 62%}}
@media (max-width:860px){.hero{grid-template-columns:1fr}.orbwrap{max-width:190px;order:-1}.nav a{padding:7px 9px}.brand span{display:none}}
@media (max-width:560px){.seg>span{display:none}main{padding-top:140px}.srow{flex-wrap:wrap}.srow .btn{width:100%}}
@media (prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important}.reveal,h1 .w{opacity:1!important;transform:none!important;filter:none!important}}
</style></head>
<body>
<div class="grain"></div>
{% macro chips() %}<div class="chips">{% for name, mode in modes.items() %}<span class="chip" title="{{ name }}: {{ mode }}"><i class="dot {{ 'live' if mode.startswith(('LIVE','configured')) else '' }}"></i>{{ name.split(' (')[0] }} <b>{{ mode.split(' - ')[0] }}</b></span>{% endfor %}</div>{% endmacro %}
{% macro searchbox() %}
<form method="post" action="/run" class="search">
  <input type="hidden" name="source" value="url">
  <div class="srow">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
    <input type="text" name="url" autocomplete="off" required aria-label="Company name or website" placeholder="Company name or website — try “boat” or notion.so" value="{{ form.get('url','') if form else '' }}">
    <button class="btn magnetic runbtn" data-sound="click">Analyse <span class="arr">→</span></button>
  </div>
  <div class="opts">
    <label class="toggle"><input type="checkbox" name="outreach" value="1" {{ '' if form and not form.get('outreach') else 'checked' }} data-sound="toggle">Draft the email if it qualifies</label>
    <label class="toggle"><input type="checkbox" name="approve_review" value="1" {{ 'checked' if form and form.get('approve_review') else '' }} data-sound="toggle">Draft even if it needs review</label>
  </div>
  <div class="demos" style="padding:4px 12px 8px;margin-top:6px">Or try a demo:
    {% for d in demos %}<button class="chipbtn" name="demo_pick" value="{{ d }}" formnovalidate data-sound="click" title="{{ d }}">{{ d.split(' (')[0] }}</button>{% endfor %}
  </div>
</form>
{% endmacro %}

<div class="top">
  <div class="bar">
    <div class="pill">
      <a class="brand" href="/" data-sound="click"><i></i><span>Sprinto Lead Radar</span></a>
      {% if view not in ('login','locked') %}<nav class="nav" style="display:flex;gap:2px">
        <a href="/" class="{{ 'on' if view in ('form','result') else '' }}" data-sound="click">Analyse</a>
        <a href="/history" class="{{ 'on' if view == 'history' else '' }}" data-sound="click">History</a>
        {% if has_password %}<a href="/logout" data-sound="click">Log out</a>{% endif %}</nav>{% endif %}
    </div>
    <div class="pill">
      <button class="icon" id="themeBtn" type="button" aria-label="Switch light or dark theme" title="Theme">
        <svg id="sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>
        <svg id="moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>
      </button>
      <div class="seg" role="group" aria-label="Interface sounds"><span>Sound</span>
        <button type="button" data-snd="on" aria-pressed="true">On</button><button type="button" data-snd="off" aria-pressed="false">Off</button></div>
    </div>
  </div>
  <div class="ticker" aria-label="Recently analysed companies"><div class="track">
    {% for _ in range(2) %}
      {% for r in stats.recent %}<span class="tk"><b>{{ r.domain }}</b><span class="st {{ r.status }}">{{ r.status|replace('_',' ') }}{% if r.rank %} · {{ r.rank }}{% endif %}</span>{{ r.ago }}</span>{% endfor %}
      <span class="tk">◆ <b>{{ stats.total }}</b> companies analysed</span>
      <span class="tk">◆ <b>{{ stats.rate }}%</b> qualified</span>
      <span class="tk">◆ Every claim is quoted from the company's own site</span>
      <span class="tk">◆ Certified → skip · Not B2B → skip · Stage unknown → still a lead, ranked B</span>
      <span class="tk">◆ At most {{ limits[0] }} extra pages per company</span>
    {% endfor %}
  </div></div>
</div>
<div class="toast" id="toast"></div>

<main>
{% if view == 'locked' %}
<div class="card reveal" style="max-width:520px;margin:10vh auto 0"><h3>App locked</h3><div class="box bad">{{ locked }}</div></div>

{% elif view == 'login' %}
<div class="card reveal" style="max-width:420px;margin:10vh auto 0"><h3>Sign in</h3>
{% if locked %}<div class="box bad">{{ locked }}</div>{% elif not has_password %}<p>No password is set. <a href="/" style="color:var(--acc)">Continue</a></p>
{% else %}<form method="post"><label class="field"><input type="password" name="password" placeholder="Password" autofocus required></label>
{% if error %}<div class="box bad">{{ error }}</div>{% endif %}<button class="btn" data-sound="click">Sign in <span class="arr">→</span></button></form>{% endif %}</div>

{% elif view == 'sent' %}
<div class="card reveal" style="max-width:560px;margin:10vh auto 0"><h3>{{ 'Test email sent' if ok else 'Not sent' }}</h3>
<div class="box {{ 'ok' if ok else 'warn' }}">{{ message }}</div>
<p style="margin:16px 0 0"><a class="btn ghost" href="/" data-sound="click">Analyse another company <span class="arr">→</span></a></p></div>

{% elif view == 'history' %}
<div class="sec reveal" style="margin-top:0"><h2>History</h2><p>{% if on_vercel and persistent %}Saved in SQLite, kept between visits with Vercel Blob.{% elif on_vercel %}Temporary on this server.{% else %}Saved in outreach.db.{% endif %}</p></div>
<div class="grid g4 reveal" style="margin-bottom:14px">
  <div class="card"><div class="k">Analysed</div><div class="big count" data-to="{{ stats.total }}">{{ stats.total }}</div></div>
  <div class="card"><div class="k">Qualified</div><div class="big" style="color:var(--ok)">{{ stats.qualified }}</div></div>
  <div class="card"><div class="k">Disqualified</div><div class="big" style="color:var(--bad)">{{ stats.disqualified }}</div></div>
  <div class="card"><div class="k">Needs review</div><div class="big" style="color:var(--warn)">{{ stats.review }}</div></div>
</div>
<div class="card reveal">{% if runs %}<div class="scroll"><table><thead><tr><th>#</th><th>When</th><th>Company</th><th>Verdict</th><th>AI</th><th>Why it stopped</th></tr></thead><tbody>
{% for r in runs %}<tr><td class="mono">{{ r.id }}</td><td class="mono">{{ (r.started_at or '')[:16]|replace('T',' ') }}</td><td>{{ r.company_url }}</td>
<td><span class="tag {{ 'yes' if r.status=='QUALIFIED' else 'no' if r.status=='DISQUALIFIED' else '' }}">{{ r.status|replace('_',' ') }}{% if r.rank %} · {{ r.rank }}{% endif %}</span></td><td>{{ r.llm_mode }}</td><td class="mute">{{ r.stop_reason }}</td></tr>{% endfor %}
</tbody></table></div>{% else %}<p class="mute" style="margin:0">Nothing analysed yet. <a href="/" style="color:var(--acc)">Analyse a company →</a></p>{% endif %}</div>

{% elif view == 'form' %}
<section class="hero">
  <div>
    <div class="eyebrow"><span class="num">SOC 2 · ISO 27001</span>Lead qualification for compliance automation</div>
    <h1 data-words>Know who's ready for Sprinto <span class="soft">before you write a word.</span></h1>
    <p class="lede reveal">Type a company. We read its website, verify every claim, apply three rules, and hand you a verdict and a cold email built only from evidence.</p>
  </div>
  <div class="orbwrap"><div class="orbshadow"></div><div class="orb" id="orb"></div></div>
</section>
{% if error %}<div class="box warn reveal">{{ error }}</div>{% endif %}
{% if lookup and lookup.tried %}<div class="banner reveal"><span class="mute">Checked:</span>{% for t in lookup.tried[:6] %}<span class="tag">{{ t.url|replace('https://','') }} — {{ t.reason }}</span>{% endfor %}</div>{% endif %}
<div class="reveal">{{ searchbox() }}</div>

<div class="sec reveal"><h2>How it decides</h2><p>The AI reads. Code decides.</p></div>
<div class="grid g4 steps4">
  <div class="card reveal"><span class="n">01</span><b>Find &amp; read</b><span class="mute">Locates the official site, reads the homepage and up to {{ limits[0] }} more pages.</span></div>
  <div class="card reveal"><span class="n">02</span><b>Verify</b><span class="mute">Each claim must be a word-for-word quote from the page. No quote, no claim.</span></div>
  <div class="card reveal"><span class="n">03</span><b>Decide</b><span class="mute">Three rules, applied by code the same way every time.</span></div>
  <div class="card reveal"><span class="n">04</span><b>Draft</b><span class="mute">A named email with two pain points, each tied to a quote.</span></div>
</div>

<div class="grid g3" style="margin-top:14px">
  <div class="card reveal span2"><h3>The three rules</h3><ul class="rules">
    <li><span>1</span><b>Already certified?</b> <span class="mute">Holds SOC 2, ISO 27001… → skip. Working towards it → strong signal.</span></li>
    <li><span>2</span><b>B2B SaaS?</b> <span class="mute">Must sell to businesses. Consumer → skip. Unclear → a human decides.</span></li>
    <li><span>3</span><b>Right stage?</b> <span class="mute">A named funding round, 5+ open roles, or an enterprise plan. Unknown → still a lead, ranked B.</span></li>
  </ul></div>
  <div class="card reveal"><h3>So far</h3>
    <div class="big"><span class="count" data-to="{{ stats.total }}">{{ stats.total }}</span><span class="mute" style="font-size:14px;font-weight:400"> companies</span></div>
    <div class="bar2">{% if stats.total %}<i data-w="{{ (100*stats.qualified/stats.total)|round }}" style="background:var(--ok)"></i><i data-w="{{ (100*stats.review/stats.total)|round }}" style="background:var(--warn)"></i><i data-w="{{ (100*stats.disqualified/stats.total)|round }}" style="background:var(--bad)"></i>{% endif %}</div>
    <div class="mute" style="font-size:12.5px">{{ stats.qualified }} qualified · {{ stats.review }} review · {{ stats.disqualified }} skipped</div>
  </div>
</div>

{% if stats.recent %}
<div class="sec reveal"><h2>Recently analysed</h2><p><a href="/history" style="color:var(--acc)">All history →</a></p></div>
<div class="recent reveal">{% for r in stats.recent[:6] %}<div class="rrow"><span class="mono">{{ r.domain }}</span><span class="tk"><span class="st {{ r.status }}">{{ r.status|replace('_',' ') }}{% if r.rank %} · {{ r.rank }}{% endif %}</span></span><span class="mute">{{ r.ago }}</span></div>{% endfor %}</div>
{% endif %}

{% elif view == 'result' %}
{% if error %}<div class="box bad reveal">{{ error }}</div>{% endif %}
{% if lookup and lookup.url %}<div class="banner reveal">🔎 <span>Found <b>{{ lookup.name }}</b> at <a href="{{ lookup.url }}" target="_blank" rel="noopener noreferrer" style="color:var(--acc)">{{ lookup.url|replace('https://','') }}</a></span>
<span class="mute">verified: {{ lookup.reason }}</span>{% if lookup.alternatives %}<span class="mute">· also: {{ lookup.alternatives|join(', ') }}</span>{% endif %}</div>{% endif %}
{% if research and info %}{% set d = research.decision %}
<section class="verdict reveal {{ {'QUALIFIED':'ok','DISQUALIFIED':'bad'}.get(d.status,'warn') }}">
  <div class="vtop">
    <div><div class="k" style="margin-bottom:10px">Verdict</div>
      <div class="vstatus">{{ {'QUALIFIED':'Qualified','DISQUALIFIED':'Disqualified','MANUAL_REVIEW':'Needs review','FETCH_FAILED':'Couldn’t read site'}.get(d.status, d.status) }}{% if d.rank %}<span class="rank" title="A = stage evidence found, B = stage unknown">{{ d.rank }}</span>{% endif %}</div></div>
    <div class="vco"><b>{{ info.name }}</b><a href="{{ research.company_url }}" target="_blank" rel="noopener noreferrer">{{ info.domain }} ↗</a>
      {% if research.llm_mode == 'mock' %}<div><span class="tag" style="margin-top:6px">mock AI · demo</span></div>{% endif %}</div>
  </div>
  <p class="why">{{ d.summary }}{% if info.sells %} <span class="mute">· {{ info.sells }}</span>{% endif %}</p>
  <div class="next">→ {{ info.next_step }}</div>
  <div class="kpis">
    <div class="kpi"><b><span class="count" data-to="{{ info.good_signals }}">{{ info.good_signals }}</span><span class="mute" style="font-size:14px"> / 8</span></b><span>buying signals</span></div>
    <div class="kpi"><b><span class="count" data-to="{{ info.quality.verified }}">{{ info.quality.verified }}</span></b><span>verified quotes</span></div>
    <div class="kpi"><b>{{ info.pages_ok }}<span class="mute" style="font-size:14px"> / {{ info.pages_total }}</span></b><span>pages read</span></div>
    <div class="kpi"><b>{{ research.extra_fetches }}<span class="mute" style="font-size:14px"> / {{ limits[0] }}</span></b><span>extra pages used</span></div>
  </div>
</section>
{% for f in d.flags %}<div class="box warn reveal">{{ f }}</div>{% endfor %}

<div class="sec reveal"><h2>Evidence Map</h2><p>Stops at the first rule that fails.</p></div>
<div class="stepper">
  {% for q in ['Already certified?','B2B SaaS?','Right stage?'] %}{% set s = info.steps[loop.index0] if loop.index0 < info.steps|length else none %}
  <div class="step reveal {{ s.tone if s else 'skip' }}"><div class="ic">{{ ('✓' if s.tone=='good' else '✕' if s.tone=='bad' else '?') if s else '–' }}</div>
    <b>{{ loop.index }}. {{ q }}</b><span class="a">{{ s.a if s else 'NOT CHECKED' }}</span>
    <div class="mute" style="font-size:13px">{{ s.note if s else 'Skipped: an earlier rule already decided.' }}</div>
    {% if s and s.ids %}<div class="mono mute" style="font-size:11.5px;margin-top:8px">evidence {{ s.ids|join(' ') }}</div>{% endif %}</div>
  {% endfor %}
</div>

<div class="sec reveal"><h2>Signals</h2><p>Hover a card to see the quote behind it.</p></div>
<div class="grid g4">
  {% for s in info.signals %}<div class="sig reveal {{ s.tone }}" tabindex="0"><div class="k">{{ s.label }}<i class="dotg"></i></div>
    <div class="v">{{ s.value }}</div><div class="h">{{ s.hint }}</div>
    {% if s.quote %}<div class="q">“{{ s.quote }}”<br><span style="opacity:.7">{{ s.id }} · {{ s.url|replace('https://','') }}</span></div>{% endif %}</div>{% endfor %}
</div>

<div class="grid g3" style="margin-top:14px">
  <div class="card reveal"><h3>Evidence quality</h3>
    <div style="display:flex;gap:18px;align-items:center">
      <div class="ring" data-p="{{ info.quality.pct }}"><div><b>{{ info.quality.pct }}%</b><span>verified</span></div></div>
      <div class="mute" style="font-size:13px">{{ info.quality.verified }} of {{ info.quality.total }} claims matched the page word-for-word. {% if info.quality.unverified %}{{ info.quality.unverified }} ignored.{% else %}None ignored.{% endif %}</div>
    </div>
    <div style="margin-top:14px;font-size:13px">Facts vs inferences</div>
    {% set tot = info.quality.facts + info.quality.inferences %}
    <div class="bar2">{% if tot %}<i data-w="{{ (100*info.quality.facts/tot)|round }}" style="background:var(--acc)"></i><i data-w="{{ (100*info.quality.inferences/tot)|round }}" style="background:var(--acc2)"></i>{% endif %}</div>
    <div class="mute" style="font-size:12.5px">{{ info.quality.facts }} stated on the page · {{ info.quality.inferences }} concluded</div>
  </div>
  <div class="card reveal"><h3>Research budget</h3>
    <div class="meter"><div class="lbl"><span>Extra pages</span><span class="mono">{{ research.extra_fetches }}/{{ limits[0] }}</span></div>
      <div class="cells">{% for i in range(limits[0]) %}<i class="{{ 'on' if i < research.extra_fetches else '' }}"></i>{% endfor %}</div></div>
    <div class="meter"><div class="lbl"><span>Stage-related pages</span><span class="mono">{{ research.stage_fetches }}/{{ limits[1] }}</span></div>
      <div class="cells">{% for i in range(limits[1]) %}<i class="{{ 'on' if i < research.stage_fetches else '' }}"></i>{% endfor %}</div></div>
    <div class="mute" style="font-size:12.5px">Stopped: {{ research.stop_reason }}</div>
  </div>
  <div class="card reveal"><h3>Sources</h3>
    {% if info.quality.sources %}<div class="src">{% for s in info.quality.sources %}<a href="{{ s.url }}" target="_blank" rel="noopener noreferrer">{{ s.url|replace('https://','') }} ↗</a>{% endfor %}</div>
    {% else %}<p class="mute" style="margin:0">No verified sources.</p>{% endif %}
    {% if info.customers %}<div style="margin-top:14px;font-size:13px"><span class="k">Customers</span><div>{{ info.customers }}</div></div>{% endif %}
  </div>
</div>

<div class="grid g2" style="margin-top:14px">
  <div class="card reveal"><h3>How the agent worked</h3><div class="timeline">
    {% for t in info.trail %}<div class="tl {{ t.tone }}"><span class="ic">{{ t.icon }}</span><b>{{ t.title }}</b>{% if t.detail %}<p>{{ t.detail }}</p>{% endif %}{% if t.why %}<p>“{{ t.why }}”</p>{% endif %}</div>{% endfor %}
  </div></div>
  <div class="card reveal"><h3>All findings</h3>
    <p class="mute" style="margin-top:-4px">{{ info.quality.total }} claims · fact = stated, inference = concluded.</p>
    <div class="scroll" style="max-height:420px;overflow:auto"><table><thead><tr><th>ID</th><th>Claim</th><th>Kind</th><th>✓</th></tr></thead><tbody>
    {% for f in findings %}<tr{% if not f.verified %} style="opacity:.5"{% endif %} title="“{{ f.quote }}” — {{ f.source_url }}"><td class="mono">{{ f.id }}</td>
      <td>{{ f.value }}<div class="mute" style="font-size:11.5px">{{ f.field|replace('_',' ') }} · <a href="{{ f.source_url }}" target="_blank" rel="noopener noreferrer">source ↗</a></div></td>
      <td><span class="tag">{{ f.kind }}</span></td><td>{% if f.verified %}<span class="tag yes">✓</span>{% else %}<span class="tag no">✗</span>{% endif %}</td></tr>
    {% else %}<tr><td colspan="4">No findings.</td></tr>{% endfor %}</tbody></table></div>
  </div>
</div>

<details class="reveal"><summary data-sound="toggle">Raw pages read ({{ research.pages|length }})</summary>
{% for p in research.pages %}<p style="margin:10px 0 4px"><b>{{ p.url }}</b> <span class="mute">— {{ p.get('purpose') }} · {{ p.status }}{% if p.get('counted_as_stage') %} · stage fetch{% endif %}</span></p>
{% if p.get('errors') %}<p class="mute">{{ p.errors|join('; ') }}</p>{% endif %}<pre>{{ (p.get('text') or '')[:1500] }}</pre>{% endfor %}</details>
{% endif %}

{% if outreach %}
<div class="sec reveal"><h2>Outreach</h2><p>Nothing goes to the prospect.</p></div>
{% if outreach.get('error') %}<div class="box bad reveal">{{ outreach.error }}</div>{% endif %}
{% if outreach.get('skipped') %}<div class="box warn reveal">{{ outreach.skipped }}</div>{% endif %}
{% set e = outreach.get('email') %}
{% if e or outreach.get('contacts') %}
<div class="grid g3">
  {% if outreach.get('contacts') %}{% set ch = outreach.chosen %}<div class="card reveal"><h3>Decision-maker{{ ' · mock' if outreach.mode == 'mock' else '' }}</h3>
    {% if ch %}<div class="contact"><div class="avatar">{{ (ch.full_name or '?')[:1] }}</div>
      <div><b>{{ ch.full_name }}</b><div class="mute">{{ ch.position }}</div><div class="mono mute" style="font-size:12px">{{ ch.email }}</div></div></div>{% endif %}
    <p class="mute" style="font-size:12.5px;margin:0">{{ outreach.reason }}</p>
  </div>{% endif %}
  {% if e %}<div class="reveal" style="{{ 'grid-column:span 2' if outreach.get('contacts') else 'grid-column:1/-1' }}">
    <div class="mail"><div class="hd"><span>Draft for {{ e.contact.full_name if e.contact else 'the contact' }} · <span class="tag">{{ e.status|replace('_',' ') }}</span></span><b>{{ e.subject }}</b></div><div class="bd">{{ e.body }}</div></div>
    {% for i in e.issues %}<div class="box warn">{{ i }}</div>{% endfor %}
  </div>{% endif %}
</div>
{% endif %}
{% if e %}
<div class="grid g2" style="margin-top:14px">
  <div class="card reveal"><h3>Why these pain points</h3><ul class="pain">
    {% for p in e.pain_points %}<li><b>{{ p.pain_point }}</b><div class="mute" style="font-size:13px">{{ p.reasoning }}</div><ul>
    {% for i in p.evidence_ids %}{% set ev = evidence.get(i) %}<li>{% if ev %}<span class="mono">{{ i }}</span> “{{ ev.quote }}”{% else %}{{ i }}: unknown{% endif %}</li>{% endfor %}</ul></li>{% endfor %}</ul></div>
  <div class="card reveal"><h3>Send a test</h3>
    {% if send_to and outreach.get('email_id') %}
    <form method="post" action="/send">
      <input type="hidden" name="email_id" value="{{ outreach.email_id }}">
      <p class="mute" style="margin-top:-4px">Goes to a pre-approved test inbox only, with [TEST] in the subject. One send per draft.</p>
      <label class="field"><span>Send to</span><select name="to">{% for m in send_to %}<option value="{{ loop.index0 }}">{{ m }}</option>{% endfor %}</select></label>
      <label class="toggle" style="margin:4px 0 14px"><input type="checkbox" name="approve" value="1" required data-sound="toggle">I approve sending this as a test</label>
      <button class="btn" data-sound="click">Send test email <span class="arr">→</span></button>
    </form>
    {% else %}<p class="mute" style="margin:0">Test sending isn't configured on this server.</p>{% endif %}
  </div>
</div>
{% endif %}
{% endif %}

<div class="sec reveal"><h2>Analyse another</h2><p></p></div>
<div class="reveal">{{ searchbox() }}</div>
{% endif %}
</main>

<footer>
  <div class="fwrap">
    <div><h4>About this project</h4>
      <p>Mesa School of Business · AI assignment: <b>Sprinto Cold Outreach at Scale</b>.</p>
      <p>Seven steps: scrape → extract (AI) → verify quotes → Evidence Map (code) → agent loop (max {{ limits[0] }} extra pages, {{ limits[1] }} for stage, no duplicates) → contact (Hunter.io) → evidence-checked email → test send (Resend, approved inboxes only).</p>
      <p>Demo companies are fictional. Mock contacts are labelled. Prospects are never emailed.</p></div>
    <div><h4>Stack</h4>
      <p>Python · Flask on Vercel (Streamlit locally) · SQLite kept with Vercel Blob · Gemini with fallback models (Claude-ready) · Hunter.io · Resend.</p>
      <p><a href="https://github.com/prernaarora-design1515/sprinto-outreach" target="_blank" rel="noopener noreferrer">Source code &amp; README ↗</a></p></div>
    <div><h4>Live status</h4>{{ chips() }}</div>
  </div>
</footer>

<div class="loading" id="loading" aria-live="polite"><div class="inner">
  <div class="orbwrap"><div class="orbshadow"></div><div class="orb"></div></div>
  <div class="term" id="term"><div>find the official website</div><div>read the homepage</div><div>extract &amp; verify quotes</div>
    <div>apply the Evidence Map</div><div>read missing pages (max {{ limits[0] }})</div><div>draft the email</div></div>
  <div class="elapsed">Usually 1–3 minutes · <span id="secs">0</span>s</div>
</div></div>

<script>
(function(){
  var reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
  function store(k,v){try{if(v===undefined)return localStorage.getItem(k);localStorage.setItem(k,v);}catch(e){return null;}}
  /* sound */
  var ctx=null,soundOn=store('sound')!=='off';
  function tone(f,d,type,vol,slide){if(!soundOn)return;try{ctx=ctx||new(window.AudioContext||window.webkitAudioContext)();if(ctx.state==='suspended')ctx.resume();
    var t=ctx.currentTime,o=ctx.createOscillator(),g=ctx.createGain();o.type=type||'sine';o.frequency.setValueAtTime(f,t);if(slide)o.frequency.exponentialRampToValueAtTime(slide,t+d);
    g.gain.setValueAtTime(.0001,t);g.gain.exponentialRampToValueAtTime(vol||.08,t+.008);g.gain.exponentialRampToValueAtTime(.0001,t+d);o.connect(g).connect(ctx.destination);o.start(t);o.stop(t+d+.02);}catch(e){}}
  var S={click:function(){tone(520,.09,'sine',.09,260)},toggle:function(){tone(700,.05,'triangle',.05);setTimeout(function(){tone(1050,.06,'triangle',.04)},45)},
    hover:function(){tone(1400,.025,'sine',.012)},on:function(){tone(440,.08,'sine',.07);setTimeout(function(){tone(660,.1,'sine',.07)},70)},
    done:function(){[523,659,784].forEach(function(f,i){setTimeout(function(){tone(f,.18,'sine',.05)},i*90)})}};
  document.addEventListener('click',function(e){var el=e.target.closest('[data-sound]');if(el)(S[el.dataset.sound]||S.click)();});
  var lh=0;document.addEventListener('mouseover',function(e){var el=e.target.closest('.btn,.icon,.nav a,.chipbtn,summary,.sig');if(el&&Date.now()-lh>60){lh=Date.now();S.hover();}});
  var toastEl=document.getElementById('toast'),tt;function toast(m){toastEl.textContent=m;toastEl.classList.add('on');clearTimeout(tt);tt=setTimeout(function(){toastEl.classList.remove('on')},1400);}
  function paintSound(){document.querySelectorAll('[data-snd]').forEach(function(b){b.setAttribute('aria-pressed',String((b.dataset.snd==='on')===soundOn));});}
  document.querySelectorAll('[data-snd]').forEach(function(b){b.addEventListener('click',function(){soundOn=b.dataset.snd==='on';store('sound',soundOn?'on':'off');paintSound();if(soundOn)S.on();toast(soundOn?'Sound on':'Sound off');});});
  paintSound();
  /* theme */
  var root=document.documentElement;function paintTheme(){var dark=root.dataset.theme!=='light';document.getElementById('sun').style.display=dark?'block':'none';document.getElementById('moon').style.display=dark?'none':'block';}
  document.getElementById('themeBtn').addEventListener('click',function(){root.dataset.theme=root.dataset.theme==='light'?'dark':'light';store('theme',root.dataset.theme);paintTheme();S.toggle();toast(root.dataset.theme==='light'?'Light mode':'Dark mode');});
  paintTheme();
  /* headline words */
  document.querySelectorAll('[data-words]').forEach(function(h){var i=0;(function walk(n){Array.prototype.slice.call(n.childNodes).forEach(function(c){if(c.nodeType===3){var fr=document.createDocumentFragment();
    c.textContent.split(/(\s+)/).forEach(function(w){if(!w.trim()){fr.appendChild(document.createTextNode(w));return;}var s=document.createElement('span');s.className='w';s.textContent=w;s.style.animationDelay=(.15+i++*.06)+'s';fr.appendChild(s);});
    c.parentNode.replaceChild(fr,c);}else walk(c);});})(h);});
  /* reveal + animated bars/rings when visible */
  function activate(el){el.classList.add('in');el.querySelectorAll('[data-w]').forEach(function(b){b.style.width=b.dataset.w+'%';});
    el.querySelectorAll('.ring').forEach(function(r){r.style.setProperty('--p',r.dataset.p);});}
  var io='IntersectionObserver' in window?new IntersectionObserver(function(es){es.forEach(function(en){if(en.isIntersecting){activate(en.target);io.unobserve(en.target);}});},{threshold:.08,rootMargin:'0px 0px -40px 0px'}):null;
  document.querySelectorAll('.reveal').forEach(function(el,i){el.style.transitionDelay=Math.min((i%6)*.06,.36)+'s';if(io&&!reduce)io.observe(el);else activate(el);});
  /* spotlight, orb tilt, magnetic button */
  document.addEventListener('pointermove',function(e){var c=e.target.closest('.card');if(!c)return;var r=c.getBoundingClientRect();c.style.setProperty('--mx',(e.clientX-r.left)+'px');c.style.setProperty('--my',(e.clientY-r.top)+'px');});
  var orb=document.getElementById('orb');if(orb&&!reduce)document.addEventListener('pointermove',function(e){var x=e.clientX/innerWidth-.5,y=e.clientY/innerHeight-.5;orb.style.setProperty('--ry',(x*22)+'deg');orb.style.setProperty('--rx',(-y*22)+'deg');});
  document.querySelectorAll('.magnetic').forEach(function(b){if(reduce)return;b.addEventListener('pointermove',function(e){var r=b.getBoundingClientRect();b.style.transform='translate('+((e.clientX-r.left-r.width/2)*.15)+'px,'+((e.clientY-r.top-r.height/2)*.25)+'px)';});b.addEventListener('pointerleave',function(){b.style.transform='';});});
  /* count-ups */
  document.querySelectorAll('.count').forEach(function(el){var to=+el.dataset.to;if(reduce||!to)return;var n=0,step=Math.max(1,Math.round(to/20));el.textContent='0';var t=setInterval(function(){n=Math.min(to,n+step);el.textContent=n;if(n>=to)clearInterval(t);},45);});
  /* loading overlay (the request itself is unchanged) */
  document.querySelectorAll('form[action="/run"]').forEach(function(form){form.addEventListener('submit',function(){
    var btn=form.querySelector('.runbtn');if(btn){btn.disabled=true;btn.firstChild.textContent='Analysing… ';}
    document.getElementById('loading').classList.add('on');var lines=document.querySelectorAll('#term div'),k=0,s=0;lines[0].classList.add('on');
    setInterval(function(){s++;document.getElementById('secs').textContent=s;if(s%9===0&&k<lines.length-1){lines[k].classList.remove('on');lines[k].classList.add('done');k++;lines[k].classList.add('on');S.hover();}},1000);});});
  if(document.querySelector('.verdict'))setTimeout(function(){S.done();},500);
})();
</script>
</body></html>
"""
