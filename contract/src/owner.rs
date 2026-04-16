// owner.rs — Owner-gated admin functions (approve_measurements, etc.)
//
// This module mirrors shade-contract-template/src/owner.rs.
// If building inside the shade-agent-framework monorepo, copy that file here
// verbatim and it will work without changes.
//
// Minimal version for standalone builds:

use crate::*;
use near_sdk::{env, near, require};

#[near]
impl Contract {
    // ── Guard ─────────────────────────────────────────────────────────────────

    pub(crate) fn require_owner(&self) {
        require!(
            env::predecessor_account_id() == self.owner_id,
            "Only the contract owner can call this function"
        );
    }

    // ── Measurements ─────────────────────────────────────────────────────────

    /// Approve a Docker image code-hash so its TEE agents can register.
    /// Must be called after every Docker image rebuild.
    pub fn approve_measurements(&mut self, measurements: FullMeasurementsHex) {
        self.require_owner();
        self.approved_measurements.insert(measurements);
    }

    pub fn remove_measurements(&mut self, measurements: FullMeasurementsHex) {
        self.require_owner();
        self.approved_measurements.remove(&measurements);
    }

    // ── PPIDs ─────────────────────────────────────────────────────────────────

    pub fn approve_ppid(&mut self, ppid: Ppid) {
        self.require_owner();
        self.approved_ppids.insert(ppid);
    }

    pub fn remove_ppid(&mut self, ppid: Ppid) {
        self.require_owner();
        self.approved_ppids.remove(&ppid);
    }

    // ── Local dev whitelist ───────────────────────────────────────────────────

    /// Whitelist an agent account for local (non-TEE) testing.
    /// Panics if requires_tee is true — don't use in production.
    pub fn whitelist_agent_for_local(&mut self, account_id: AccountId) {
        self.require_owner();
        require!(
            !self.requires_tee,
            "Cannot whitelist for local mode when TEE is required"
        );
        self.whitelisted_agents_for_local.insert(account_id);
    }

    pub fn remove_agent_from_whitelist_for_local(&mut self, account_id: AccountId) {
        self.require_owner();
        self.whitelisted_agents_for_local.remove(&account_id);
    }

    // ── Ownership transfer ────────────────────────────────────────────────────

    pub fn update_owner_id(&mut self, new_owner_id: AccountId) {
        self.require_owner();
        self.owner_id = new_owner_id;
    }
}
