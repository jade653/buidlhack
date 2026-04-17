// owner.rs — Owner-gated admin functions.
// require_owner() is defined in internal/helpers.rs.

use crate::*;

#[near]
impl Contract {
    // ── Measurements ──────────────────────────────────────────────────────────

    /// Approve a Docker image code-hash. Must be called after every image rebuild.
    /// In local mode: approve create_mock_full_measurements_hex() as the default.
    pub fn approve_measurements(&mut self, measurements: FullMeasurementsHex) {
        self.require_owner();
        self.approved_measurements.insert(measurements);
    }

    pub fn remove_measurements(&mut self, measurements: FullMeasurementsHex) {
        self.require_owner();
        self.approved_measurements.remove(&measurements);
    }

    // ── PPIDs ─────────────────────────────────────────────────────────────────

    /// Approve a Phala platform identifier.
    /// In local mode: approve Ppid::default() (all-zeros).
    pub fn approve_ppid(&mut self, ppid: Ppid) {
        self.require_owner();
        self.approved_ppids.insert(ppid);
    }

    pub fn remove_ppid(&mut self, ppid: Ppid) {
        self.require_owner();
        self.approved_ppids.remove(&ppid);
    }

    // ── Local dev whitelist ───────────────────────────────────────────────────

    /// Whitelist an agent for local (non-TEE) testing.
    /// Disabled when requires_tee = true.
    pub fn whitelist_agent_for_local(&mut self, account_id: AccountId) {
        self.require_owner();
        require!(
            !self.requires_tee,
            "Cannot whitelist in local mode when TEE is required"
        );
        self.whitelisted_agents_for_local.insert(account_id);
    }

    pub fn remove_agent_from_whitelist_for_local(&mut self, account_id: AccountId) {
        self.require_owner();
        self.whitelisted_agents_for_local.remove(&account_id);
    }

    pub fn remove_agent(&mut self, account_id: AccountId) {
        self.require_owner();
        self.agents.remove(&account_id);
    }

    // ── Ownership ─────────────────────────────────────────────────────────────

    pub fn update_owner_id(&mut self, new_owner_id: AccountId) {
        self.require_owner();
        self.owner_id = new_owner_id;
    }
}
