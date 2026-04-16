// views.rs — Read-only queries for the base Shade Agent state.

use crate::*;
use near_sdk::near;

#[near(serializers = [json])]
pub struct ContractInfo {
    pub requires_tee: bool,
    pub attestation_expiration_time_ms: u64,
    pub owner_id: AccountId,
}

#[near]
impl Contract {
    pub fn get_contract_info(&self) -> ContractInfo {
        ContractInfo {
            requires_tee: self.requires_tee,
            attestation_expiration_time_ms: self.attestation_expiration_time_ms,
            owner_id: self.owner_id.clone(),
        }
    }

    pub fn get_agent(&self, account_id: AccountId) -> Option<Agent> {
        self.agents.get(&account_id)
    }

    pub fn get_approved_measurements(&self) -> Vec<FullMeasurementsHex> {
        self.approved_measurements.iter().cloned().collect()
    }
}
