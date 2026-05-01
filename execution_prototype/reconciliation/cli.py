import argparse
import sys
import json
from execution_prototype.reconciliation.loaders import load_simulations, load_lifecycle_events
from execution_prototype.reconciliation.comparator import reconcile
from execution_prototype.reconciliation.report_writer import write_reports

def main():
    parser = argparse.ArgumentParser(description="Phase 30 Simulation vs Reality Reconciliation")
    parser.add_argument("--simulation-source", required=True, help="Path to simulation records directory")
    parser.add_argument("--lifecycle-source", required=True, help="Path to lifecycle records directory")
    parser.add_argument("--output-dir", required=True, help="Output directory for reports")
    parser.add_argument("--format", choices=["jsonl", "csv", "both"], default="both", help="Output format")
    
    args = parser.parse_args()
    
    print("Loading simulation records...")
    simulations = load_simulations(args.simulation_source)
    print(f"Loaded {len(simulations)} simulation records.")
    
    print("Loading lifecycle records...")
    lifecycle_events = load_lifecycle_events(args.lifecycle_source)
    print(f"Loaded {len(lifecycle_events)} unique lifecycle records.")
    
    if not simulations and not lifecycle_events:
        print("No data found to reconcile.")
        sys.exit(0)
        
    print("Matching and reconciling records...")
    reconciled_records = []
    
    # Priority matching: 1. session_id, 2. intent_id
    # We will try to match every simulation. If a simulation has no match, it will not produce a valid reconciliation? Or it produces one with missing actual data.
    # The prompt implies comparing existing overlaps.
    for sim in simulations:
        match = None
        is_ambiguous = False
        
        # 1. Match by session_id
        if sim.session_id:
            candidates = [l for l in lifecycle_events if l.session_id == sim.session_id]
            if len(candidates) == 1:
                match = candidates[0]
            elif len(candidates) > 1:
                is_ambiguous = True
                
        # 2. Match by intent_id if no session_id match
        if not match and not is_ambiguous and sim.intent_id:
            candidates = [l for l in lifecycle_events if l.intent_id == sim.intent_id]
            if len(candidates) == 1:
                match = candidates[0]
            elif len(candidates) > 1:
                is_ambiguous = True
                
        # 3. Match by tx_hash (currently sim doesn't have tx_hash, so this is skipped for now, but priority is noted)
        
        if is_ambiguous:
            from execution_prototype.reconciliation.comparator import reconcile_ambiguous
            rec = reconcile_ambiguous(sim)
            reconciled_records.append(rec)
        elif match:
            rec = reconcile(sim, match)
            reconciled_records.append(rec)
            
    if not reconciled_records:
        print("No matches found between simulation and lifecycle records.")
        sys.exit(0)
        
    print("Writing reports...")
    out_info = write_reports(reconciled_records, args.output_dir, args.format)
    
    print("\nRECONCILIATION SUMMARY:")
    print(json.dumps(out_info["summary"], indent=2))
    print("\nFILES CREATED:")
    for f in out_info["files"]:
        print(f"- {f}")

if __name__ == "__main__":
    main()
