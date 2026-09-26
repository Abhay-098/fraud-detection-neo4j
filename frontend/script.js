const $=id=>document.getElementById(id);
async function get(url){const r=await fetch(url);if(!r.ok)throw new Error(await r.text());return r.json()}
async function post(url,body){const r=await fetch(url,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});if(!r.ok)throw new Error(await r.text());return r.json()}
function rows(el, headers, data, fields){
  el.innerHTML=`<div class="row head">${headers.map(x=>`<div>${x}</div>`).join("")}</div>`+
    data.map(d=>`<div class="row">${fields.map(f=>`<div>${Array.isArray(d[f])?d[f].slice(0,4).join(", "):d[f]??"—"}</div>`).join("")}</div>`).join("");
}
function renderRings(data){
  $("ringsTable").innerHTML=data.length?data.map(r=>`<div class="ring-card"><div class="ring-title"><span>${r.ring_id}</span><span>${r.risk_level} · ${r.ring_score}/100</span></div><div>${r.member_count} accounts · ${r.internal_transfers} internal transfers · amount ${Number(r.internal_amount||0).toLocaleString()}</div><div class="ring-members">${(r.accounts||[]).join(", ")}</div></div>`).join(""):'<div class="muted">No candidate rings found with the current criteria.</div>';
}
async function load(){
  try{
    const h=await get("/api/health");$("dot").style.background=h.neo4j?"#6ee7b7":"#fbbf24";$("health").textContent=h.neo4j?"API + Neo4j connected":"API online / Neo4j unavailable";
    const s=await get("/api/summary");$("customers").textContent=(s.customers??0).toLocaleString();$("accounts").textContent=(s.accounts??0).toLocaleString();$("transactions").textContent=(s.transactions??0).toLocaleString();$("fraud").textContent=(s.fraud_transactions??0).toLocaleString();$("devices").textContent=(s.devices??0).toLocaleString();
    rows($("riskTable"),["Account","Txns","Peers","Risk"],await get("/api/fraud/high-risk-accounts?limit=8"),["account","tx_count","shared_device_peers","risk_indicator"]);
    rows($("devicesTable"),["Device","Accounts","Members"],await get("/api/fraud/shared-devices?limit=8"),["device","account_count","accounts"]);
    renderRings(await get("/api/fraud/rings?limit=8"));
    rows($("txTable"),["Transaction","Type","Origin","Destination","Amount","Fraud"],await get("/api/transactions?limit=12"),["transaction_id","type","origin","destination","amount","is_fraud"]);
  }catch(e){$("health").textContent="API/Neo4j unavailable";console.error(e)}
}
$("analysisForm").addEventListener("submit",async e=>{
  e.preventDefault();const out=$("analysisResult");out.innerHTML='<span class="muted">Analyzing graph context…</span>';
  try{
    const r=await post("/api/fraud/analyze",{origin:$("anOrigin").value.trim(),destination:$("anDestination").value.trim(),amount:Number($("anAmount").value),type:$("anType").value});
    out.innerHTML=`<div class="scoreline"><span class="score">${r.risk_score}/100</span><span class="pill">${r.risk_level} RISK</span><strong>${r.flagged?'FLAG FOR INVESTIGATION':'No high-risk flag'}</strong></div><ul class="indicators">${r.indicators.map(x=>`<li>${x.replaceAll('_',' ')}</li>`).join('')}</ul><div class="muted">Shared-device peers: ${r.evidence.shared_device_peers} · Origin transactions: ${r.evidence.origin_tx_count} · Reverse flows: ${r.evidence.return_flows}</div><div class="muted">${r.note}</div>`;
  }catch(err){out.textContent='Analysis failed: '+err.message}
});
load();
