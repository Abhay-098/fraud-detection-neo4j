const $ = id => document.getElementById(id);


/* ============================================================
   API HELPERS
============================================================ */

async function get(url) {

  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(await response.text());
  }

  return response.json();
}


async function post(url, body) {

  const response = await fetch(url, {

    method: "POST",

    headers: {
      "Content-Type": "application/json"
    },

    body: JSON.stringify(body)

  });

  if (!response.ok) {
    throw new Error(await response.text());
  }

  return response.json();
}


/* ============================================================
   GENERIC TABLE RENDERER
============================================================ */

function rows(el, headers, data, fields) {

  el.innerHTML =

    `<div class="row head">
      ${headers.map(x => `<div>${x}</div>`).join("")}
    </div>`

    +

    data.map(d =>

      `<div class="row">

        ${fields.map(f =>

          `<div>${
            Array.isArray(d[f])
              ? d[f].slice(0, 4).join(", ")
              : d[f] ?? "—"
          }</div>`

        ).join("")}

      </div>`

    ).join("");
}


/* ============================================================
   FRAUD RING RENDERER
============================================================ */

function renderRings(data) {

  if (!data.length) {

    $("ringsTable").innerHTML =
      `<div class="muted">
        No candidate rings found with the current criteria.
      </div>`;

    return;
  }


  $("ringsTable").innerHTML = data.map(r => `

    <div class="ring-card">

      <div class="ring-title">

        <span>
          ${r.ring_id}
        </span>

        <span>
          ${r.risk_level} · ${r.ring_score}/100
        </span>

      </div>


      <div>

        ${r.member_count} accounts ·
        ${r.internal_transfers} internal transfers ·
        amount ${Number(r.internal_amount || 0).toLocaleString()}

      </div>


      <div class="ring-members">

        ${(r.accounts || []).join(", ")}

      </div>

    </div>

  `).join("");
}


/* ============================================================
   LOAD DASHBOARD DATA
============================================================ */

async function load() {

  try {

    /* ---------------- API HEALTH ---------------- */

    const health = await get("/api/health");


    $("dot").style.background =
      health.neo4j ? "#6ee7b7" : "#fbbf24";


    $("health").textContent =
      health.neo4j
        ? "API + Neo4j connected"
        : "API online / Neo4j unavailable";


    /* ---------------- DATABASE SUMMARY ---------------- */

    const summary = await get("/api/summary");


    $("customers").textContent =
      (summary.customers ?? 0).toLocaleString();


    $("accounts").textContent =
      (summary.accounts ?? 0).toLocaleString();


    $("transactions").textContent =
      (summary.transactions ?? 0).toLocaleString();


    $("fraud").textContent =
      (summary.fraud_transactions ?? 0).toLocaleString();


    $("devices").textContent =
      (summary.devices ?? 0).toLocaleString();


    /* ---------------- HIGH-RISK ACCOUNTS ---------------- */

    const riskAccounts =
      await get("/api/fraud/high-risk-accounts?limit=8");


    rows(

      $("riskTable"),

      [
        "Account",
        "Txns",
        "Peers",
        "Risk"
      ],

      riskAccounts,

      [
        "account",
        "tx_count",
        "shared_device_peers",
        "risk_indicator"
      ]

    );


    /* ---------------- SHARED DEVICES ---------------- */

    const sharedDevices =
      await get("/api/fraud/shared-devices?limit=8");


    rows(

      $("devicesTable"),

      [
        "Device",
        "Accounts",
        "Members"
      ],

      sharedDevices,

      [
        "device",
        "account_count",
        "accounts"
      ]

    );


    /* ---------------- FRAUD RINGS ---------------- */

    const rings =
      await get("/api/fraud/rings?limit=8");


    renderRings(rings);


    /* ---------------- RECENT TRANSACTIONS ---------------- */

    const transactions =
      await get("/api/transactions?limit=12");


    rows(

      $("txTable"),

      [
        "Transaction",
        "Type",
        "Origin",
        "Destination",
        "Amount",
        "Fraud"
      ],

      transactions,

      [
        "transaction_id",
        "type",
        "origin",
        "destination",
        "amount",
        "is_fraud"
      ]

    );


  } catch (error) {

    $("health").textContent =
      "API/Neo4j unavailable";

    console.error(error);

  }
}


/* ============================================================
   STORED TRANSACTION
   ML + GRAPH ANALYSIS
============================================================ */

$("storedAnalysisForm").addEventListener(

  "submit",

  async event => {

    event.preventDefault();


    const output =
      $("storedAnalysisResult");


    const transactionId =
      $("storedTransactionId").value.trim();


    output.innerHTML =
      `<span class="muted">
        Running machine-learning and graph analysis...
      </span>`;


    try {

      const result = await get(

        `/api/fraud/analyze/${encodeURIComponent(transactionId)}`

      );


      const ml =
        result.ml_analysis;


      const graph =
        result.graph_analysis;


      const truth =
        result.ground_truth;


      const tx =
        result.transaction;


      const predictionClass =

        ml.label === "FRAUD"
          ? "fraud-result"
          : "legit-result";


      const truthLabel =

        truth.is_fraud
          ? "FRAUD"
          : "LEGITIMATE";


      output.innerHTML = `


        <!-- TRANSACTION INFORMATION -->

        <div class="analysis-section">

          <h3>
            Transaction
          </h3>


          <div>

            <strong>
              ${result.transaction_id}
            </strong>

            &nbsp; | &nbsp;

            ${tx.type}

            &nbsp; | &nbsp;

            Amount:
            ${Number(tx.amount || 0).toLocaleString()}

          </div>


          <div class="muted">

            Step:
            ${tx.step ?? "—"}

          </div>


          <div class="muted">

            ${tx.origin}
            &rarr;
            ${tx.destination}

          </div>

        </div>



        <!-- MACHINE LEARNING RESULT -->

        <div class="analysis-section ${predictionClass}">

          <h3>
            ML Fraud Detection
          </h3>


          <div class="scoreline">

            <span class="pill">

              ${ml.label}

            </span>


            <strong>

              ${ml.fraud_probability_percent}%
              fraud probability

            </strong>

          </div>


          <div class="muted">

            Model:
            ${ml.model}

            &nbsp; | &nbsp;

            Classification threshold:
            ${(ml.threshold * 100).toFixed(0)}%

          </div>

        </div>



        <!-- GRAPH ANALYSIS -->

        <div class="analysis-section">

          <h3>
            Neo4j Graph Risk Analysis
          </h3>


          <div class="scoreline">

            <span class="score">

              ${graph.risk_score}/100

            </span>


            <span class="pill">

              ${graph.risk_level} RISK

            </span>

          </div>


          <ul class="indicators">

            ${graph.indicators

              .map(

                indicator =>

                  `<li>
                    ${indicator.replaceAll("_", " ")}
                  </li>`

              )

              .join("")}

          </ul>


          <div class="muted">

            Origin transactions:
            ${graph.evidence.origin_tx_count}

            &nbsp; | &nbsp;

            Reverse flows:
            ${graph.evidence.return_flows}

            &nbsp; | &nbsp;

            Shared-device peers:
            ${graph.evidence.shared_device_peers}

          </div>


          <div class="muted">

            ${graph.note}

          </div>

        </div>



        <!-- GROUND TRUTH -->

        <div class="analysis-section">

          <h3>
            Ground Truth
          </h3>


          <strong>

            Known PaySim label:
            ${truthLabel}

          </strong>


          <div class="muted">

            Used in prediction:
            ${truth.used_in_prediction ? "Yes" : "No"}

          </div>

        </div>



        <!-- EXPLANATION -->

        <div class="notice">

          The machine-learning model performs transaction-level
          fraud classification while Neo4j provides
          relationship-aware risk evidence.

          The known PaySim fraud label is displayed only for
          evaluation and is not used to generate the prediction.

        </div>

      `;


    } catch (error) {

      output.innerHTML = `

        <div class="notice">

          Analysis failed:
          ${error.message}

        </div>

      `;

    }

  }

);


/* ============================================================
   NEW TRANSACTION GRAPH-RISK ANALYSIS
============================================================ */

$("analysisForm").addEventListener(

  "submit",

  async event => {

    event.preventDefault();


    const output =
      $("analysisResult");


    output.innerHTML =

      `<span class="muted">
        Analyzing graph context...
      </span>`;


    try {

      const result = await post(

        "/api/fraud/analyze",

        {

          origin:
            $("anOrigin").value.trim(),

          destination:
            $("anDestination").value.trim(),

          amount:
            Number($("anAmount").value),

          type:
            $("anType").value

        }

      );


      output.innerHTML = `

        <div class="scoreline">

          <span class="score">

            ${result.risk_score}/100

          </span>


          <span class="pill">

            ${result.risk_level} RISK

          </span>


          <strong>

            ${
              result.flagged
                ? "FLAG FOR INVESTIGATION"
                : "No high-risk flag"
            }

          </strong>

        </div>


        <ul class="indicators">

          ${result.indicators

            .map(

              indicator =>

                `<li>
                  ${indicator.replaceAll("_", " ")}
                </li>`

            )

            .join("")}

        </ul>


        <div class="muted">

          Shared-device peers:
          ${result.evidence.shared_device_peers}

          &nbsp; | &nbsp;

          Origin transactions:
          ${result.evidence.origin_tx_count}

          &nbsp; | &nbsp;

          Reverse flows:
          ${result.evidence.return_flows}

        </div>


        <div class="muted">

          ${result.note}

        </div>

      `;


    } catch (error) {

      output.textContent =
        "Analysis failed: " + error.message;

    }

  }

);


/* ============================================================
   START DASHBOARD
============================================================ */

load();