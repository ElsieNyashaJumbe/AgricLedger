"""
Deployment script for AgricLedger blockchain contracts
"""

import os
import json
import subprocess
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def compile_contracts():
    """Compile Solidity contracts using Truffle"""
    print("🔨 Compiling contracts...")
    try:
        # Change to blockchain directory
        os.chdir('blockchain')
        
        # Run truffle compile
        result = subprocess.run(
            ['npx', 'truffle', 'compile'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Contracts compiled successfully")
            return True
        else:
            print(f"❌ Compilation failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error compiling contracts: {str(e)}")
        return False

def deploy_contracts():
    """Deploy contracts using Truffle"""
    print("🚀 Deploying contracts...")
    try:
        # Run truffle migrate
        result = subprocess.run(
            ['npx', 'truffle', 'migrate', '--network', 'development'],
            capture_output=True,
            text=True,
            cwd='blockchain'
        )
        
        if result.returncode == 0:
            print("✅ Contracts deployed successfully")
            
            # Get contract addresses from build files
            with open('blockchain/build/contracts/DataSovereignty.json', 'r') as f:
                data_sovereignty = json.load(f)
                ds_address = data_sovereignty['networks']['5777']['address']
                print(f"📋 DataSovereignty address: {ds_address}")
            
            with open('blockchain/build/contracts/LandTenure.json', 'r') as f:
                land_tenure = json.load(f)
                lt_address = land_tenure['networks']['5777']['address']
                print(f"📋 LandTenure address: {lt_address}")
            
            # Update .env file
            update_env(ds_address, lt_address)
            
            return True
        else:
            print(f"❌ Deployment failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error deploying contracts: {str(e)}")
        return False

def update_env(ds_address, lt_address):
    """Update .env file with contract addresses"""
    env_file = '.env'
    
    # Read existing env file
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            lines = f.readlines()
    else:
        lines = []
    
    # Update or add contract addresses
    updated = False
    for i, line in enumerate(lines):
        if line.startswith('DATA_SOVEREIGNTY_ADDRESS='):
            lines[i] = f'DATA_SOVEREIGNTY_ADDRESS={ds_address}\n'
            updated = True
        elif line.startswith('LAND_TENURE_ADDRESS='):
            lines[i] = f'LAND_TENURE_ADDRESS={lt_address}\n'
            updated = True
    
    if not updated:
        lines.append(f'DATA_SOVEREIGNTY_ADDRESS={ds_address}\n')
        lines.append(f'LAND_TENURE_ADDRESS={lt_address}\n')
    
    # Write back
    with open(env_file, 'w') as f:
        f.writelines(lines)
    
    print("✅ .env file updated with contract addresses")

if __name__ == "__main__":
    print("🌾 AgricLedger Blockchain Deployment")
    print("=" * 40)
    
    # Step 1: Compile contracts
    if not compile_contracts():
        sys.exit(1)
    
    # Step 2: Deploy contracts
    if not deploy_contracts():
        sys.exit(1)
    
    print("=" * 40)
    print("🎉 Blockchain module setup complete!")