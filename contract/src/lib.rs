use hex;
use near_sdk::{
    AccountId, BorshStorageKey, Gas, NearToken, PanicOnDefault, Promise,
    env::{self, block_timestamp_ms},
    json_types::U64,
    log, near, require,
    serde::Serialize,
    serde_json,
    store::{IterableMap, IterableSet},
};
use shade_attestation::{
    attestation::DstackAttestation,
    measurements::{FullMeasurements, FullMeasurementsHex, create_mock_full_measurements_hex},
    report_data::ReportData,
    tcb_info::HexBytes,
};

pub use internal::events::Event;
pub use internal::helpers::AgentRemovalReason;
pub use views::ContractInfo;

pub mod internal;
pub mod owner;
pub mod platform;
pub mod views;

pub use platform::{Challenge, LockedOutput, ScoreRecord};

/// Phala's platform identifier — 16-byte hex value.
pub type Ppid = HexBytes<16>;

// ── Storage keys ──────────────────────────────────────────────────────────────

#[derive(BorshStorageKey)]
#[near]
pub enum StorageKey {
    // Base Shade Agent keys
    ApprovedMeasurements,
    ApprovedPpids,
    Agents,
    WhitelistedAgentsForLocal,
    // Platform additions
    Challenges,
    Scores,
    LockedOutputs,
}

// ── Agent record ──────────────────────────────────────────────────────────────

#[near(serializers = [borsh])]
#[derive(Clone)]
pub struct Agent {
    pub measurements: FullMeasurementsHex,
    pub ppid: Ppid,
    pub valid_until_ms: u64,
}

// ── Main contract state ───────────────────────────────────────────────────────

#[near(contract_state)]
#[derive(PanicOnDefault)]
pub struct Contract {
    // Base Shade Agent fields
    pub requires_tee: bool,
    pub attestation_expiration_time_ms: u64,
    pub owner_id: AccountId,
    pub mpc_contract_id: AccountId,
    pub approved_measurements: IterableSet<FullMeasurementsHex>,
    pub approved_ppids: IterableSet<Ppid>,
    pub agents: IterableMap<AccountId, Agent>,
    pub whitelisted_agents_for_local: IterableSet<AccountId>,

    // Platform additions
    pub challenges: IterableMap<String, Challenge>,
    pub scores: IterableMap<String, ScoreRecord>,
    pub locked_outputs: IterableMap<String, LockedOutput>,
}

// ── Constructor ───────────────────────────────────────────────────────────────

const STORAGE_BYTES_TO_REGISTER: u128 = 486;

#[near]
impl Contract {
    /// Initialize the contract.
    ///
    /// Example (testnet, local dev mode):
    ///   near contract deploy CONTRACT.testnet use-file res/contract.wasm \
    ///     with-init-call new json-args \
    ///     '{"requires_tee":false,"attestation_expiration_time_ms":"86400000",
    ///       "owner_id":"YOU.testnet","mpc_contract_id":"v1.signer-prod.testnet"}' \
    ///     prepaid-gas '100 Tgas' attached-deposit '0 NEAR'
    #[init]
    pub fn new(
        requires_tee: bool,
        attestation_expiration_time_ms: U64,
        owner_id: AccountId,
        mpc_contract_id: AccountId,
    ) -> Self {
        Self {
            requires_tee,
            attestation_expiration_time_ms: attestation_expiration_time_ms.into(),
            owner_id,
            mpc_contract_id,
            approved_measurements: IterableSet::new(StorageKey::ApprovedMeasurements),
            approved_ppids: IterableSet::new(StorageKey::ApprovedPpids),
            agents: IterableMap::new(StorageKey::Agents),
            whitelisted_agents_for_local: IterableSet::new(
                StorageKey::WhitelistedAgentsForLocal,
            ),
            challenges: IterableMap::new(StorageKey::Challenges),
            scores: IterableMap::new(StorageKey::Scores),
            locked_outputs: IterableMap::new(StorageKey::LockedOutputs),
        }
    }

    // ── Agent registration ────────────────────────────────────────────────────

    /// Called by the TEE agent on boot via ShadeClient.register().
    #[payable]
    pub fn register_agent(&mut self, attestation: DstackAttestation) -> bool {
        let predecessor = env::predecessor_account_id();
        let already_registered = self.agents.get(&predecessor).is_some();

        if !already_registered {
            let storage_cost = env::storage_byte_cost()
                .checked_mul(STORAGE_BYTES_TO_REGISTER)
                .unwrap();
            require!(
                env::attached_deposit() >= storage_cost,
                &format!(
                    "Attached deposit must be >= storage cost {:?}",
                    storage_cost.exact_amount_display()
                )
            );
        }

        let (measurements, ppid) = self.verify_attestation(attestation);
        let valid_until_ms = block_timestamp_ms() + self.attestation_expiration_time_ms;

        Event::AgentRegistered {
            account_id: &predecessor,
            measurements: &measurements,
            ppid: &ppid,
            current_time_ms: U64::from(block_timestamp_ms()),
            valid_until_ms: U64::from(valid_until_ms),
        }
        .emit();

        self.agents.insert(
            predecessor,
            Agent {
                measurements,
                ppid,
                valid_until_ms,
            },
        );

        true
    }

    /// Called by require_valid_agent cross-contract call when an agent is invalid.
    #[private]
    pub fn fail_on_invalid_agent(reasons: Vec<AgentRemovalReason>) {
        env::panic_str(&format!("Invalid agent: {:?}", reasons));
    }

    /// View: check if a given account is a currently-valid registered agent.
    pub fn is_valid_agent(&self, account_id: AccountId) -> bool {
        match self.agents.get(&account_id) {
            None => false,
            Some(agent) => {
                agent.valid_until_ms >= block_timestamp_ms()
                    && self.approved_measurements.contains(&agent.measurements)
                    && self.approved_ppids.contains(&agent.ppid)
            }
        }
    }
}
