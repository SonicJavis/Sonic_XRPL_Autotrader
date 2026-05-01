import argparse
import sys
from pathlib import Path
import hashlib
from .models import DataAdapterConfig, AdapterRunSummary
from .clio_adapter import ClioAdapter
from .xrpl_rpc_adapter import XrplRpcAdapter
from .firstledger_adapter import FirstLedgerAdapter
from .exporter import export_fixtures
from .report_writer import write_adapter_report

def main():
    parser = argparse.ArgumentParser(description="Phase 41 Read-Only Data Adapters")
    parser.add_argument("--source", choices=["fixture", "clio", "xrpl_rpc", "firstledger"], default="fixture")
    parser.add_argument("--endpoint", help="API endpoint")
    parser.add_argument("--enable-network-read", action="store_true", help="Explicitly enable network access")
    parser.add_argument("--ledger-min", type=int, help="Minimum ledger index")
    parser.add_argument("--ledger-max", type=int, help="Maximum ledger index")
    parser.add_argument("--account", help="XRPL account")
    parser.add_argument("--max-records", type=int, default=1000)
    parser.add_argument("--max-pages", type=int, default=10)
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Dry run mode (default: True)")
    parser.add_argument("--no-dry-run", dest="dry_run", action="store_false", help="Disable dry run mode")
    
    args = parser.parse_args()
    
    # 1. Config
    config = DataAdapterConfig(
        adapter_id=hashlib.sha256(f"{args.source}:{args.endpoint}".encode()).hexdigest(),
        source_type=args.source,
        endpoint=args.endpoint,
        network_read_enabled=args.enable_network_read,
        ledger_min=args.ledger_min,
        ledger_max=args.ledger_max,
        account=args.account,
        max_records=args.max_records,
        max_pages=args.max_pages,
        dry_run=args.dry_run
    )
    
    # 2. Select Adapter
    adapter = None
    if args.source == "clio":
        adapter = ClioAdapter(config)
    elif args.source == "xrpl_rpc":
        adapter = XrplRpcAdapter(config)
    elif args.source == "firstledger":
        adapter = FirstLedgerAdapter(config)
    else:
        # Fixture mode (manual or previous raw records)
        print("Fixture source mode not yet fully implemented in CLI.")
        sys.exit(0)
        
    # 3. Execute
    try:
        raw_records = adapter.fetch_records()
        
        summary = AdapterRunSummary(
            run_id=hashlib.sha256(f"{config.adapter_id}:run".encode()).hexdigest(),
            source_type=args.source,
            network_read_enabled=args.enable_network_read,
            dry_run=args.dry_run,
            records_read=len(raw_records),
            fixtures_written=0, # Normalization placeholder
            quality_score=100
        )
        
        if not args.dry_run:
            out_path = export_fixtures(Path(args.output_dir), raw_records, [], summary)
            write_adapter_report(out_path / "adapter_report.md", summary)
            print(f"Export successful. Saved to: {out_path}")
        else:
            print("Dry run complete. No records written.")
            
    except PermissionError as e:
        print(f"Safety Error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
