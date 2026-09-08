"""
Blockchain Connector Module for AgricLedger
Handles all blockchain interactions using Web3.py
"""

import os
import json
from typing import Dict, Any, Optional, List
from web3 import Web3
from web3.middleware import geth_poa_middleware
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BlockchainConnector:
    """
    Main connector class for blockchain interactions
    Handles connections to Ganache and smart contract operations
    """
    
    def __init__(self, network: str = 'development'):
        """
        Initialize blockchain connector
        
        Args:
            network: Network to connect to ('development' or 'local')
        """
        self.network = network
        self.w3 = None
        self.data_sovereignty = None
        self.land_tenure = None
        self.default_account = None
        self.is_connected = False
        
        # Contract addresses from .env
        self.data_sovereignty_address = os.getenv('DATA_SOVEREIGNTY_ADDRESS')
        self.land_tenure_address = os.getenv('LAND_TENURE_ADDRESS')
        self.private_key = os.getenv('WALLET_PRIVATE_KEY')
        
        # Load contract ABIs
        self.data_sovereignty_abi = None
        self.land_tenure_abi = None
        
        self.connect()
    
    def connect(self) -> bool:
        """
        Connect to the blockchain network
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Try multiple connection options
            connection_urls = [
                'http://127.0.0.1:7545',  # Ganache default
                'http://127.0.0.1:8545',  # Hardhat / local
                os.getenv('GANACHE_URL', 'http://127.0.0.1:7545')
            ]
            
            # Try each URL
            for url in connection_urls:
                try:
                    self.w3 = Web3(Web3.HTTPProvider(url))
                    # Add POA middleware for Ganache
                    try:
                        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
                    except Exception:
                        pass  # Middleware might already be injected
                    
                    if self.w3.is_connected():
                        logger.info(f"✅ Connected to blockchain at {url}")
                        self.is_connected = True
                        break
                except Exception as e:
                    logger.debug(f"Connection attempt to {url} failed: {e}")
                    continue
            
            if not self.is_connected:
                logger.warning("⚠️ Could not connect to blockchain. Running in offline mode.")
                self.w3 = None
                return False
            
            # Set default account (first account from Ganache)
            try:
                self.default_account = self.w3.eth.accounts[0]
                logger.info(f"📊 Default account: {self.default_account}")
                logger.info(f"📊 Block number: {self.w3.eth.block_number}")
            except Exception as e:
                logger.warning(f"Could not get accounts: {e}")
                self.default_account = None
            
            # Load contracts
            self.load_contracts()
            
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to blockchain: {str(e)}")
            self.is_connected = False
            self.w3 = None
            return False
    
    def load_contracts(self) -> None:
        """Load smart contract ABIs and create contract instances"""
        if not self.is_connected or not self.w3:
            logger.warning("⚠️ Cannot load contracts - blockchain not connected")
            return
            
        try:
            # Try to load DataSovereignty ABI from multiple locations
            contract_paths = [
                'blockchain/build/contracts/DataSovereignty.json',
                'build/contracts/DataSovereignty.json',
                '../blockchain/build/contracts/DataSovereignty.json'
            ]
            
            for path in contract_paths:
                try:
                    with open(path, 'r') as f:
                        contract_json = json.load(f)
                        self.data_sovereignty_abi = contract_json['abi']
                        
                        if self.data_sovereignty_address:
                            self.data_sovereignty = self.w3.eth.contract(
                                address=self.data_sovereignty_address,
                                abi=self.data_sovereignty_abi
                            )
                            logger.info("✅ DataSovereignty contract loaded")
                        break
                except FileNotFoundError:
                    continue
                except Exception as e:
                    logger.debug(f"Error loading from {path}: {e}")
                    continue
            
            # Try to load LandTenure ABI
            for path in contract_paths:
                try:
                    with open(path.replace('DataSovereignty', 'LandTenure'), 'r') as f:
                        contract_json = json.load(f)
                        self.land_tenure_abi = contract_json['abi']
                        
                        if self.land_tenure_address:
                            self.land_tenure = self.w3.eth.contract(
                                address=self.land_tenure_address,
                                abi=self.land_tenure_abi
                            )
                            logger.info("✅ LandTenure contract loaded")
                        break
                except FileNotFoundError:
                    continue
                except Exception as e:
                    logger.debug(f"Error loading LandTenure: {e}")
                    continue
                    
            if not self.data_sovereignty_abi and not self.land_tenure_abi:
                logger.warning("⚠️ No contract ABIs found. Blockchain features may be limited.")
                    
        except Exception as e:
            logger.error(f"Error loading contracts: {str(e)}")
    
    # ========== WRAPPER FUNCTIONS WITH ERROR HANDLING ==========
    
    def register_farmer(self, farmer_id: str, name: str, location: str) -> Dict[str, Any]:
        """Register a farmer on the blockchain"""
        if not self.is_connected or not self.data_sovereignty:
            return {'success': False, 'error': 'Blockchain not connected or contract not loaded'}
        
        try:
            # Build transaction
            tx = self.data_sovereignty.functions.registerFarmer(
                farmer_id,
                name,
                location
            ).build_transaction({
                'from': self.default_account,
                'gas': 300000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.default_account)
            })
            
            # Sign and send transaction
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            return {
                'success': True,
                'transaction_hash': tx_hash.hex(),
                'receipt': receipt
            }
            
        except Exception as e:
            logger.error(f"Error registering farmer: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def grant_data_access(self, organization_address: str, data_type: str, purpose: str) -> Dict[str, Any]:
        """Grant data access permission to an organization"""
        if not self.is_connected or not self.data_sovereignty:
            return {'success': False, 'error': 'Blockchain not connected or contract not loaded'}
        
        try:
            tx = self.data_sovereignty.functions.grantAccess(
                organization_address,
                data_type,
                purpose
            ).build_transaction({
                'from': self.default_account,
                'gas': 300000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.default_account)
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            return {
                'success': True,
                'transaction_hash': tx_hash.hex(),
                'receipt': receipt
            }
            
        except Exception as e:
            logger.error(f"Error granting access: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def revoke_data_access(self, organization_address: str) -> Dict[str, Any]:
        """Revoke data access permission from an organization"""
        if not self.is_connected or not self.data_sovereignty:
            return {'success': False, 'error': 'Blockchain not connected or contract not loaded'}
        
        try:
            tx = self.data_sovereignty.functions.revokeAccess(
                organization_address
            ).build_transaction({
                'from': self.default_account,
                'gas': 300000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.default_account)
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            return {
                'success': True,
                'transaction_hash': tx_hash.hex(),
                'receipt': receipt
            }
            
        except Exception as e:
            logger.error(f"Error revoking access: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def register_land(
        self,
        land_id: str,
        location: str,
        document_type: str,
        document_hash: str,
        plot_number: str,
        district: str,
        province: str,
        size_hectares: float
    ) -> Dict[str, Any]:
        """Register a land tenure record"""
        if not self.is_connected or not self.land_tenure:
            return {'success': False, 'error': 'Blockchain not connected or contract not loaded'}
        
        try:
            tx = self.land_tenure.functions.registerLand(
                land_id,
                location,
                document_type,
                document_hash,
                plot_number,
                district,
                province,
                size_hectares
            ).build_transaction({
                'from': self.default_account,
                'gas': 500000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.default_account)
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            return {
                'success': True,
                'transaction_hash': tx_hash.hex(),
                'receipt': receipt
            }
            
        except Exception as e:
            logger.error(f"Error registering land: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_land_record(self, land_id: str) -> Dict[str, Any]:
        """Get land record from blockchain"""
        if not self.is_connected or not self.land_tenure:
            return {'success': False, 'error': 'Blockchain not connected or contract not loaded'}
        
        try:
            land_record = self.land_tenure.functions.getLandRecord(land_id).call()
            
            return {
                'success': True,
                'land_record': {
                    'landId': land_record[0],
                    'owner': land_record[1],
                    'location': land_record[2],
                    'documentType': land_record[3],
                    'documentHash': land_record[4],
                    'registrationDate': land_record[5],
                    'lastUpdated': land_record[6],
                    'isVerified': land_record[7],
                    'plotNumber': land_record[8],
                    'district': land_record[9],
                    'province': land_record[10],
                    'sizeInHectares': land_record[11]
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting land record: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_access_history(self, farmer_address: str) -> Dict[str, Any]:
        """Get access history for a farmer"""
        if not self.is_connected or not self.data_sovereignty:
            return {'success': False, 'error': 'Blockchain not connected or contract not loaded'}
        
        try:
            history = self.data_sovereignty.functions.getAccessHistory(farmer_address).call()
            
            records = []
            for record in history:
                records.append({
                    'farmerAddress': record[0],
                    'organizationAddress': record[1],
                    'timestamp': record[2],
                    'dataType': record[3],
                    'isActive': record[4],
                    'purpose': record[5]
                })
            
            return {
                'success': True,
                'records': records
            }
            
        except Exception as e:
            logger.error(f"Error getting access history: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def check_access(self, farmer_address: str, organization_address: str) -> Dict[str, Any]:
        """Check if an organization has access to a farmer's data"""
        if not self.is_connected or not self.data_sovereignty:
            return {'success': False, 'error': 'Blockchain not connected or contract not loaded'}
        
        try:
            has_access = self.data_sovereignty.functions.hasAccess(
                farmer_address,
                organization_address
            ).call()
            
            return {
                'success': True,
                'has_access': has_access
            }
            
        except Exception as e:
            logger.error(f"Error checking access: {str(e)}")
            return {'success': False, 'error': str(e)}