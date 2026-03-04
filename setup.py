"""
Setup file for mkv_episode_matcher.
"""

import os
import subprocess
import sys
from pathlib import Path
from setuptools import setup
from setuptools.command.build_py import build_py


class BuildWithFrontend(build_py):
    """Custom build command that builds the frontend before packaging."""
    
    def run(self):
        # Build frontend first
        self.build_frontend()
        # Then run standard build
        super().run()
    
    def build_frontend(self):
        """Build the frontend assets."""
        frontend_dir = Path("mkv_episode_matcher/frontend")
        dist_dir = frontend_dir / "dist"
        assets_dir = dist_dir / "assets"
        
        # Check if assets already exist and are recent
        if assets_dir.exists() and self._frontend_is_current(frontend_dir, dist_dir):
            print("Frontend assets are already up to date")
            return
            
        print("Building frontend assets...")
        
        # Check if we have Node.js
        try:
            subprocess.run(["node", "--version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("WARNING: Node.js not found. Frontend assets will not be built.")
            print("The web interface may not work correctly.")
            self._create_minimal_assets()
            return
            
        # Change to frontend directory and build
        original_cwd = os.getcwd()
        try:
            os.chdir(frontend_dir)
            
            # Install dependencies if needed
            if not Path("node_modules").exists():
                print("Installing frontend dependencies...")
                subprocess.run(["npm", "install"], check=True)
            
            # Build the frontend
            print("Building frontend...")
            subprocess.run(["npm", "run", "build"], check=True)
            print("Frontend build completed successfully!")
            
        except subprocess.CalledProcessError as e:
            print(f"WARNING: Frontend build failed: {e}")
            print("The web interface may not work correctly.")
            self._create_minimal_assets()
        except FileNotFoundError:
            print("WARNING: npm not found. Frontend assets will not be built.")
            self._create_minimal_assets()
        finally:
            os.chdir(original_cwd)
    
    def _frontend_is_current(self, frontend_dir, dist_dir):
        """Check if frontend build is current."""
        package_json = frontend_dir / "package.json"
        src_dir = frontend_dir / "src"
        assets_dir = dist_dir / "assets"
        
        if not assets_dir.exists():
            return False
            
        # Get modification times
        try:
            package_json_mtime = package_json.stat().st_mtime
            assets_mtime = min(f.stat().st_mtime for f in assets_dir.glob("*"))
            
            # Check if any source files are newer than assets
            for src_file in src_dir.rglob("*"):
                if src_file.is_file() and src_file.stat().st_mtime > assets_mtime:
                    return False
                    
            # Check if package.json is newer than assets
            if package_json_mtime > assets_mtime:
                return False
                
            return True
        except (OSError, ValueError):
            return False
    
    def _create_minimal_assets(self):
        """Create minimal assets directory structure to prevent runtime errors."""
        assets_dir = Path("mkv_episode_matcher/frontend/dist/assets")
        assets_dir.mkdir(parents=True, exist_ok=True)
        
        # Create empty placeholder files
        (assets_dir / "index.js").write_text("// Frontend build failed - placeholder file")
        (assets_dir / "index.css").write_text("/* Frontend build failed - placeholder file */")


if __name__ == "__main__":
    try:
        setup(
            use_scm_version={"version_scheme": "no-guess-dev"},
            cmdclass={"build_py": BuildWithFrontend}
        )
    except:  # noqa
        print(
            "\n\nAn error occurred while building the project, "
            "please ensure you have the most updated version of setuptools, "
            "setuptools_scm and wheel with:\n"
            "   pip install -U setuptools setuptools_scm wheel\n\n"
        )
        raise
