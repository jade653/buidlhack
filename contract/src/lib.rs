// ─────────────────────────────────────────────────────────────────────────────
// Base Shade Agent contract (derived from shade-contract-template).
// If building inside the shade-agent-framework monorepo, replace this file
// with the template's lib.rs and only apply the "PLATFORM ADDITIONS" block.
// ─────────────────────────────────────────────────────────────────────────────

use near_sdk::borsh::{BorshDeserialize, BorshSerialize};
use near_sdk::collections::{IterableMap, IterableSet};
use near_sdk::store::UnorderedMap;
use near_sdk::{
    env, near, require, AccountId, BorshStorageKey, NearToken, PanicOnDefault, Promise,
};
use shade_attestation::{DstackAttestation, DstackAttestationForContract, FullMeasurementsHex, Ppid};

pub mod owner;
pub mod platform;
pub mod views;

pub use platform::{Challenge, LockedOutput, ScoreRecord};

// ── Storage keys ──────────────────────────────────────────────────────────────

#[derive(BorshSerialize, BorshDeserialize, BorshStorageKey)]
#[borsh(crate = "near_sdk::borsh")]
pub enum StorageKey {
    // Base Shade Agent keys
    ApprovedMeasurements,
    ApprovedPpids,
    Agents,
    WhitelistedAgentsForLocal,
    // ── PLATFORM ADDITIONS ────────────────────────────────────────────────────
    Challenges,
    /// composite key per score: "{challenge_id}::{user_id}"
    Scores,
    /// composite key per output: "{challenge_id}::{user_id}"
    LockedOutputs,
}

// ── Agent record ──────────────────────────────────────────────────────────────

#[near(serializers = [borsh, json])]
pub struct Agent {
    pub measurements: FullMeasurementsHex,
    pub ppid: Ppid,
    pub valid_until_ms: u64,
}

// ── Main contract state ───────────────────────────────────────────────────────

#[near(contract_state)]
#[derive(PanicOnDefault)]
pub struct Contract {
    // ── Base Shade Agent fields ────────────────────────────────────────────────
    pub requires_tee: bool,
    pub attestation_expiration_time_ms: u64,
    pub owner_id: AccountId,
    pub mpc_contract_id: AccountId,
    pub approved_measurements: IterableSet<FullMeasurementsHex>,
    pub approved_ppids: IterableSet<Ppid>,
    pub agents: IterableMap<AccountId, Agent>,
    pub whitelisted_agents_for_local: IterableSet<AccountId>,

    // ── PLATFORM ADDITIONS ────────────────────────────────────────────────────
    pub challenges: UnorderedMap<String, Challenge>,
    pub scores: UnorderedMap<String, ScoreRecord>,
    pub locked_outputs: UnorderedMap<String, LockedOutput>,
}

// ── Constructor ───────────────────────────────────────────────────────────────

#[near]
impl Contract {
    /// Deploy with:
    ///   near contract deploy ... call-function as-transaction new \
    ///     json-args '{"owner_id":"you.testnet","mpc_contract_id":"mpc.testnet","requires_tee":false}' ...
    #[init]
    pub fn new(
        owner_id: AccountId,
        mpc_contract_id: AccountId,
        requires_tee: bool,
        attestation_expiration_time_ms: Option<u64>,
    ) -> Self {
        // Default: attestation is valid for 24 hours
        let expiry_ms = attestation_expiration_time_ms.unwrap_or(24 * 60 * 60 * 1_000);
        Self {
            requires_tee,
            attestation_expiration_time_ms: expiry_ms,
            owner_id,
            mpc_contract_id,
            approved_measurements: IterableSet::new(StorageKey::ApprovedMeasurements),
            approved_ppids: IterableSet::new(StorageKey::ApprovedPpids),
            agents: IterableMap::new(StorageKey::Agents),
            whitelisted_agents_for_local: IterableSet::new(
                StorageKey::WhitelistedAgentsForLocal,
            ),
            challenges: UnorderedMap::new(StorageKey::Challenges),
            scores: UnorderedMap::new(StorageKey::Scores),
            locked_outputs: UnorderedMap::new(StorageKey::LockedOutputs),
        }
    }

    // ── Agent registration (Shade Agent base) ─────────────────────────────────

    /// Called by the TEE agent on boot via ShadeClient.register().
    /// In TEE mode: verifies Dstack attestation against approved measurements.
    /// In local mode: checks the whitelist (for dev/testing only).
    #[payable]
    pub fn register_agent(&mut self, attestation: DstackAttestationForContract) -> bool {
        let agent_id = env::predecessor_account_id();

        if self.requires_tee {
            // Verify against approved measurements and PPIDs
            let verified = attestation
                .verify(
                    agent_id.as_str(),
                    &self.approved_measurements,
                    &self.approved_ppids,
                )
                .expect("TEE attestation verification failed");

            // Require sufficient deposit to cover storage for the Agent record
            let storage_cost = env::storage_byte_cost()
                .as_yoctonear()
                .saturating_mul(512);
            let existing = self.agents.contains_key(&agent_id);
            if !existing {
                require!(
                    env::attached_deposit().as_yoctonear() >= storage_cost,
                    "Attached deposit must cover storage cost"
                );
            }

            let valid_until_ms =
                env::block_timestamp_ms() + self.attestation_expiration_time_ms;

            self.agents.insert(
                agent_id.clone(),
                Agent {
                    measurements: verified.measurements,
                    ppid: verified.ppid,
                    valid_until_ms,
                },
            );

            near_sdk::log!(
                "EVENT:agent_registered:{}:valid_until:{}",
                agent_id,
                valid_until_ms
            );
        } else {
            require!(
                !self.requires_tee,
                "TEE mode is enabled; local whitelist registration is disabled"
            );
            require!(
                self.whitelisted_agents_for_local.contains(&agent_id),
                "Agent not whitelisted for local mode"
            );
        }

        true
    }

    // ── Internal helper: gate functions to verified TEE agents ────────────────

    /// Returns Some(panic_promise) if the caller is NOT a valid registered agent.
    /// Pattern from shade-contract-template — used by TEE-gated functions.
    pub(crate) fn require_valid_agent(&self) -> Option<()> {
        let caller = env::predecessor_account_id();

        if self.requires_tee {
            match self.agents.get(&caller) {
                None => {
                    env::panic_str("Caller is not a registered TEE agent");
                }
                Some(agent) => {
                    if agent.valid_until_ms < env::block_timestamp_ms() {
                        env::panic_str("Agent attestation has expired; re-register");
                    }
                }
            }
        } else {
            if !self.whitelisted_agents_for_local.contains(&caller) {
                env::panic_str("Caller is not whitelisted for local mode");
            }
        }

        None
    }

    /// Convenience: checks whether a given account is a valid registered agent.
    pub fn is_valid_agent(&self, account_id: AccountId) -> bool {
        if self.requires_tee {
            match self.agents.get(&account_id) {
                None => false,
                Some(agent) => agent.valid_until_ms >= env::block_timestamp_ms(),
            }
        } else {
            self.whitelisted_agents_for_local.contains(&account_id)
        }
    }
}
