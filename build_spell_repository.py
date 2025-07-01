#!/usr/bin/env python3
"""
Build comprehensive spell repository with descriptions and metadata using OpenAI API.
Uses GPT-4.1-mini for cost-effective processing of all 245 unique spells.
"""

import json
import re
import time
import logging
from datetime import datetime
from openai import OpenAI
from config import OPENAI_API_KEY, DM_MINI_MODEL
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('spell_extraction_log.txt'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class SpellRepositoryBuilder:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = DM_MINI_MODEL
        self.repository_file = 'spell_repository.json'
        self.backup_file = 'spell_repository_backup.json'
        self.spells_processed = 0
        self.total_spells = 0
        
        # Load existing repository if it exists
        self.repository = self.load_repository()
        
    def load_repository(self):
        """Load existing repository or create new one"""
        try:
            with open(self.repository_file, 'r') as f:
                repository = json.load(f)
                # Remove metadata from count
                spell_count = len([k for k in repository.keys() if not k.startswith('_')])
                logger.info(f"Loaded existing repository with {spell_count} spells")
                return repository
        except FileNotFoundError:
            logger.info("Creating new spell repository")
            return {}
            
    def save_repository(self, backup=True):
        """Save repository to file with optional backup"""
        if backup and self.repository:
            # Create backup
            with open(self.backup_file, 'w') as f:
                json.dump(self.repository, f, indent=2)
        
        # Save main file
        with open(self.repository_file, 'w') as f:
            json.dump(self.repository, f, indent=2)
            
        logger.info(f"Repository saved with {len(self.repository)} spells")
        
    def normalize_spell_key(self, spell_name):
        """Convert spell name to normalized key"""
        key = spell_name.lower()
        key = re.sub(r"['\s/-]", '_', key)
        key = re.sub(r'_+', '_', key)
        key = key.strip('_')
        return key
        
    def extract_spell_classes(self, spell_name):
        """Extract which classes can use this spell from the mapping file"""
        classes = []
        try:
            with open('spell_class_mapping.txt', 'r') as f:
                content = f.read()
                
            # Find the spell in the mapping
            spell_section = None
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip() == f"{spell_name}:":
                    if i + 1 < len(lines):
                        classes_line = lines[i + 1].strip()
                        if classes_line.startswith('Classes:'):
                            # Extract class names from "Classes: Bard (Cantrips), Wizard (Cantrips), etc."
                            classes_text = classes_line.replace('Classes:', '').strip()
                            for class_entry in classes_text.split(','):
                                class_name = class_entry.split('(')[0].strip()
                                if class_name and class_name not in classes:
                                    classes.append(class_name)
                    break
        except FileNotFoundError:
            logger.warning("spell_class_mapping.txt not found, using default classes")
            
        return classes if classes else ["Unknown"]
        
    def get_spell_level_from_mapping(self, spell_name):
        """Extract spell level from the class mapping"""
        try:
            with open('spell_class_mapping.txt', 'r') as f:
                content = f.read()
                
            # Find the spell and extract level
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip() == f"{spell_name}:":
                    if i + 1 < len(lines):
                        classes_line = lines[i + 1].strip()
                        if classes_line.startswith('Classes:'):
                            # Look for level indicators like "(Cantrips)", "(1st)", etc.
                            if "(Cantrips)" in classes_line:
                                return 0
                            elif "(1st)" in classes_line:
                                return 1
                            elif "(2nd)" in classes_line:
                                return 2
                            elif "(3rd)" in classes_line:
                                return 3
                            elif "(4th)" in classes_line:
                                return 4
                            elif "(5th)" in classes_line:
                                return 5
                            elif "(6th)" in classes_line:
                                return 6
                            elif "(7th)" in classes_line:
                                return 7
                            elif "(8th)" in classes_line:
                                return 8
                            elif "(9th)" in classes_line:
                                return 9
                    break
        except FileNotFoundError:
            pass
            
        return 1  # Default to 1st level if not found
        
    def create_spell_prompt(self, spell_name):
        """Create prompt for AI to generate spell information"""
        return f"""Please provide detailed information for the 5th edition spell "{spell_name}" in the following JSON format. Use only official SRD 5.2.1 information (CC BY 4.0 licensed content). Be accurate and complete:

{{
  "name": "Exact spell name",
  "level": 0-9 (0 for cantrips),
  "school": "School of magic (e.g., Evocation, Divination, etc.)",
  "casting_time": "Casting time (e.g., 1 action, 1 bonus action, etc.)",
  "range": "Range (e.g., Self, Touch, 30 feet, etc.)",
  "components": {{
    "verbal": true/false,
    "somatic": true/false,
    "material": true/false,
    "materials": "specific material components if any, or empty string"
  }},
  "duration": "Duration (e.g., Instantaneous, Concentration, up to 1 minute, etc.)",
  "description": "Complete spell description from SRD",
  "higher_levels": "How spell changes at higher levels, or empty string if not applicable",
  "ritual": true/false,
  "concentration": true/false
}}

Respond with ONLY the JSON object, no additional text."""

    def process_spell(self, spell_name):
        """Process a single spell using OpenAI API"""
        spell_key = self.normalize_spell_key(spell_name)
        
        # Skip if already processed
        if spell_key in self.repository:
            return True
            
        logger.info(f"Processing spell: {spell_name}")
        
        try:
            # Get spell information from AI
            prompt = self.create_spell_prompt(spell_name)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a 5th edition rules expert. Provide accurate spell information from the SRD 5.2.1 in the requested JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            # Parse the response
            content = response.choices[0].message.content.strip()
            
            # Remove any markdown formatting if present
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
                
            spell_data = json.loads(content)
            
            # Add additional metadata
            spell_data["classes"] = self.extract_spell_classes(spell_name)
            spell_data["_srd_attribution"] = "Portions derived from SRD 5.2.1, CC BY 4.0"
            
            # Validate required fields
            required_fields = ["name", "level", "school", "casting_time", "range", "components", "duration", "description"]
            for field in required_fields:
                if field not in spell_data:
                    raise ValueError(f"Missing required field: {field}")
                    
            # Add to repository
            self.repository[spell_key] = spell_data
            self.spells_processed += 1
            
            # Save after each successful spell
            self.save_repository(backup=False)
            
            self.spells_processed += 1
            logger.debug(f"Successfully processed '{spell_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to process spell '{spell_name}': {e}")
            return False
            
    def process_batch(self, spell_names, delay=1.0):
        """Process a batch of spells with rate limiting"""
        successful = 0
        failed = []
        
        for spell_name in spell_names:
            if self.process_spell(spell_name):
                successful += 1
            else:
                failed.append(spell_name)
                
            # Rate limiting
            if delay > 0:
                time.sleep(delay)
                
        return successful, failed
        
    def build_repository(self, delay=1.0):
        """Build the complete spell repository"""
        # Load spell list
        try:
            with open('spell_list.txt', 'r') as f:
                all_spells = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            logger.error("spell_list.txt not found. Run extract_spells.py first.")
            return False
            
        self.total_spells = len(all_spells)
        
        # Count already processed spells
        processed_count = len([k for k in self.repository.keys() if not k.startswith('_')])
        remaining_spells = [spell for spell in all_spells if self.normalize_spell_key(spell) not in self.repository]
        
        print(f"\n🎯 Spell Repository Builder")
        print(f"Total spells: {self.total_spells}")
        print(f"Already processed: {processed_count}")
        print(f"Remaining to process: {len(remaining_spells)}")
        
        if not remaining_spells:
            print("✅ All spells already processed!")
            return True
            
        # Create backup of existing repository
        if self.repository:
            self.save_repository(backup=True)
            
        # Process each spell individually with progress bar
        failed_spells = []
        
        with tqdm(total=len(remaining_spells), desc="Processing spells", unit="spell") as pbar:
            for i, spell_name in enumerate(remaining_spells):
                pbar.set_postfix(spell=spell_name[:20])
                
                if self.process_spell(spell_name):
                    # Save after each successful spell
                    self.save_repository(backup=False)
                else:
                    failed_spells.append(spell_name)
                
                # Update progress
                pbar.update(1)
                
                # Rate limiting
                if delay > 0:
                    time.sleep(delay)
                
                # Create backup every 20 spells
                if (i + 1) % 20 == 0:
                    self.save_repository(backup=True)
                    
        # Final save
        self.save_repository(backup=True)
        
        # Report results
        total_processed = len([k for k in self.repository.keys() if not k.startswith('_')])
        
        print(f"\n✅ Repository build complete!")
        print(f"Total spells in repository: {total_processed}/{self.total_spells}")
        print(f"Completion rate: {total_processed/self.total_spells*100:.1f}%")
        print(f"Spells processed this session: {len(remaining_spells) - len(failed_spells)}")
        
        if failed_spells:
            print(f"⚠️  Failed to process {len(failed_spells)} spells: {', '.join(failed_spells)}")
        else:
            print("🎉 All spells processed successfully!")
            
        return True
        
    def validate_repository(self):
        """Validate the completed repository"""
        logger.info("Validating spell repository...")
        
        total_spells = len(self.repository)
        valid_spells = 0
        issues = []
        
        for spell_key, spell_data in self.repository.items():
            # Skip metadata entries
            if spell_key.startswith('_'):
                continue
                
            try:
                # Check required fields
                required_fields = ["name", "level", "school", "casting_time", "range", "components", "duration", "description", "classes"]
                for field in required_fields:
                    if field not in spell_data:
                        issues.append(f"{spell_key}: missing field '{field}'")
                        continue
                        
                # Check data types
                if not isinstance(spell_data["level"], int) or spell_data["level"] < 0 or spell_data["level"] > 9:
                    issues.append(f"{spell_key}: invalid level")
                    
                if not isinstance(spell_data["components"], dict):
                    issues.append(f"{spell_key}: components must be a dict")
                    
                if not isinstance(spell_data["classes"], list):
                    issues.append(f"{spell_key}: classes must be a list")
                    
                # Check attribution
                if "_srd_attribution" not in spell_data:
                    issues.append(f"{spell_key}: missing SRD attribution")
                    
                if len(issues) == 0:
                    valid_spells += 1
                    
            except Exception as e:
                issues.append(f"{spell_key}: validation error - {e}")
                
        logger.info(f"Validation complete: {valid_spells}/{total_spells} spells valid")
        
        if issues:
            logger.warning(f"Found {len(issues)} issues:")
            for issue in issues[:10]:  # Show first 10 issues
                logger.warning(f"  - {issue}")
            if len(issues) > 10:
                logger.warning(f"  ... and {len(issues) - 10} more issues")
                
        return len(issues) == 0

def main():
    """Main function to build spell repository"""
    print("5th Edition Spell Repository Builder")
    print("=" * 40)
    
    builder = SpellRepositoryBuilder()
    
    # Check if we should resume or start fresh
    spell_count = len([k for k in builder.repository.keys() if not k.startswith('_')])
    if spell_count > 0:
        print(f"Found existing repository with {spell_count} spells")
        print("Resuming build automatically...")
    else:
        print("Starting fresh build...")
    
    # Build the repository
    start_time = datetime.now()
    success = builder.build_repository(delay=2.0)
    end_time = datetime.now()
    
    if success:
        print(f"\nRepository build completed in {end_time - start_time}")
        
        # Validate the repository
        builder.validate_repository()
        
        print(f"\nSpell repository saved to: {builder.repository_file}")
        print(f"Backup saved to: {builder.backup_file}")
        print(f"Processing log saved to: spell_extraction_log.txt")
        
    else:
        print("Repository build failed. Check the log for details.")

if __name__ == '__main__':
    main()