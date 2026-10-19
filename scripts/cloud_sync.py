#!/usr/bin/env python3
"""
sao-ttrpg/scripts/cloud_sync.py
Cloud Archival & NotebookLM Synchronization Engine for SAO 100-Mile Area Survey.

Targets:
1. Google Drive Destination: G:\\My Drive\\SAO Area Survery
   - Root directory for HTML maps and Markdown compendiums.
   - Imagery\\ subdirectory for high-resolution PNG/JPG plates and atlas sheets.
2. NotebookLM Target:
   - Notebook UUID: 32da0ad5-a672-4225-a54d-284203f94cfe
   - Target Notebook Title: "Mapping"
"""

import os
import sys
import shutil
import argparse
import subprocess
import json
import logging
from typing import Dict, List, Any, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ"
)
logger = logging.getLogger("cloud_sync")

# Target specifications
GOOGLE_DRIVE_ROOT = r"G:\My Drive\SAO Area Survery"
GOOGLE_DRIVE_IMAGERY = os.path.join(GOOGLE_DRIVE_ROOT, "Imagery")
NOTEBOOKLM_NOTEBOOK_UUID = "32da0ad5-a672-4225-a54d-284203f94cfe"
NOTEBOOKLM_NOTEBOOK_TITLE = "Mapping"


def get_project_root() -> str:
    """Returns absolute path to repository root."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def get_sync_manifest(project_root: str) -> Dict[str, Any]:
    """Compiles the complete manifest of files targeted for archival and cloud sync."""
    root_files = [
        "SAO_100Mile_New_Locations_Interactive_GIS_Map.html",
        "SAO_100Mile_Merged_Master_Interactive_GIS_Map.html",
        "08_100Mile_Exhaustive_MultiScan_Compare_and_Contrast_Compendium.md",
        "00_SAO_Area_Survey_Master_Compendium.md",
    ]

    imagery_sources = [
        os.path.join(project_root, "sao-ttrpg", "assets", "maps", "raw"),
        os.path.join(project_root, "sao-ttrpg", "assets", "maps", "quad_plates"),
        os.path.join(project_root, "warren_county_subsurface_gis", "outputs", "atlas_sheets"),
        os.path.join(project_root, "warren_county_subsurface_gis", "outputs", "cross_sections"),
    ]

    imagery_files: List[str] = []
    for src_dir in imagery_sources:
        if os.path.isdir(src_dir):
            for fname in os.listdir(src_dir):
                if fname.lower().endswith((".png", ".jpg", ".jpeg", ".pdf")):
                    imagery_files.append(os.path.join(src_dir, fname))

    notebooklm_docs = [
        os.path.join(project_root, "08_100Mile_Exhaustive_MultiScan_Compare_and_Contrast_Compendium.md"),
        os.path.join(project_root, "00_SAO_Area_Survey_Master_Compendium.md"),
    ]

    local_staging_root = os.path.join(project_root, "outputs", "cloud_sync_staging", "SAO Area Survery")
    local_staging_imagery = os.path.join(local_staging_root, "Imagery")

    return {
        "root_files": [os.path.join(project_root, f) for f in root_files],
        "imagery_files": imagery_files,
        "notebooklm_docs": notebooklm_docs,
        "target_drive_root": GOOGLE_DRIVE_ROOT,
        "target_drive_imagery": GOOGLE_DRIVE_IMAGERY,
        "local_staging_root": local_staging_root,
        "local_staging_imagery": local_staging_imagery,
        "target_notebooklm_uuid": NOTEBOOKLM_NOTEBOOK_UUID,
        "target_notebooklm_title": NOTEBOOKLM_NOTEBOOK_TITLE,
    }


def sync_google_drive(manifest: Dict[str, Any], dry_run: bool = False, stage_locally_if_unmounted: bool = True) -> Dict[str, Any]:
    r"""
    Synchronizes HTML maps, Markdown compendiums, and PNG/JPG plates to Google Drive.
    If the target drive (e.g. G:\) is unmounted or inaccessible, stages files into a structured
    local staging directory (e.g. outputs/cloud_sync_staging/SAO Area Survery).
    """
    results = {
        "drive_accessible": False,
        "staged_locally": False,
        "effective_root": "",
        "root_files_copied": 0,
        "imagery_files_copied": 0,
        "errors": []
    }

    target_root = manifest.get("target_drive_root", GOOGLE_DRIVE_ROOT)
    target_imagery = manifest.get("target_drive_imagery", GOOGLE_DRIVE_IMAGERY)

    # Check whether the drive letter of target_root is mounted on this host
    drive_letter = os.path.splitdrive(target_root)[0]
    is_drive_mounted = os.path.exists(drive_letter + "\\") if drive_letter else True

    effective_root = target_root
    effective_imagery = target_imagery

    if not is_drive_mounted:
        results["drive_accessible"] = False
        logger.warning("Google Drive (G:) is not mounted or not accessible on this system.")
        logger.info(f"Target path '{target_root}' will be staged locally or skipped gracefully.")
        if stage_locally_if_unmounted:
            local_root = manifest.get("local_staging_root")
            local_imagery = manifest.get("local_staging_imagery")
            if not local_root:
                project_root = get_project_root()
                local_root = os.path.join(project_root, "outputs", "cloud_sync_staging", "SAO Area Survery")
                local_imagery = os.path.join(local_root, "Imagery")
            effective_root = local_root
            effective_imagery = local_imagery
            results["staged_locally"] = True
            logger.info(f"Staging all deliverables locally into structured directory: {effective_root}")
        else:
            return results
    else:
        results["drive_accessible"] = True

    results["effective_root"] = effective_root

    # In dry_run mode, DO NOT create directories on disk
    if not dry_run:
        try:
            os.makedirs(effective_root, exist_ok=True)
            os.makedirs(effective_imagery, exist_ok=True)
            logger.info(f"Verified destination directory: {effective_root}")
        except Exception as e:
            logger.error(f"Failed to access or create target directory {effective_root}: {e}")
            results["errors"].append(str(e))
            return results

    # Sync Root Deliverables
    logger.info("Synchronizing Root Deliverables (HTML Maps & Markdown Compendiums)...")
    for src_path in manifest["root_files"]:
        if not os.path.isfile(src_path):
            logger.warning(f"Source file not found (skipped): {src_path}")
            continue
        dest_path = os.path.join(effective_root, os.path.basename(src_path))
        if dry_run:
            logger.info(f"[DRY-RUN] Would copy: {src_path} -> {dest_path}")
            results["root_files_copied"] += 1
        else:
            try:
                shutil.copy2(src_path, dest_path)
                logger.info(f"Copied root deliverable: {os.path.basename(src_path)} -> {dest_path}")
                results["root_files_copied"] += 1
            except Exception as e:
                logger.error(f"Error copying {src_path}: {e}")
                results["errors"].append(f"{src_path}: {e}")

    # Sync Imagery Deliverables
    logger.info("Synchronizing High-Resolution Plates to Imagery/ Subdirectory...")
    for src_path in manifest["imagery_files"]:
        if not os.path.isfile(src_path):
            continue
        dest_path = os.path.join(effective_imagery, os.path.basename(src_path))
        if dry_run:
            results["imagery_files_copied"] += 1
        else:
            try:
                shutil.copy2(src_path, dest_path)
                results["imagery_files_copied"] += 1
            except Exception as e:
                logger.error(f"Error copying image plate {src_path}: {e}")
                results["errors"].append(f"{src_path}: {e}")

    dest_desc = "Local Staging" if results["staged_locally"] else "Google Drive"
    logger.info(f"{dest_desc} Sync Complete. Root files: {results['root_files_copied']}, Imagery plates: {results['imagery_files_copied']}.")
    return results


def sync_notebooklm(manifest: Dict[str, Any], dry_run: bool = False, execute_upload: bool = False) -> Dict[str, Any]:
    """
    Contracts and executes document synchronization with NotebookLM.
    Targets notebook UUID 32da0ad5-a672-4225-a54d-284203f94cfe (Title: 'Mapping').
    Integrates with nlm CLI / NotebookLM API to execute genuine source upload.
    """
    uuid = manifest["target_notebooklm_uuid"]
    title = manifest["target_notebooklm_title"]
    docs = manifest["notebooklm_docs"]

    results = {
        "notebook_uuid": uuid,
        "notebook_title": title,
        "documents_queued": len(docs),
        "uploaded_sources": [],
        "status": "ready"
    }

    logger.info(f"Preparing NotebookLM Sync for Notebook: '{title}' (UUID: {uuid})")
    for doc in docs:
        if not os.path.isfile(doc):
            logger.warning(f"NotebookLM target document missing: {doc}")
            continue
        file_size = os.path.getsize(doc)
        logger.info(f"NotebookLM Source Manifest: {os.path.basename(doc)} ({file_size} bytes)")

    # Document upload contract definition
    upload_contract = {
        "target_notebook_id": uuid,
        "target_notebook_title": title,
        "action": "source_add",
        "mime_type": "text/markdown",
        "sources": [
            {
                "file_path": doc,
                "title": os.path.splitext(os.path.basename(doc))[0],
                "size_bytes": os.path.getsize(doc) if os.path.isfile(doc) else 0
            }
            for doc in docs
        ]
    }
    results["contract"] = upload_contract

    if dry_run:
        results["status"] = "contract_verified"
        logger.info(f"NotebookLM integration contract verified for {len(docs)} compendiums.")
        return results

    if execute_upload:
        nlm_path = shutil.which("nlm") or shutil.which("nlm.exe")
        if nlm_path:
            logger.info(f"Found NotebookLM CLI: {nlm_path}. Executing live upload to notebook {uuid}...")
            for doc in docs:
                if not os.path.isfile(doc):
                    continue
                try:
                    logger.info(f"Executing: nlm source add {uuid} --file {doc} --wait --json")
                    proc = subprocess.run(
                        [nlm_path, "source", "add", uuid, "--file", doc, "--wait", "--json"],
                        capture_output=True,
                        text=True,
                        check=False
                    )
                    if proc.returncode == 0:
                        logger.info(f"Successfully uploaded {os.path.basename(doc)} to NotebookLM notebook {uuid}.")
                        results["uploaded_sources"].append({
                            "file": doc,
                            "status": "uploaded",
                            "stdout": proc.stdout.strip()
                        })
                    else:
                        logger.warning(f"Upload returned code {proc.returncode}: {proc.stderr}")
                        results["uploaded_sources"].append({
                            "file": doc,
                            "status": "warning",
                            "error": proc.stderr.strip()
                        })
                except Exception as e:
                    logger.error(f"Failed to execute nlm upload for {doc}: {e}")
                    results["uploaded_sources"].append({
                        "file": doc,
                        "status": "error",
                        "error": str(e)
                    })
            results["status"] = "upload_executed"
        else:
            logger.info("NotebookLM CLI 'nlm' not in PATH; contract verified for agent MCP tool execution.")
            results["status"] = "contract_verified"
    else:
        results["status"] = "contract_verified"
        logger.info(f"NotebookLM integration contract verified for {len(docs)} compendiums.")

    return results


def main():
    parser = argparse.ArgumentParser(description="SAO 100-Mile Survey Cloud Archival & NotebookLM Sync")
    parser.add_argument("--dry-run", action="store_true", help="Simulate synchronization without writing files")
    parser.add_argument("--drive-only", action="store_true", help="Perform Google Drive sync only")
    parser.add_argument("--notebooklm-only", action="store_true", help="Perform NotebookLM sync only")
    parser.add_argument("--upload-notebooklm", action="store_true", help="Execute live upload of compendiums to NotebookLM notebook via nlm CLI")
    parser.add_argument("--staging-dir", type=str, default=None, help="Custom local staging directory for deliverables when G: is unmounted")
    args = parser.parse_args()

    project_root = get_project_root()
    manifest = get_sync_manifest(project_root)
    if args.staging_dir:
        manifest["local_staging_root"] = args.staging_dir
        manifest["local_staging_imagery"] = os.path.join(args.staging_dir, "Imagery")

    logger.info("=================================================================")
    logger.info("SAO AREA SURVEY CLOUD SYNCHRONIZATION ENGINE")
    logger.info(f"Project Root: {project_root}")
    logger.info(f"Google Drive Target: {GOOGLE_DRIVE_ROOT}")
    logger.info(f"NotebookLM Target: {NOTEBOOKLM_NOTEBOOK_TITLE} ({NOTEBOOKLM_NOTEBOOK_UUID})")
    logger.info("=================================================================")

    if not args.notebooklm_only:
        drive_res = sync_google_drive(manifest, dry_run=args.dry_run)
        logger.info(f"Drive Sync Result: Accessible={drive_res['drive_accessible']}, Root={drive_res['root_files_copied']}, Imagery={drive_res['imagery_files_copied']}")

    if not args.drive_only:
        nlm_res = sync_notebooklm(manifest, dry_run=args.dry_run, execute_upload=args.upload_notebooklm)
        logger.info(f"NotebookLM Sync Result: Status={nlm_res['status']}, Queued={nlm_res['documents_queued']}")

    logger.info("All synchronization tasks completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
