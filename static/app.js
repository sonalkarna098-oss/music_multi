const state = {instruments:["piano"]};
const $ = id => document.getElementById(id);
document.querySelectorAll(".instrument").forEach(btn => btn.addEventListener("click", () => {
  const key = btn.dataset.instrument;
  const chosen = new Set(state.instruments);
  if (chosen.has(key)) {
    if (chosen.size === 1) { $("status").textContent = "Select at least one instrument."; return; }
    chosen.delete(key);
  } else { chosen.add(key); }
  state.instruments = [...chosen];
  btn.classList.toggle("selected", chosen.has(key));
  btn.setAttribute("aria-pressed", String(chosen.has(key)));
  $("status").textContent = `${state.instruments.length} instrument${state.instruments.length === 1 ? "" : "s"} selected.`;
}));
$("bpm").addEventListener("input", () => $("bpm-out").textContent = `${$("bpm").value} BPM`);
document.querySelectorAll(".prompt-examples button").forEach(btn => btn.addEventListener("click", () => {
  $("idea").value = btn.dataset.prompt; $("idea").focus();
}));
function settings() {
 return {instruments:state.instruments,key:$("key").value,scale:$("scale").value,
 bpm:Number($("bpm").value),bars:Number($("bars").value),octave:Number($("octave").value),seed:Number($("seed").value)||0};
}
function applySettings(s) {
 if (!s) throw new Error("AI did not return music settings.");
 const chosen = Array.isArray(s.instruments) ? s.instruments : [s.instrument || "piano"];
 const allowed = ["piano","guitar","drums","flute","trumpet","bass","violin","strings"];
 if (!chosen.length || chosen.some(k => !allowed.includes(k))) throw new Error("AI suggested an unsupported instrument.");
 state.instruments = [...new Set(chosen)];
 document.querySelectorAll(".instrument").forEach(b => {
   const active = state.instruments.includes(b.dataset.instrument);
   b.classList.toggle("selected", active);
   b.setAttribute("aria-pressed", String(active));
 });
 ["key","scale","bpm","bars","octave","seed"].forEach(k=>{if(s[k]!==undefined)$(k).value=s[k]});
 $("bpm-out").textContent=`${$("bpm").value} BPM`;
}
function showInfo(info) {
 $("track-info").classList.remove("hidden");
 $("track-info").textContent=`${info.instruments.join(" + ")} · ${info.key} ${info.scale} · ${info.bpm} BPM · ${info.bars} bars · ${info.duration_seconds}s · ${info.note_count} notes`;
}
$("generate").addEventListener("click", async () => {
 const btn=$("generate"); btn.disabled=true; btn.firstChild.textContent="Generating…";
 $("status").textContent="Creating your MIDI pattern…";
 $("download").classList.add("hidden");
 try {
   const r=await fetch("/api/generate",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(settings())});
   const data=await r.json(); if(!r.ok||!data.ok)throw new Error(data.error||"Could not generate track.");
   $("status").textContent="Your track is ready. Download the MIDI and open it in a MIDI player or music application.";
   showInfo(data.info); $("download").href=data.download_url; $("download").classList.remove("hidden");
 } catch(e){$("status").textContent=e.message}
 finally{btn.disabled=false;btn.firstChild.textContent="Generate music "}
});
$("suggest").addEventListener("click", async () => {
 const prompt=$("idea").value.trim(); if(!prompt){$("status").textContent="Describe the music you want first.";return}
 const btn=$("suggest");btn.disabled=true;btn.firstChild.textContent="Thinking…";
 $("status").textContent="Asking the AI to suggest musical settings…";
 try {
   const r=await fetch("/api/ai-prompt",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({prompt})});
   const data=await r.json();if(!r.ok||!data.ok)throw new Error(data.error||"AI request failed.");
   applySettings(data.settings);$("status").textContent="AI suggested settings have been applied. Click Generate music to create the MIDI track.";
   showInfo(data.summary);$("download").classList.add("hidden");
 } catch(e){$("status").textContent=e.message}
 finally{btn.disabled=false;btn.firstChild.textContent="Suggest settings with AI "}
});
