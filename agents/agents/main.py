
"""
Main orchestration script for running Discovery, Scanning, and Detection Agents
Stores discovery results, retries scanning with exponential backoff, and cleans up old data
"""

import sys
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List
import psycopg2
from google.api_core.exceptions import GoogleAPIError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Import agents
from .modular_discovery_agent import ModularDiscoveryAgent
from .modular_scanning_agent import ModularScanningAgent
from .modular_detection_agent import ModularDetectionAgent
from .postgresql_db_manager import PostgreSQLCloudScanDBManager

def cleanup_old_stores(db_manager: PostgreSQLCloudScanDBManager, client_id: str, days_old: int = 30) -> int:
    """
    Remove data stores older than specified days for the given client
    
    Args:
        db_manager: PostgreSQLCloudScanDBManager instance
        client_id: Client ID for scoping
        days_old: Age threshold for deletion (days)
        
    Returns:
        Number of deleted stores
    """
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM data_stores 
            WHERE client_id = %s 
            AND discovery_timestamp < %s 
            AND store_id NOT IN (SELECT store_id FROM scans_findings WHERE scan_timestamp >= %s)
            """,
            (client_id, datetime.now() - timedelta(days=days_old), datetime.now() - timedelta(days=days_old))
        )
        deleted_count = cursor.rowcount
        conn.commit()
        logger.info(f"Cleaned up {deleted_count} old data stores for client {client_id}")
        cursor.close()
        conn.close()
        return deleted_count
    except psycopg2.Error as e:
        logger.error(f"Database error during cleanup_old_stores: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during cleanup_old_stores: {e}")
        raise

def check_existing_discovery(db_manager: PostgreSQLCloudScanDBManager, client_id: str) -> List[Dict]:
    """
    Check for existing accessible data stores in the database
    
    Args:
        db_manager: PostgreSQLCloudScanDBManager instance
        client_id: Client ID for scoping
        
    Returns:
        List of accessible data stores
    """
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT store_id, store_name, location, store_type, access_control 
            FROM data_stores 
            WHERE client_id = %s AND status = %s
            """,
            (client_id, 'accessible')
        )
        stores = [
            {
                'store_id': row[0],
                'name': row[1],
                'location': row[2],
                'type': row[3],
                'access_control': row[4],
                'status': 'accessible'
            } for row in cursor.fetchall()
        ]
        cursor.close()
        conn.close()
        logger.info(f"Found {len(stores)} existing accessible data stores")
        return stores
    except psycopg2.Error as e:
        logger.error(f"Database error checking existing discovery: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error checking existing discovery: {e}")
        raise

def run_pipeline(client_id: str = None, max_scan_retries: int = 3, base_backoff: float = 1.0) -> dict:
    """
    Run the full pipeline: Discovery -> Scanning -> Detection
    Stores discovery results, retries scanning with exponential backoff, and cleans up old data
    
    Args:
        client_id: Client ID for multi-tenant operations
        max_scan_retries: Maximum number of scan retries
        base_backoff: Base delay (seconds) for exponential backoff
        
    Returns:
        Dictionary containing pipeline results
    """
    pipeline_results = {
        'client_id': client_id,
        'timestamp': datetime.now().isoformat(),
        'stages': {},
        'status': 'in_progress',
        'error': None
    }

    try:
        # Initialize discovery agent for db_manager
        discovery_agent = ModularDiscoveryAgent(client_id=client_id)
        db_manager = discovery_agent.db_manager

        # Clean up old data stores before starting
        logger.info("Cleaning up old data stores...")
        # cleanup_old_stores(db_manager, client_id)

        # Stage 1: Discovery (check existing or run new)
        try:
            logger.info("Checking for existing discovery data sources...")
            accessible_sources = check_existing_discovery(db_manager, client_id)
            
            if not accessible_sources:
                logger.info("No existing discovery results found. Starting Discovery Agent...")
                discovery_results = discovery_agent.discover_all_sources()
            else:
                discovery_results = {
                    'sources_discovered': accessible_sources,
                    'total_sources': len(accessible_sources),
                    'discovery_timestamp': datetime.now().isoformat(),
                    'status': 'available'
                }
        except (GoogleAPIError, psycopg2.Error) as e:
            raise RuntimeError(f"Discovery failed due to service error: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Discovery failed: {str(e)}")

        # Check discovery success
        accessible_sources = [
            source for source in discovery_results.get('sources_discovered', [])
            if source.get('status') == 'accessible'
        ]
        if not accessible_sources:
            raise RuntimeError(
                f"Discovery failed: No accessible sources found (total: {discovery_results.get('total_sources', 0)})"
            )

        pipeline_results['stages']['discovery'] = {
            'status': 'successful',
            'sources_discovered': len(accessible_sources),
            'total_sources': discovery_results.get('total_sources', 0),
            'recommendations': discovery_agent.get_source_recommendations(discovery_results)
        }
        logger.info(f"Discovery completed: {len(accessible_sources)} accessible sources found")

        # Stage 2: Scanning with retries and exponential backoff
        logger.info("Starting Scanning Agent...")
        scanning_agent = ModularScanningAgent(client_id=client_id)
        retry_count = 0
        scanning_results = None

        while retry_count <= max_scan_retries:
            try:
                scanning_results = scanning_agent.scan_all_sources()
                successful_scans = [
                    result for result in scanning_results.get('sources_scanned', [])
                    if result.get('status') in ['completed', 'successful_mock'] and
                    result.get('database_stored', False)
                ]
                if successful_scans:
                    break  # Exit retry loop on success
                else:
                    raise RuntimeError("No successful scans")
            except (GoogleAPIError, psycopg2.Error, ConnectionError) as e:
                retry_count += 1
                if retry_count > max_scan_retries:
                    raise RuntimeError(f"Scanning failed after {max_scan_retries} retries: {str(e)}")
                backoff_time = base_backoff * (2 ** (retry_count - 1))  # Exponential backoff: 1s, 2s, 4s
                logger.warning(
                    f"Scanning attempt {retry_count}/{max_scan_retries} failed: {str(e)}. "
                    f"Retrying in {backoff_time} seconds..."
                )
                time.sleep(backoff_time)
            except Exception as e:
                raise RuntimeError(f"Scanning failed with unrecoverable error: {str(e)}")

        if not scanning_results:
            raise RuntimeError("Scanning failed: No results obtained after retries")

        # Check scanning success
        successful_scans = [
            result for result in scanning_results.get('sources_scanned', [])
            if result.get('status') in ['completed', 'successful_mock'] and
            result.get('database_stored', False)
        ]
        if not successful_scans:
            raise RuntimeError(
                f"Scanning failed: No successful scans (total: {scanning_results.get('total_sources', 0)})"
            )

        pipeline_results['stages']['scanning'] = {
            'status': 'successful',
            'sources_scanned': len(successful_scans),
            'total_findings': scanning_results.get('total_findings', 0),
            'scan_ids': [result.get('scan_id') for result in successful_scans]
        }
        logger.info(f"Scanning completed: {len(successful_scans)} sources scanned, {scanning_results.get('total_findings', 0)} findings")

        # Clean up failed scans
        failed_scans = [
            result.get('scan_id') for result in scanning_results.get('sources_scanned', [])
            if result.get('status') not in ['completed', 'successful_mock'] or
            not result.get('database_stored', False)
        ]
        for scan_id in failed_scans:
            if scan_id:
                logger.info(f"Cleaning up failed scan ID: {scan_id}")
                try:
                    db_manager.delete_scan(scan_id)
                except psycopg2.Error as e:
                    logger.error(f"Error deleting failed scan ID {scan_id}: {e}")
                    raise RuntimeError(f"Failed to clean up scan ID {scan_id}: {str(e)}")

        # Stage 3: Detection
        logger.info("Starting Detection Agent...")
        detection_agent = ModularDetectionAgent(client_id=client_id)
        detection_results = []

        try:
            for scan_result in successful_scans:
                scan_id = scan_result.get('scan_id')
                if scan_id:
                    logger.info(f"Analyzing findings for scan ID: {scan_id}")
                    analysis_results = detection_agent.analyze_scan_findings(scan_id)
                    
                    if analysis_results.get('total_findings', 0) == 0:
                        logger.warning(f"No findings to analyze for scan ID: {scan_id}")
                        continue
                    
                    detection_results.append({
                        'scan_id': scan_id,
                        'total_findings': analysis_results.get('total_findings', 0),
                        'overall_risk': 'unknown',
                        'recommendations': analysis_results.get('recommendations', [])
                    })
        except psycopg2.Error as e:
            raise RuntimeError(f"Detection failed due to database error: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Detection failed: {str(e)}")

        if not detection_results:
            raise RuntimeError("Detection failed: No scans had findings to analyze")

        pipeline_results['stages']['detection'] = {
            'status': 'successful',
            'analyses_performed': len(detection_results),
            'results': detection_results
        }
        logger.info(f"Detection completed: {len(detection_results)} scans analyzed")

        # Pipeline success
        pipeline_results['status'] = 'successful'
        logger.info("Pipeline completed successfully")

    except Exception as e:
        pipeline_results['status'] = 'failed'
        pipeline_results['error'] = str(e)
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

    return pipeline_results

def main():
    """Main entry point"""
    client_id = 'VV4IfgQrcbNKIquovwwRAu87Ife2'  # Example client ID
    max_scan_retries = 3  # Maximum scan retries
    base_backoff = 1.0  # Base backoff time in seconds
    logger.info(f"Starting pipeline for client: {client_id} with {max_scan_retries} scan retries")
    results = run_pipeline(client_id, max_scan_retries, base_backoff)
    
    # Print summary
    print("\n📊 Pipeline Summary:")
    print(f"Client ID: {results['client_id']}")
    print(f"Status: {results['status']}")
    print(f"Timestamp: {results['timestamp']}")
    
    if results['status'] == 'successful':
        discovery = results['stages'].get('discovery', {})
        scanning = results['stages'].get('scanning', {})
        detection = results['stages'].get('detection', {})
        
        print(f"\nDiscovery Stage:")
        print(f"- Sources Discovered: {discovery.get('sources_discovered', 0)}/{discovery.get('total_sources', 0)}")
        print(f"- Recommendations: {len(discovery.get('recommendations', []))}")
        
        print(f"\nScanning Stage:")
        print(f"- Sources Scanned: {scanning.get('sources_scanned', 0)}")
        print(f"- Total Findings: {scanning.get('total_findings', 0)}")
        
        print(f"\nDetection Stage:")
        print(f"- Analyses Performed: {detection.get('analyses_performed', 0)}")
        for result in detection.get('results', []):
            print(f"  Scan ID {result['scan_id']}: {result['total_findings']} findings, Risk: {result['overall_risk']}")
    
    if results['error']:
        print(f"\n❌ Error: {results['error']}")

if __name__ == "__main__":
    main()
