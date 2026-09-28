const ENGINE_NAMES={
  B1:"Transaction Simulation Engine",
  B2:"Transaction & Contract Security Engine",
  B3:"Real-Time Threat & Monitoring Engine",
  B4:"On-Chain Entity & Fund-Flow Intelligence Engine",
  B5:"Cross-Chain Route & Bridge Intelligence Engine",
  F1:"Portfolio & Exposure Engine",
  F2:"Protocol Risk Engine",
  F3:"Position & Liquidation Risk Engine",
  F4:"Yield & Strategy Risk Engine",
  F5:"Treasury Allocation & Scenario Engine",
};

const ENGINE_METADATA={
  B1:{engine_version:"1.3.0",analysis_framework_version:"b1-live-1.8.0"},
  B2:{engine_version:"1.1.0",analysis_framework_version:"b2-live-1.3.0"},
  B3:{engine_version:"1.1.0",analysis_framework_version:"b3-live-1.3.0"},
  B4:{engine_version:"1.0.0",analysis_framework_version:"b4-live-1.1.0"},
  B5:{engine_version:"1.2.0",analysis_framework_version:"b5-live-1.4.0"},
  F1:{engine_version:"1.2.0",analysis_framework_version:"f1-live-1.4.0"},
  F2:{engine_version:"1.2.0",analysis_framework_version:"f2-live-1.4.0"},
  F3:{engine_version:"1.3.0",analysis_framework_version:"f3-live-1.3.0"},
  F4:{engine_version:"1.2.0",analysis_framework_version:"f4-live-1.3.0"},
  F5:{engine_version:"1.2.0",analysis_framework_version:"f5-live-1.3.0"},
};

function record(value){return value&&typeof value==="object"&&!Array.isArray(value)?value:{}}
function flag(value){return value===true}
function number(value,fallback){return typeof value==="number"&&Number.isFinite(value)?value:fallback}
function clamp(value){return Math.min(100,Math.max(0,value))}

function score(engineId,input){
  if(engineId==="B1")return clamp((flag(input.will_revert)?45:10)+(flag(input.unlimited_approval)?35:0)+(flag(input.suspicious_value_flow)?20:0));
  if(engineId==="B2")return clamp((flag(input.known_malicious)?85:0)+(flag(input.unlimited_approval)?35:0)+(flag(input.unverified_contract)?20:0));
  if(engineId==="B3")return clamp((flag(input.active_exploit)?80:0)+(flag(input.oracle_anomaly)?40:0)+(flag(input.liquidity_deterioration)?30:0));
  if(engineId==="B4")return clamp((flag(input.label_conflict)?35:0)+(flag(input.suspicious_flow)?30:0)+(number(input.holder_concentration,0)>0.7?20:0));
  if(engineId==="B5")return clamp(number(input.route_risk,25)+(flag(input.bridge_incident)?20:0)+(flag(input.low_liquidity)?15:0));
  if(engineId==="F1")return clamp(Math.max(10,number(input.largest_exposure_pct,25))+(number(input.stablecoin_concentration,0)>0.7?25:0));
  if(engineId==="F2")return clamp((flag(input.exploit_history)?60:0)+(flag(input.admin_privilege)?25:0)+(flag(input.oracle_risk)?25:0)+(flag(input.low_liquidity)?20:0));
  if(engineId==="F3"){
    const healthFactor=number(input.health_factor,2);
    return healthFactor<1.05?90:healthFactor<1.2?75:healthFactor<1.5?45:20;
  }
  if(engineId==="F4")return clamp(20+(number(input.apy,0)>30?25:0)+(flag(input.incentive_dependent)?30:0)+(flag(input.lockup)?25:0));
  if(engineId==="F5")return clamp(Math.max(15,number(input.largest_allocation_pct,25))+(number(input.stablecoin_depeg_scenario_loss_pct,0)>20?30:0));
  return 0;
}

function severity(value){return value>=80?"critical":value>=60?"high":value>=35?"moderate":"low"}

export function analysisResult(engineId,demo,inputValue){
  const analysisId=crypto.randomUUID();
  const createdAt=new Date().toISOString();
  const metadata=ENGINE_METADATA[engineId]??{engine_version:"1.0.0",analysis_framework_version:"edge-runtime-1.0.0"};
  const input=record(inputValue);

  if(!demo){
    return {
      analysis_id:analysisId,engine_id:engineId,...metadata,
      status:"UNKNOWN",severity:"unknown",risk_score:null,data_confidence:0,engine_confidence:0,provider_consensus:"UNAVAILABLE",demo:false,
      summary:"No verified live provider evidence is configured for this free runtime; Rivexis returns UNKNOWN rather than fabricating a result.",
      metrics:{runtime:"supabase-edge",input_received:Object.keys(input).length>0},signals:[],warnings:[],hard_blockers:["NO_VERIFIED_PROVIDER_EVIDENCE"],mitigations:[],safer_alternatives:[],
      missing_data:["verified live provider evidence"],provider_status:[],provider_conflicts:[],evidence:[],data_freshness:{status:"UNKNOWN"},assumptions:[],created_at:createdAt,
    };
  }

  const riskScore=score(engineId,input);
  const warnings=[];
  const hardBlockers=[];
  const mitigations=[];
  const providerConflicts=[];
  if(flag(input.known_malicious)||flag(input.active_exploit))hardBlockers.push("Material security blocker detected in demonstration input");
  if(flag(input.unlimited_approval)){
    warnings.push("Unlimited approval increases token exposure");
    mitigations.push("Reduce approval to the minimum required amount");
  }
  if(flag(input.label_conflict)){
    warnings.push("Entity labels conflict; identity is not resolved");
    providerConflicts.push({metric:"entity_label",source_a:"Demo Source A",value_a:"Entity A",source_b:"Demo Source B",value_b:"Entity B",severity:"high",resolution_method:"unresolved",resolution_confidence:0});
  }
  const priceConflict=number(input.price_conflict_pct,0);
  if(priceConflict>3)providerConflicts.push({metric:"reference_price",source_a:"Demo Price A",value_a:100,source_b:"Demo Price B",value_b:100*(1+priceConflict/100),difference_percentage:priceConflict,severity:"high",resolution_method:"unresolved",resolution_confidence:0});
  const conflicts=providerConflicts.length>0;

  return {
    analysis_id:analysisId,engine_id:engineId,...metadata,
    status:conflicts?"CONFLICTING_DATA":"COMPLETED",severity:severity(riskScore),risk_score:riskScore,data_confidence:conflicts?65:82,engine_confidence:80,provider_consensus:conflicts?"CONFLICTING":"SINGLE SOURCE",demo:true,
    summary:`Demonstration result for ${ENGINE_NAMES[engineId]??engineId}: detected synthetic risk score ${riskScore}/100.`,
    metrics:{runtime:"supabase-edge-demo",input_echo:input},signals:[],warnings,hard_blockers:hardBlockers,mitigations,safer_alternatives:[...mitigations],missing_data:[],provider_status:[],provider_conflicts:providerConflicts,
    evidence:[{evidence_id:crypto.randomUUID(),provider:"Rivexis Demo Adapter",source_type:"demo",retrieved_at:createdAt,observed_at:createdAt,normalized_value:input,calculation_version:metadata.analysis_framework_version,engine_version:metadata.engine_version,confidence:75,freshness:"CURRENT",license_classification:"internal-demo"}],
    data_freshness:{status:"CURRENT",source:"demo"},assumptions:["Synthetic demonstration inputs supplied by the user/interface."],created_at:createdAt,
  };
}
