// platform.rs — Custom platform functions for the Agent Challenge contract.
//
// These are the three custom additions on top of the Shade Agent base:
//   submit_score   — TEE-gated, records a score on-chain
//   lock_output    — TEE-gated, locks encrypted agent output hash on-chain
//   release_bounty — enterprise-gated, pays winner and unlocks their output
//
// Plus supporting data structures and view functions.

use crate::*;
use near_sdk::{env, near, AccountId, NearToken, Promise};

// ─────────────────────────────────────────────────────────────────────────────
// Data structures
// ─────────────────────────────────────────────────────────────────────────────

#[near(serializers = [borsh, json])]
#[derive(Clone)]
pub struct Challenge {
    /// The NEAR account that created (and funded) this challenge.
    pub enterprise_id: AccountId,
    /// Locked bounty in yoctoNEAR. Transferred to winner on release_bounty.
    pub bounty_yocto: u128,
    /// Unix timestamp (ms) after which no new scores are accepted.
    pub deadline_ms: u64,
    pub is_finished: bool,
    pub winner: Option<AccountId>,
}

/// One score entry per (challenge, user) pair.
/// score is stored as basis-points (× 10_000) to avoid f64 in Borsh storage.
/// 0.87 → 8700 bp.  Range: 0–10_000.
#[near(serializers = [borsh, json])]
#[derive(Clone)]
pub struct ScoreRecord {
    pub score_bp: u32,
    pub submitted_at_ms: u64,
}

impl ScoreRecord {
    pub fn as_f64(&self) -> f64 {
        self.score_bp as f64 / 10_000.0
    }
}

/// Encrypted agent output locked on-chain.
/// `encrypted_hash` is the SHA-256 hex of the ciphertext stored off-chain (DB).
/// Storing the hash on-chain proves the ciphertext existed at submission time
/// and hasn't been tampered with. The actual ciphertext stays in the platform DB.
#[near(serializers = [borsh, json])]
#[derive(Clone)]
pub struct LockedOutput {
    pub encrypted_hash: String,
    /// Becomes true after release_bounty is called for this user.
    pub unlocked: bool,
}

// ─────────────────────────────────────────────────────────────────────────────
// Platform functions
// ─────────────────────────────────────────────────────────────────────────────

#[near]
impl Contract {
    // ── Enterprise: create challenge ──────────────────────────────────────────

    /// Enterprise calls this to post a challenge and lock the bounty.
    /// Attach NEAR tokens equal to the bounty.
    ///
    /// Example:
    ///   near contract call-function as-transaction \
    ///     YOUR_CONTRACT create_challenge \
    ///     json-args '{"challenge_id":"hack-001","deadline_ms":1999999999000}' \
    ///     prepaid-gas '30 Tgas' attached-deposit '10 NEAR' ...
    #[payable]
    pub fn create_challenge(&mut self, challenge_id: String, deadline_ms: u64) {
        require!(
            !self.challenges.contains_key(&challenge_id),
            "Challenge ID already exists"
        );
        let bounty = env::attached_deposit().as_yoctonear();
        require!(bounty > 0, "Must attach a non-zero bounty");
        require!(
            deadline_ms > env::block_timestamp_ms(),
            "Deadline must be in the future"
        );

        self.challenges.insert(
            challenge_id.clone(),
            Challenge {
                enterprise_id: env::predecessor_account_id(),
                bounty_yocto: bounty,
                deadline_ms,
                is_finished: false,
                winner: None,
            },
        );

        near_sdk::log!("EVENT:challenge_created:{}", challenge_id);
    }

    // ── TEE agent: submit score ───────────────────────────────────────────────

    /// Records a user's score on-chain. Only registered TEE agents can call this.
    /// Called by the Shade Agent TypeScript side after harness.py execution.
    ///
    /// `score` is a float in [0, 1] (JSON-serialized; f64 is fine for function args).
    /// We convert to u32 basis-points for Borsh storage.
    ///
    /// Re-submission is allowed — we keep the best score.
    pub fn submit_score(
        &mut self,
        challenge_id: String,
        user: AccountId,
        score: f64,
    ) {
        self.require_valid_agent();

        let challenge = self
            .challenges
            .get(&challenge_id)
            .unwrap_or_else(|| env::panic_str("Challenge not found"));

        require!(!challenge.is_finished, "Challenge is already finished");
        require!(
            env::block_timestamp_ms() <= challenge.deadline_ms,
            "Challenge deadline has passed"
        );
        require!(
            (0.0..=1.0).contains(&score),
            "Score must be in range [0, 1]"
        );

        let score_bp = (score * 10_000.0).round() as u32;
        let score_key = score_key(&challenge_id, &user);

        // Keep the best score if this user already has one
        if let Some(existing) = self.scores.get(&score_key) {
            if existing.score_bp >= score_bp {
                return; // existing is better or equal — no update
            }
        }

        self.scores.insert(
            score_key,
            ScoreRecord {
                score_bp,
                submitted_at_ms: env::block_timestamp_ms(),
            },
        );

        near_sdk::log!(
            "EVENT:score_submitted:{}:{}:{}",
            challenge_id,
            user,
            score_bp
        );
    }

    // ── TEE agent: lock output ────────────────────────────────────────────────

    /// Locks the SHA-256 hash of the encrypted output on-chain.
    /// Called alongside submit_score after harness.py execution.
    ///
    /// Only one output per (challenge, user) pair is accepted.
    /// The full ciphertext stays in the platform DB; the hash here proves
    /// it existed at this block and hasn't changed.
    pub fn lock_output(
        &mut self,
        challenge_id: String,
        user: AccountId,
        encrypted_hash: String,
    ) {
        self.require_valid_agent();

        require!(
            self.challenges.contains_key(&challenge_id),
            "Challenge not found"
        );
        require!(!encrypted_hash.is_empty(), "encrypted_hash cannot be empty");

        let output_key = score_key(&challenge_id, &user);
        require!(
            !self.locked_outputs.contains_key(&output_key),
            "Output already locked for this (challenge, user) pair"
        );

        self.locked_outputs.insert(
            output_key,
            LockedOutput {
                encrypted_hash: encrypted_hash.clone(),
                unlocked: false,
            },
        );

        near_sdk::log!(
            "EVENT:output_locked:{}:{}:{}",
            challenge_id,
            user,
            encrypted_hash
        );
    }

    // ── Enterprise: release bounty ────────────────────────────────────────────

    /// Enterprise calls this after choosing a winner.
    /// Transfers the bounty to the winner and marks their output as unlocked
    /// so the platform can deliver the ciphertext + decryption key.
    ///
    /// Only the enterprise that created the challenge can call this.
    pub fn release_bounty(
        &mut self,
        challenge_id: String,
        winner: AccountId,
    ) -> Promise {
        // Read the values we need before taking any mutable borrows.
        // (Rust borrow checker: can't hold &mut self.challenges while also
        // accessing self.locked_outputs or self.scores.)
        let (enterprise_id, bounty_yocto, is_finished) = {
            let c = self
                .challenges
                .get(&challenge_id)
                .unwrap_or_else(|| env::panic_str("Challenge not found"));
            (c.enterprise_id.clone(), c.bounty_yocto, c.is_finished)
        };

        require!(
            env::predecessor_account_id() == enterprise_id,
            "Only the enterprise that created this challenge can release the bounty"
        );
        require!(!is_finished, "Bounty already released");
        require!(bounty_yocto > 0, "No bounty to release");

        // Verify the winner has a score on-chain (they actually submitted)
        let key = score_key(&challenge_id, &winner);
        require!(
            self.scores.contains_key(&key),
            "Winner has no score on-chain for this challenge"
        );

        // Unlock the winner's output so the platform can deliver ciphertext + key.
        // get_mut() gives us a direct mutable reference — no need to re-insert.
        if let Some(output) = self.locked_outputs.get_mut(&key) {
            output.unlocked = true;
        }

        // Mark challenge finished
        {
            let c = self.challenges.get_mut(&challenge_id).unwrap();
            c.is_finished = true;
            c.winner = Some(winner.clone());
        }

        near_sdk::log!("EVENT:bounty_released:{}:{}", challenge_id, winner);

        Promise::new(winner).transfer(NearToken::from_yoctonear(bounty_yocto))
    }

    // ─────────────────────────────────────────────────────────────────────────
    // View functions
    // ─────────────────────────────────────────────────────────────────────────

    pub fn get_challenge(&self, challenge_id: String) -> Option<Challenge> {
        self.challenges.get(&challenge_id).cloned()
    }

    /// Returns the top `limit` scores for a challenge, sorted best-first.
    /// Each entry is (account_id, score_bp).  score_bp / 10_000 = float score.
    pub fn get_leaderboard(
        &self,
        challenge_id: String,
        limit: Option<u32>,
    ) -> Vec<(AccountId, u32)> {
        let limit = limit.unwrap_or(10) as usize;
        let prefix = format!("{}::", challenge_id);

        let mut entries: Vec<(AccountId, u32)> = self
            .scores
            .iter()
            .filter_map(|(key, record)| {
                key.strip_prefix(&prefix).and_then(|user_str| {
                    AccountId::try_from(user_str.to_string())
                        .ok()
                        .map(|user| (user, record.score_bp))
                })
            })
            .collect();

        entries.sort_by(|a, b| b.1.cmp(&a.1)); // descending
        entries.truncate(limit);
        entries
    }

    pub fn get_score(
        &self,
        challenge_id: String,
        user: AccountId,
    ) -> Option<ScoreRecord> {
        self.scores.get(&score_key(&challenge_id, &user)).cloned()
    }

    /// Returns the locked output for (challenge, user).
    /// `unlocked: false` until release_bounty is called.
    pub fn get_locked_output(
        &self,
        challenge_id: String,
        user: AccountId,
    ) -> Option<LockedOutput> {
        self.locked_outputs.get(&score_key(&challenge_id, &user)).cloned()
    }
}

// ── Internal helpers ──────────────────────────────────────────────────────────

/// Composite storage key for per-(challenge, user) maps.
fn score_key(challenge_id: &str, user: &AccountId) -> String {
    format!("{}::{}", challenge_id, user)
}
