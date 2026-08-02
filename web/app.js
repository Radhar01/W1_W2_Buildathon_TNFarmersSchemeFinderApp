/* =========================================================================
   app.js  —  All the behaviour for the schemes portal.

   It talks to the SAME FastAPI backend as before:
     GET  /api/schemes        -> list for the cards + left navigation
     GET  /api/schemes/{id}   -> full details of one scheme
     POST /api/chat           -> chatbot answer (WITH memory)

   Because the page is served by FastAPI itself, we can use plain relative
   URLs like "/api/schemes" — no separate address, no CORS to worry about.
   ========================================================================= */

/* -------------------------------------------------------------------------
   1. UI TEXT in both languages (scheme content itself comes from the API)
   ------------------------------------------------------------------------- */
const T = {
  ta: {
    strip: "தமிழ்நாடு அரசு · வேளாண்மைத் துறை",
    portal_title: "வேளாண் நல திட்டங்கள்",
    portal_subtitle: "தமிழ்நாடு விவசாயிகள் நல திட்டங்கள் இணையதளம்",
    nav_home: "முகப்பு",
    hero_badge: "தமிழ்நாடு விவசாயிகளுக்காக",
    hero_title: "உங்கள் ஒவ்வொரு பருவத்திற்கும் ஆதரவளிக்கும் திட்டங்கள்",
    hero_text: "தமிழ்நாடு வேளாண்மைத் துறையின் நல திட்டங்களை அறியுங்கள் — மானியங்கள், காப்பீடு, மண் ஆரோக்கியம், நீர்ப்பாசனம் மற்றும் பல. விவரங்களைக் காண எந்த திட்டத்தையும் தேர்ந்தெடுக்கவும்.",
    browse_head: "திட்டங்களைப் பார்க்கவும்",
    browse_hint: "முழு விவரங்களைக் காண ஒரு திட்டத்தைத் தேர்ந்தெடுக்கவும்.",
    view_details: "விவரங்களைக் காண →",
    back: "← அனைத்து திட்டங்களுக்கும் திரும்பு",
    all_schemes: "அனைத்து திட்டங்கள்",
    search_ph: "🔍 திட்டங்களைத் தேடுங்கள்…",
    no_results: "பொருத்தம் எதுவும் இல்லை",
    category: "வகை",
    benefits: "நன்மைகள்",
    eligibility: "தகுதி",
    officers: "யாரைத் தொடர்பு கொள்ள வேண்டும்",
    districts: "மாவட்டங்கள்",
    chat_title: "திட்ட உதவியாளர்",
    chat_welcome: "வணக்கம்! திட்டங்கள் குறித்து எதையும் கேளுங்கள். எடுத்துக்காட்டு: \"சொட்டு நீர்ப்பாசனத்திற்கு என்ன மானியம்?\"",
    chat_ph: "உங்கள் கேள்வியைத் தட்டச்சு செய்யவும்…",
    chat_clear: "அழி",
    chat_sources: "தொடர்புடைய திட்டங்கள்",
    thinking: "பதிலைத் தயாரிக்கிறது…",
    connect_error: "சேவையகத்துடன் இணைக்க முடியவில்லை. பின்பக்க (backend) சேவையகம் இயங்குகிறதா எனச் சரிபார்க்கவும்.",
    footer: "தமிழ்நாடு வேளாண்மைத் துறை · விவசாயிகள் நல திட்டங்கள் இணையதளம் · மாதிரி தரவு",
  },
  en: {
    strip: "Government of Tamil Nadu · Department of Agriculture",
    portal_title: "Farmers' Welfare Schemes",
    portal_subtitle: "Tamil Nadu Farmers' Welfare Schemes Portal",
    nav_home: "Home",
    hero_badge: "FOR THE FARMERS OF TAMIL NADU",
    hero_title: "Schemes that support every season of your work",
    hero_text: "Explore the welfare schemes offered by the Tamil Nadu Department of Agriculture — subsidies, insurance, soil health, irrigation and more. Tap any scheme to see its full details.",
    browse_head: "Browse schemes",
    browse_hint: "Pick a scheme to open its full details page.",
    view_details: "View details →",
    back: "← Back to all schemes",
    all_schemes: "All schemes",
    search_ph: "🔍 Search schemes…",
    no_results: "No matches",
    category: "Category",
    benefits: "Benefits",
    eligibility: "Eligibility",
    officers: "Whom to contact",
    districts: "Districts",
    chat_title: "Scheme Helper",
    chat_welcome: "Hello! Ask me anything about the schemes. For example: \"What subsidy is there for drip irrigation?\"",
    chat_ph: "Type your question…",
    chat_clear: "Clear",
    chat_sources: "Related schemes",
    thinking: "Preparing the answer…",
    connect_error: "Could not reach the server. Please check that the backend is running.",
    footer: "Tamil Nadu Department of Agriculture · Farmers' Welfare Schemes Portal · Sample data",
  }
};

/* -------------------------------------------------------------------------
   2. PHOTOS  (free, openly-licensed Wikimedia Commons images of TN farming).
   Special:FilePath gives a stable link; ?width keeps the download small.
   Every <img> also has an onerror fallback so a missing photo never breaks
   the layout — the coloured tile with an icon shows instead.
   ------------------------------------------------------------------------- */
const FP = "https://commons.wikimedia.org/wiki/Special:FilePath/";
const PHOTO = {
  transplant: FP + encodeURIComponent("Paddy transplantation in Tamil Nadu.jpg"),
  farmer:     FP + encodeURIComponent("A Farmer in Tamil Nadu.JPG"),
  cows:       FP + encodeURIComponent("A farmer and his cows.jpg"),
  lush:       FP + encodeURIComponent("A Lush Paddy field in VEDAL.jpg"),
  colorful:   FP + encodeURIComponent("A colorful Paddy field.JPG"),
  metured:    FP + encodeURIComponent("A metured paddy field in tamilnadu.jpg"),
};
function img(url, w){ return url + "?width=" + w; }

// Each scheme category gets an icon, an accent gradient and a thumbnail photo.
const CATEGORY_STYLE = {
  "Enterprise & Infrastructure": {icon:"🏗️", tile:"linear-gradient(135deg,#00695c,#26a69a)", photo:PHOTO.cows},
  "Extension & Training":        {icon:"🎓", tile:"linear-gradient(135deg,#1565c0,#42a5f5)", photo:PHOTO.farmer},
  "Improving Soil Health":       {icon:"🧪", tile:"linear-gradient(135deg,#6d4c2b,#a1887f)", photo:PHOTO.metured},
  "Increasing Crop Productivity":{icon:"🌱", tile:"linear-gradient(135deg,#2e7d32,#7cb342)", photo:PHOTO.lush},
  "Insurance & Risk Protection": {icon:"🛡️", tile:"linear-gradient(135deg,#7b1fa2,#ab47bc)", photo:PHOTO.colorful},
  "National Food Security Mission":{icon:"🌾", tile:"linear-gradient(135deg,#8d6e00,#d4a017)", photo:PHOTO.transplant},
  "Organic Farming":             {icon:"🍃", tile:"linear-gradient(135deg,#33691e,#8bc34a)", photo:PHOTO.lush},
  "Plant Protection":            {icon:"🐛", tile:"linear-gradient(135deg,#558b2f,#9ccc65)", photo:PHOTO.metured},
  "Quality Seed Production":     {icon:"🌰", tile:"linear-gradient(135deg,#a1651a,#e0a44b)", photo:PHOTO.colorful},
  "RKVY & Development Projects": {icon:"📈", tile:"linear-gradient(135deg,#283593,#5c6bc0)", photo:PHOTO.farmer},
  "Seed Programmes":             {icon:"🌾", tile:"linear-gradient(135deg,#8d6e00,#d4a017)", photo:PHOTO.transplant},
};
function styleFor(cat){
  return CATEGORY_STYLE[cat] || {icon:"🌾", tile:"linear-gradient(135deg,#2e7d32,#7cb342)", photo:PHOTO.lush};
}

/* -------------------------------------------------------------------------
   3. STATE
   ------------------------------------------------------------------------- */
let lang = localStorage.getItem("lang") || "ta";   // Tamil is the default
let schemes = [];              // short list for cards + nav
let current = null;            // id of the scheme open on the detail page
let chatHistory = [];          // memory: [{role:'user'/'assistant', content:'...'}]

/* -------------------------------------------------------------------------
   4. SMALL HELPERS
   ------------------------------------------------------------------------- */
const $ = (id) => document.getElementById(id);
function titleOf(s){ return lang === "ta" ? s.title_ta : s.title_en; }
function catOf(s){ return lang === "ta" ? s.category_ta : s.category_en; }
function sumOf(s){ return lang === "ta" ? s.summary_ta : s.summary_en; }
function esc(str){ const d=document.createElement("div"); d.textContent=str; return d.innerHTML; }

async function api(path, options){
  const r = await fetch(path, options);
  if(!r.ok) throw new Error("HTTP " + r.status);
  return r.json();
}

/* -------------------------------------------------------------------------
   5. LANGUAGE
   ------------------------------------------------------------------------- */
function setLang(newLang){
  lang = newLang;
  localStorage.setItem("lang", lang);
  document.documentElement.lang = lang;
  applyLabels();
  renderCards();
  if(!$("detail-view").classList.contains("hidden")){ renderNav(); renderContent(); }
}

function applyLabels(){
  const t = T[lang];
  $("lang-ta").classList.toggle("on", lang==="ta");
  $("lang-en").classList.toggle("on", lang==="en");
  $("strip-text").textContent = t.strip;
  $("portal-title").textContent = t.portal_title;
  $("portal-subtitle").textContent = t.portal_subtitle;
  $("nav-home").textContent = t.nav_home;
  $("hero-badge").textContent = t.hero_badge;
  $("hero-title").textContent = t.hero_title;
  $("hero-text").textContent = t.hero_text;
  $("browse-head").textContent = t.browse_head;
  $("browse-hint").textContent = t.browse_hint;
  $("nav-title").textContent = t.all_schemes;
  $("nav-search").placeholder = t.search_ph;
  $("chat-title").textContent = t.chat_title;
  $("chat-clear").textContent = t.chat_clear;
  $("chat-input").placeholder = t.chat_ph;
  $("fab").title = t.chat_title;
  $("footer").textContent = t.footer;
}

/* -------------------------------------------------------------------------
   6. HERO farmer photos (inside the header area)
   ------------------------------------------------------------------------- */
function buildHero(){
  // Big background photo of farmers at work, with graceful fallback.
  const hero = $("hero");
  const test = new Image();
  test.onload = () => {
    hero.style.setProperty("--hero-photo", `url("${img(PHOTO.transplant,1600)}")`);
    hero.classList.add("has-photo");
  };
  test.src = img(PHOTO.transplant, 1600);

  // A small row of farmer thumbnails.
  const shots = [PHOTO.transplant, PHOTO.farmer, PHOTO.cows, PHOTO.colorful];
  $("hero-photos").innerHTML = shots.map(u =>
    `<img src="${img(u,200)}" alt="Tamil Nadu farming" loading="lazy"
          onerror="this.style.display='none'">`
  ).join("");
}

/* -------------------------------------------------------------------------
   7. HOME:  scheme cards
   ------------------------------------------------------------------------- */
function renderCards(){
  const t = T[lang];
  $("cards").innerHTML = schemes.map(s => {
    const st = styleFor(s.category_en);
    return `
      <div class="card" tabindex="0" role="button"
           onclick="openDetail('${s.id}')"
           onkeydown="if(event.key==='Enter')openDetail('${s.id}')">
        <div class="thumb" style="--tile:${st.tile}">
          <img src="${img(st.photo,500)}" alt="" loading="lazy"
               onload="this.parentNode.querySelector('.ic').style.display='none'"
               onerror="this.style.display='none'">
          <span class="ic">${st.icon}</span>
        </div>
        <div class="body">
          <div class="cat">${esc(catOf(s))}</div>
          <h3>${esc(titleOf(s))}</h3>
          <p class="sm">${esc(sumOf(s))}</p>
          <div class="go">${t.view_details}</div>
        </div>
      </div>`;
  }).join("");
}

/* -------------------------------------------------------------------------
   8. DETAIL:  left nav (search + highlight) and right content
   ------------------------------------------------------------------------- */
function renderNav(){
  const t = T[lang];
  const q = ($("nav-search").value || "").toLowerCase();
  const list = schemes.filter(s => {
    const hay = (s.title_en + s.title_ta + s.category_en + s.category_ta).toLowerCase();
    return hay.includes(q);
  });
  $("navlist").innerHTML = list.length
    ? list.map(s => `
        <li class="${s.id===current ? 'active':''}" onclick="openDetail('${s.id}')">
          ${esc(titleOf(s))}
        </li>`).join("")
    : `<li style="color:#999;cursor:default">${t.no_results}</li>`;
}

async function renderContent(){
  const t = T[lang];
  let s;
  try{
    s = await api(`/api/schemes/${current}`);
  }catch(e){
    $("content").innerHTML = `<p>${t.connect_error}</p>`;
    return;
  }
  const title = lang==="ta" ? s.title_ta : s.title_en;
  const category = lang==="ta" ? s.category_ta : s.category_en;
  const summary = lang==="ta" ? s.summary_ta : s.summary_en;
  const benefits = lang==="ta" ? s.benefits_ta : s.benefits_en;
  const elig = lang==="ta" ? s.eligibility_ta : s.eligibility_en;
  const officers = lang==="ta" ? s.officers_ta : s.officers_en;
  const districts = s.districts_en || "";

  const li = (arr) => (arr||[]).map(x => `<li>${esc(x)}</li>`).join("");

  $("content").innerHTML = `
    <button class="back" onclick="showHome()">${t.back}</button>
    <div><span class="cat">${t.category}: ${esc(category)}</span></div>
    <h2>${esc(title)}</h2>
    <p class="lead">${esc(summary)}</p>
    <div class="flabel">✅ ${t.benefits}</div>
    <ul>${li(benefits)}</ul>
    <div class="flabel">📋 ${t.eligibility}</div>
    <ul>${li(elig)}</ul>
    <div class="flabel">👤 ${t.officers}</div>
    <ul>${li(officers)}</ul>
    <div class="flabel">📍 ${t.districts}</div>
    <p>${esc(districts)}</p>`;
}

function openDetail(id){
  current = id;
  $("home-view").classList.add("hidden");
  $("detail-view").classList.remove("hidden");
  $("nav-search").value = "";
  renderNav();
  renderContent();
  window.scrollTo({top:0, behavior:"smooth"});
}

function showHome(){
  $("detail-view").classList.add("hidden");
  $("home-view").classList.remove("hidden");
  window.scrollTo({top:0, behavior:"smooth"});
}

/* -------------------------------------------------------------------------
   9. CHAT  (floating, on every view, WITH memory)
   ------------------------------------------------------------------------- */
function toggleChat(){ $("chat").classList.toggle("open"); }

function seedChatIfEmpty(){
  if($("chat-log").children.length === 0){
    addBubble("bot", T[lang].chat_welcome);
  }
}

function addBubble(role, text, sourcesHtml){
  const div = document.createElement("div");
  div.className = "bubble " + (role==="me" ? "me" : "bot");
  div.textContent = text;
  if(sourcesHtml){
    const s = document.createElement("span");
    s.className = "src";
    s.textContent = sourcesHtml;
    div.appendChild(s);
  }
  $("chat-log").appendChild(div);
  $("chat-log").scrollTop = $("chat-log").scrollHeight;
  return div;
}

function clearChat(){
  chatHistory = [];
  $("chat-log").innerHTML = "";
  addBubble("bot", T[lang].chat_welcome);
}

async function sendChat(){
  const input = $("chat-input");
  const q = input.value.trim();
  if(!q) return;
  input.value = "";

  addBubble("me", q);

  // Show a temporary "typing…" line
  const typing = document.createElement("div");
  typing.className = "typing";
  typing.textContent = T[lang].thinking;
  $("chat-log").appendChild(typing);
  $("chat-log").scrollTop = $("chat-log").scrollHeight;

  try{
    // Send the whole history so the bot REMEMBERS the conversation.
    const result = await api("/api/chat", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ question: q, lang: lang, history: chatHistory })
    });
    typing.remove();

    let answer = result.answer || "";
    // Turn the returned scheme ids into readable titles.
    let srcText = "";
    if(result.sources && result.sources.length){
      const titles = result.sources
        .map(id => { const m = schemes.find(x => x.id === id); return m ? titleOf(m) : null; })
        .filter(Boolean);
      if(titles.length) srcText = T[lang].chat_sources + ": " + titles.join("; ");
    }
    addBubble("bot", answer, srcText);

    // Update memory with this turn.
    chatHistory.push({role:"user", content:q});
    chatHistory.push({role:"assistant", content:answer});
    // Keep memory to a sensible length.
    if(chatHistory.length > 12) chatHistory = chatHistory.slice(-12);
  }catch(e){
    typing.remove();
    addBubble("bot", T[lang].connect_error);
  }
}

/* -------------------------------------------------------------------------
   10. START-UP
   ------------------------------------------------------------------------- */
async function init(){
  document.documentElement.lang = lang;
  applyLabels();
  buildHero();
  seedChatIfEmpty();
  try{
    const data = await api("/api/schemes");
    schemes = data.schemes || [];
    renderCards();
  }catch(e){
    $("cards").innerHTML = `<p style="color:#b00">${T[lang].connect_error}</p>`;
  }
}
init();
