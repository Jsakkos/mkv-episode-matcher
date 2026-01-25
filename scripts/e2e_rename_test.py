from pathlib import Path
import shutil
import logging
import sys

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_test_files():
    main_folder = Path(r'X:\media\rips\Tests')
    if not main_folder.exists():
        logger.error(f"Test folder not found: {main_folder}")
        return False

    logger.info(f"Resetting test files in {main_folder}")
    
    # Rename logic as requested by user
    mkv_files = list(main_folder.rglob('*.mkv'))
    logger.info(f"Found {len(mkv_files)} MKV files to reset")
    
    for i, mkv_file in enumerate(mkv_files, start=1):
        try:
            new_name = mkv_file.parent / f'{i:02d}.mkv'
            if mkv_file != new_name:
                mkv_file.rename(new_name)
                logger.info(f"Renamed {mkv_file.name} -> {new_name.name}")
        except Exception as e:
            logger.error(f"Failed to rename {mkv_file}: {e}")
            
    return True

if __name__ == "__main__":
    success = setup_test_files()
    sys.exit(0 if success else 1)
