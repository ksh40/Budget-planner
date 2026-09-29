import json
import os
from web3 import Web3
from solcx import compile_source, install_solc
from django.conf import settings

install_solc('0.8.0')

def get_web3():
    w3 = Web3(Web3.HTTPProvider(
        f'https://sepolia.infura.io/v3/{settings.INFURA_API_KEY}'
    ))
    return w3


def compile_contract():
    contract_path = os.path.join(os.path.dirname(__file__), 'contract.sol')
    with open(contract_path, 'r') as f:
        source = f.read()
    compiled = compile_source(source, solc_version='0.8.0')
    contract_interface = compiled['<stdin>:PermitRegistry']
    return contract_interface


def deploy_contract():
    w3 = get_web3()
    contract_interface = compile_contract()
    
    contract = w3.eth.contract(
        abi=contract_interface['abi'],
        bytecode=contract_interface['bin']
    )
    
    account = w3.eth.account.from_key(settings.WALLET_PRIVATE_KEY)
    
    transaction = contract.constructor().build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 2000000,
        'gasPrice': w3.eth.gas_price,
    })
    
    signed = account.sign_transaction(transaction)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    contract_address = receipt.contractAddress
    
    # Save contract address and ABI to file
    deployment = {
        'address': contract_address,
        'abi': contract_interface['abi']
    }
    deployment_path = os.path.join(os.path.dirname(__file__), 'deployment.json')
    with open(deployment_path, 'w') as f:
        json.dump(deployment, f)
    
    print(f'Contract deployed at: {contract_address}')
    return contract_address


def get_contract():
    w3 = get_web3()
    deployment_path = os.path.join(os.path.dirname(__file__), 'deployment.json')
    with open(deployment_path, 'r') as f:
        deployment = json.load(f)
    
    contract = w3.eth.contract(
        address=deployment['address'],
        abi=deployment['abi']
    )
    return w3, contract


def register_permit(permit_number, issuing_authority):
    w3, contract = get_contract()
    account = w3.eth.account.from_key(settings.WALLET_PRIVATE_KEY)
    
    transaction = contract.functions.registerPermit(
        permit_number,
        issuing_authority
    ).build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 200000,
        'gasPrice': w3.eth.gas_price,
    })
    
    signed = account.sign_transaction(transaction)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    return {
        'tx_hash': receipt.transactionHash.hex(),
        'block_number': receipt.blockNumber,
        'status': 'registered'
    }


def verify_permit(permit_number, issuing_authority):
    w3, contract = get_contract()
    account = w3.eth.account.from_key(settings.WALLET_PRIVATE_KEY)

    # First check the result using call() — no gas needed, instant
    is_valid = contract.functions.verifyPermit(
        permit_number,
        issuing_authority
    ).call({'from': account.address})

    # Then record the verification on the blockchain as a transaction
    transaction = contract.functions.verifyPermit(
        permit_number,
        issuing_authority
    ).build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 200000,
        'gasPrice': w3.eth.gas_price,
    })

    signed = account.sign_transaction(transaction)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    return {
        'is_valid': is_valid,
        'tx_hash': receipt.transactionHash.hex(),
        'block_number': receipt.blockNumber,
    }