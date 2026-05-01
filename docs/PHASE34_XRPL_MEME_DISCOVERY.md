# Phase 34: XRPL Meme Discovery Engine

## Overview
The XRPL Meme Discovery Engine is an autonomous, read-only module designed to detect early signals of new tokens (memecoins or otherwise) launching on the XRP Ledger. It analyzes transaction fixtures to identify new trustline creation, AMM deployments, and issuer distribution activity.

## XRPL Token Model & Discovery
On the XRPL, tokens are not "deployed" via a smart contract. They exist as soon as a `TrustSet` transaction establishes a trustline between an account and an issuer, and a `Payment` delivers a balance. Therefore, discovery relies on detecting these events early.

## Detection Signals
- **Trustline Creation**: `TrustSet` transactions indicate user interest in receiving a token.
- **AMM Creation**: `AMMCreate` transactions indicate the token has been seeded with decentralized liquidity. This is the strongest signal of a serious launch.
- **Offer Activity**: `OfferCreate` transactions provide weak signals. Anyone can place an offer for any currency pair. Without metadata proving the offer was filled or had a meaningful impact, this remains a low-confidence signal.
- **Issuer Activity**: Payments originating from the token's issuer often indicate initial distribution or airdrops.

## Why Offers ≠ Liquidity
A standing `OfferCreate` does not mean the liquidity is accessible or correctly priced. Only an AMM or a deep, metadata-validated order book proves real liquidity.

## Metadata Dependency
Metadata is crucial. Without the `meta` field from a validated ledger, the engine cannot confirm if a `TrustSet` succeeded or an `AMMCreate` executed. Missing metadata severely penalizes candidate scores and forces a "low confidence" ceiling.

## Limitations
- **No live connection**: The Phase 34 prototype operates on historical fixtures. Live websocket streaming is reserved for future implementation.
- **FirstLedger API**: Not natively integrated; acts as an optional placeholder.

## Safety & No Auto-Trading
This module is **strictly advisory**. It produces "Candidates for human review." It does NOT produce "Buy signals."
There is absolutely zero trading automation, auto-calibration, signing, or submission logic in this module. The risk flags explicitly enforce a `prohibited_auto_action` string prohibiting automated buying.
