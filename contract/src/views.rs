use crate::*;

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

    // Agent struct is borsh-only, so we expose individual fields rather than the struct.
    // (borsh types can't be returned as JSON directly without json serializer derive)
    pub fn get_agent_valid_until(&self, account_id: AccountId) -> Option<u64> {
        self.agents.get(&account_id).map(|a| a.valid_until_ms)
    }

    pub fn get_approved_measurements(&self) -> Vec<FullMeasurementsHex> {
        self.approved_measurements.iter().cloned().collect()
    }

    pub fn get_whitelisted_agents(&self) -> Vec<AccountId> {
        self.whitelisted_agents_for_local.iter().cloned().collect()
    }
}
