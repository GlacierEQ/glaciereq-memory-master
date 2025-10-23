#!/usr/bin/env python3
"""
Migration Helper - Automated Repository Consolidation
Migrates Phase 1 repositories using git subtree with history preservation
"""

import os
import subprocess
import json
from pathlib import Path

class MigrationHelper:
    def __init__(self):
        # Load consolidation config
        with open('consolidation-config.json', 'r') as f:
            self.config = json.load(f)
        
        self.github_org = self.config['github_org']
        self.source_repos = self.config['source_repos']
        
    def run_command(self, cmd: List[str], cwd: str = '.') -> tuple[bool, str]:
        """Run shell command and return success status and output"""
        try:
            result = subprocess.run(
                cmd, 
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, f"Error: {e.stderr}"
    
    def migrate_repository(self, target_path: str, source_repo: str) -> bool:
        """Migrate repository using git subtree"""
        print(f"🚚 Migrating {source_repo} → {target_path}")
        
        # Create target directory
        Path(target_path).mkdir(parents=True, exist_ok=True)
        
        # Add remote
        remote_name = f"{source_repo}-remote"
        remote_url = f"https://github.com/{self.github_org}/{source_repo}.git"
        
        success, output = self.run_command(['git', 'remote', 'add', remote_name, remote_url])
        if not success and 'already exists' not in output:
            print(f"  ❌ Failed to add remote: {output}")
            return False
        
        # Fetch repository
        print(f"  📥 Fetching {source_repo}...")
        success, output = self.run_command(['git', 'fetch', remote_name])
        if not success:
            print(f"  ❌ Failed to fetch: {output}")
            return False
        
        # Add as subtree (preserves history)
        print(f"  🌳 Adding subtree...")
        success, output = self.run_command([
            'git', 'subtree', 'add', 
            '--prefix', target_path,
            remote_name, 'main', 
            '--squash'
        ])
        
        if not success:
            print(f"  ❌ Failed to add subtree: {output}")
            return False
        
        print(f"  ✅ Migration complete: {source_repo}")
        return True
    
    def run_phase_1_migration(self) -> Dict[str, bool]:
        """Execute Phase 1 critical repository migrations"""
        print("🚀 PHASE 1 MIGRATION: Critical Memory Core")
        print("=" * 50)
        
        results = {}
        
        for target_path, source_repo in self.source_repos.items():
            success = self.migrate_repository(target_path, source_repo)
            results[source_repo] = success
            
            if success:
                print(f"  ✅ {source_repo} → {target_path}")
            else:
                print(f"  ❌ {source_repo} FAILED")
        
        # Summary
        successful = sum(results.values())
        total = len(results)
        
        print(f"\n📊 MIGRATION SUMMARY:")
        print(f"  Successful: {successful}/{total}")
        print(f"  Success Rate: {(successful/total)*100:.1f}%")
        
        if successful == total:
            print("\n🎉 PHASE 1 COMPLETE - All critical repositories migrated!")
        else:
            print("\n⚠️  Some migrations failed - check errors above")
        
        return results
    
    def validate_migration(self) -> Dict:
        """Validate that all expected directories exist"""
        validation_results = {}
        
        for target_path, source_repo in self.source_repos.items():
            path_exists = Path(target_path).exists()
            has_files = len(list(Path(target_path).rglob('*'))) > 0 if path_exists else False
            
            validation_results[source_repo] = {
                'path_exists': path_exists,
                'has_files': has_files,
                'status': 'VALID' if path_exists and has_files else 'INVALID'
            }
        
        return validation_results

if __name__ == '__main__':
    migrator = MigrationHelper()
    
    print("GlacierEQ Memory Master - Migration Helper")
    print("Phase 1: Critical Memory Core Migration\n")
    
    # Run migration
    results = migrator.run_phase_1_migration()
    
    # Validate migration
    print("\n🔍 VALIDATION:")
    validation = migrator.validate_migration()
    
    for repo, status in validation.items():
        icon = "✅" if status['status'] == 'VALID' else "❌"
        print(f"  {icon} {repo}: {status['status']}")
    
    print("\n🏁 Migration helper complete.")