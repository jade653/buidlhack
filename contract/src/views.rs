use crate::*;

#[near(serializers = [json])]
pub struct ContractInfo {
    pub requires_tee: bool,
    pub attestation_expiration_time_ms: u64,
    pub owner_id: AccountId,
    pub mpc_contract_id: AccountId,
}

#[near(serializers = [json])]
pub enum AgentValidity {
    Valid,
    Invalid(Vec<AgentRemovalReason>),
}

#[near(serializers = [json])]
pub struct AgentView {
    pub account_id: AccountId,
    pub valid_until_ms: U64,
}

#[near]
impl Contract {
    pub fn get_contract_info(&self) -> ContractInfo {
        ContractInfo {
            requires_tee: self.requires_tee,
            attestation_expiration_time_ms: self.attestation_expiration_time_ms,
            owner_id: self.owner_id.clone(),
            mpc_contract_id: self.mpc_contract_id.clone(),
        }
    }

    /// Returns agent view if registered, None otherwise.
    /// ShadeClient calls this to decide whether to attach deposit on register_agent.
    pub fn get_agent(&self, account_id: AccountId) -> Option<AgentView> {
        self.agents.get(&account_id).map(|a| AgentView {
            account_id: account_id.clone(),
            valid_until_ms: U64::from(a.valid_until_ms),
        })
    }

    pub fn get_agent_valid_until(&self, account_id: AccountId) -> Option<u64> {
        self.agents.get(&account_id).map(|a| a.valid_until_ms)
    }

    pub fn get_approved_measurements(&self) -> Vec<String> {
        // Return as opaque strings to avoid JsonSchema requirement on FullMeasurementsHex
        self.approved_measurements
            .iter()
            .map(|m| serde_json::to_string(m).unwrap_or_default())
            .collect()
    }

    /// Called by ShadeClient.isWhitelisted()
    pub fn get_whitelisted_agents_for_local(&self) -> Vec<AccountId> {
        self.whitelisted_agents_for_local.iter().cloned().collect()
    }
}
