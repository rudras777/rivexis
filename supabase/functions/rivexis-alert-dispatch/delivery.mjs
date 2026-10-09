const UUID_RE=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export function validEmail(value){
  if(typeof value!=="string"||!value||value.length>320||value.split("@").length!==2||/\s/.test(value))return false;
  const [local,domain]=value.split("@");
  return Boolean(local&&domain&&domain.includes("."));
}

export function escapeHtml(value){
  return String(value??"")
    .replaceAll("&","&amp;")
    .replaceAll("<","&lt;")
    .replaceAll(">","&gt;")
    .replaceAll('"',"&quot;")
    .replaceAll("'","&#39;");
}

export async function idempotencyUuid(value){
  const raw=String(value??"");
  if(UUID_RE.test(raw))return raw.toLowerCase();
  const digest=new Uint8Array(await crypto.subtle.digest("SHA-256",new TextEncoder().encode(raw)));
  const bytes=digest.slice(0,16);
  bytes[6]=(bytes[6]&0x0f)|0x50;
  bytes[8]=(bytes[8]&0x3f)|0x80;
  const hex=[...bytes].map(byte=>byte.toString(16).padStart(2,"0")).join("");
  return `${hex.slice(0,8)}-${hex.slice(8,12)}-${hex.slice(12,16)}-${hex.slice(16,20)}-${hex.slice(20)}`;
}

function numberValue(value){
  return typeof value==="number"&&Number.isFinite(value)?value:null;
}

function evidenceMode(payload){
  return typeof payload?.evidence_mode==="string"&&payload.evidence_mode?payload.evidence_mode:"PERSISTED_ALERT_RECORD";
}

export function alertEmail(alert){
  const severity=String(alert?.severity??"unknown").toUpperCase();
  const status=String(alert?.status??"open").toUpperCase();
  const workspace=String(alert?.workspace_name??"Workspace");
  const reference=String(alert?.id??"unknown");
  const occurrence=Math.max(1,Number(alert?.occurrence_count??1)||1);
  const risk=numberValue(alert?.payload?.risk_score);
  const mode=evidenceMode(alert?.payload);
  const synthetic=mode==="SYNTHETIC_DEMO"||alert?.payload?.analysis_demo===true;
  const subject=`[Rivexis] ${severity} alert — ${workspace}`.slice(0,180);
  const truth=synthetic
    ?"This is synthetic demonstration evidence. It is not a live threat claim."
    :"This notification reflects a persisted Rivexis alert record. It does not imply continuous provider surveillance.";
  const text=[
    "Rivexis alert notification",
    `Workspace: ${workspace}`,
    `Severity: ${severity}`,
    `State: ${status}`,
    `Occurrences: ${occurrence}`,
    risk===null?"":`Risk score: ${risk}/100`,
    `Evidence mode: ${mode}`,
    `Reference: ${reference}`,
    "",
    truth,
    "Review the canonical record in your Rivexis workspace before acting."
  ].filter(Boolean).join("\n");
  const html=`<!doctype html><html><body style="font-family:Arial,sans-serif;background:#F3F2EC;color:#202B2D;padding:28px">
    <div style="max-width:640px;margin:auto;background:#F3F2EC;padding:28px;border-top:3px solid #326C6A">
      <img src="https://rivexis-web.rudrasingh0718.workers.dev/brand/rivexis-wordmark-light.png" alt="RIVEXIS" width="220" style="display:block;width:220px;max-width:100%;height:auto;margin-bottom:28px"/>
      <div style="font-size:12px;letter-spacing:.14em;color:#596A69">RIVEXIS · EVIDENCE ALERT</div>
      <h1 style="font-size:24px;margin:14px 0">${escapeHtml(severity)} alert</h1>
      <p style="color:#596A69">${escapeHtml(workspace)}</p>
      <table style="width:100%;border-collapse:collapse">
        <tr><td style="padding:8px 0;color:#596A69">State</td><td style="padding:8px 0;text-align:right;font-weight:700">${escapeHtml(status)}</td></tr>
        <tr><td style="padding:8px 0;color:#596A69">Occurrences</td><td style="padding:8px 0;text-align:right;font-weight:700">${occurrence}</td></tr>
        ${risk===null?"":`<tr><td style="padding:8px 0;color:#596A69">Risk score</td><td style="padding:8px 0;text-align:right;font-weight:700">${risk}/100</td></tr>`}
        <tr><td style="padding:8px 0;color:#596A69">Evidence mode</td><td style="padding:8px 0;text-align:right;font-weight:700">${escapeHtml(mode)}</td></tr>
      </table>
      <p style="margin-top:22px;padding-top:18px;border-top:1px solid #D9DFD7">${escapeHtml(truth)}</p>
      <p style="font-size:12px;color:#596A69">Reference: ${escapeHtml(reference)}</p>
      <p><a href="https://rivexis-web.rudrasingh0718.workers.dev/workspace/alerts" style="color:#326C6A">Review canonical alert record</a></p>
    </div>
  </body></html>`;
  return {subject,text,html,synthetic};
}

export function classifyBrevo(status,providerCode=""){
  if(status>=200&&status<300)return {ok:true,duplicate:false,error_code:null};
  const code=String(providerCode??"").toLowerCase();
  if(status===400&&(code==="duplicate_parameter"||code==="duplicateparameter")){
    return {ok:true,duplicate:true,error_code:null};
  }
  return {ok:false,duplicate:false,error_code:`brevo_http_${Math.trunc(status)}`};
}
