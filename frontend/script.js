const $=id=>document.getElementById(id);
async function get(url){const r=await fetch(url);if(!r.ok)throw new Error(await r.text());return r.json()}
function rows(el, headers, data, fields){
  el.innerHTML=`<div class="row head">${headers.map(x=>`<div>${x}</div>`).join("")}</div>`+
    data.map(d=>`<div class="row">${fields.map(f=>`<div>${d[f]??"—"}</div>`).join("")}</div>`).join("");
}
async function load(){
  try{
    const h=await get("/api/health");$("dot").style.background=h.neo4j?"#6ee7b7":"#fbbf24";$("health").textContent=h.neo4j?"API + Neo4j connected":"API online / Neo4j unavailable";
    const s=await get("/api/summary");$("customers").textContent=(s.customers??0).toLocaleString();$("accounts").textContent=(s.accounts??0).toLocaleString();$("transactions").textContent=(s.transactions??0).toLocaleString();$("fraud").textContent=(s.fraud_transactions??0).toLocaleString();$("devices").textContent=(s.devices??0).toLocaleString();
    rows($("riskTable"),["Account","Txns","Fraud","Risk"],await get("/api/fraud/high-risk-accounts?limit=8"),["account","tx_count","known_fraud","risk_indicator"]);
    rows($("devicesTable"),["Device","Accounts","Members"],await get("/api/fraud/shared-devices?limit=8"),["device","account_count","accounts"]);
    rows($("ringsTable"),["Account A","Account B","Transfers"],await get("/api/fraud/rings?limit=8"),["account_a","account_b","transfers"]);
    rows($("txTable"),["Transaction","Type","Origin","Destination","Amount","Fraud"],await get("/api/transactions?limit=12"),["transaction_id","type","origin","destination","amount","is_fraud"]);
  }catch(e){$("health").textContent="Start Neo4j and API";console.error(e)}
}
load();
