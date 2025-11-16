#!/usr/bin/env python3
"""
Check risk assessment data for a specific client ID
"""

import os
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

from postgresql_db_manager import PostgreSQLCloudScanDBManager

def check_risk_assessment_data(client_id: str):
    """Check if risk assessment data exists for the client"""
    print(f"Checking risk assessment data for client_id: {client_id}")
    
    try:
        db_manager = PostgreSQLCloudScanDBManager()
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Check risk_assessments table
        print("\nChecking risk_assessments table...")
        cursor.execute("""
            SELECT assessment_id, total_data_sources, total_sdes, scanned_sdes, 
                   high_risk_sdes, total_sensitive_records, risk_score, 
                   confidence_score, timestamp
            FROM risk_assessments
            WHERE client_id = %s
            ORDER BY timestamp DESC
            LIMIT 5
        """, (client_id,))
        
        risk_assessments = cursor.fetchall()
        print(f"Found {len(risk_assessments)} risk assessment records")
        
        if risk_assessments:
            print("\nLatest risk assessment data:")
            for i, row in enumerate(risk_assessments):
                print(f"Record {i+1}:")
                print(f"  Assessment ID: {row['assessment_id']}")
                print(f"  Total Data Sources: {row['total_data_sources']}")
                print(f"  Total SDEs: {row['total_sdes']}")
                print(f"  Scanned SDEs: {row['scanned_sdes']}")
                print(f"  High Risk SDEs: {row['high_risk_sdes']}")
                print(f"  Total Sensitive Records: {row['total_sensitive_records']}")
                print(f"  Risk Score: {row['risk_score']}")
                print(f"  Confidence Score: {row['confidence_score']}")
                print(f"  Timestamp: {row['timestamp']}")
                print()
        else:
                    print("FAILED: No risk assessment data found!")
        print("TIP: You need to run a risk assessment first using POST /risk/risk-assessment")
        
        # Check sdes table
        print("\nChecking sdes table...")
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM sdes
            WHERE client_id = %s
        """, (client_id,))
        
        sdes_count = cursor.fetchone()[0]
        print(f"Found {sdes_count} SDE records")
        
        # Check scan_findings table
        print("\nChecking scan_findings table...")
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM scan_findings
            WHERE client_id = %s
        """, (client_id,))
        
        findings_count = cursor.fetchone()[0]
        print(f"Found {findings_count} scan findings")
        
        conn.close()
        
        print(f"\nSummary for client_id: {client_id}")
        print(f"  Risk Assessments: {len(risk_assessments)}")
        print(f"  SDEs: {sdes_count}")
        print(f"  Scan Findings: {findings_count}")
        
        if len(risk_assessments) == 0:
            print("\nSOLUTION: You need to run a risk assessment first!")
            print("   Use: POST /risk/risk-assessment with body: {\"client_id\": \"" + client_id + "\"}")
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    client_id = input("Enter client_id to check: ").strip()
    if not client_id:
        print("ERROR: Please provide a client_id")
        sys.exit(1)
    
    check_risk_assessment_data(client_id) 