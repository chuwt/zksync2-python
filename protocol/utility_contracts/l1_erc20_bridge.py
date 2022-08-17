import importlib.resources as pkg_resources
from eth_account.signers.base import BaseAccount
from web3 import Web3
from web3.contract import Contract
from eth_typing import HexStr
from typing import List
import json

from protocol.utility_contracts.gas_provider import GasProvider
from .. import contract_abi

l1_erc20_bridge_abi_cache = None


def _l1_erc20_bridge_abi_default():
    global l1_erc20_bridge_abi_cache

    if l1_erc20_bridge_abi_cache is None:
        with pkg_resources.path(contract_abi, "L1ERC20Bridge.json") as p:
            with p.open(mode='r') as json_file:
                data = json.load(json_file)
                l1_erc20_bridge_abi_cache = data['abi']
    return l1_erc20_bridge_abi_cache


class L1ERC20Bridge:
    DEFAULT_GAS_LIMIT = 21000

    def __init__(self,
                 contract_address: HexStr,
                 web3: Web3,
                 eth_account: BaseAccount,
                 gas_provider: GasProvider, abi=None):
        check_sum_address = Web3.toChecksumAddress(contract_address)
        self.web3 = web3
        self.addr = check_sum_address
        self.account = eth_account
        self.gas_provider = gas_provider
        if abi is None:
            abi = _l1_erc20_bridge_abi_default()
        self.contract: Contract = self.web3.eth.contract(self.addr, abi=abi)

    def _get_nonce(self):
        return self.web3.eth.get_transaction_count(self.account.address)

    def claim_failed_deposit(self, deposit_sender: HexStr,
                             l1_token: HexStr,
                             tx_hash,
                             l2_block_number: int,
                             l2_msg_index: int,
                             merkle_proof: List[bytes]):
        tx = self.contract.functions.claimFailedDeposit(deposit_sender,
                                                        l1_token,
                                                        tx_hash,
                                                        l2_block_number,
                                                        l2_msg_index,
                                                        merkle_proof).build_transaction(
            {
                "chainId": self.web3.eth.chain_id,
                "from": self.account.address,
                "nonce": self._get_nonce(),
                "gas": self.gas_provider.gas_limit(),
                "gasPrice": self.gas_provider.gas_price()
            })
        signed_tx = self.account.sign_transaction(tx)
        txn_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        txn_receipt = self.web3.eth.wait_for_transaction_receipt(txn_hash)
        return txn_receipt

    def deposit(self, l2_receiver: HexStr, l1_token: HexStr, amount: int, queue_type: int):
        tx = self.contract.functions.deposit(l2_receiver,
                                             l1_token,
                                             amount,
                                             queue_type).build_transaction(
            {
                "chainId": self.web3.eth.chain_id,
                "from": self.account.address,
                "nonce": self._get_nonce(),
                "gas": self.gas_provider.gas_limit(),
                "gasPrice": self.gas_provider.gas_price()
            })
        signed_tx = self.account.sign_transaction(tx)
        txn_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        txn_receipt = self.web3.eth.wait_for_transaction_receipt(txn_hash)
        return txn_receipt

    def finalize_withdrawal(self,
                            l2_block_number: int,
                            l2_msg_index: int,
                            msg: bytes,
                            merkle_proof: List[bytes]):
        tx = self.contract.functions.finalizeWithdrawal(l2_block_number,
                                                        l2_msg_index,
                                                        msg,
                                                        merkle_proof).build_transaction(
            {
                "chainId": self.web3.eth.chain_id,
                "from": self.account.address,
                "nonce": self._get_nonce(),
                "gas": self.gas_provider.gas_limit(),
                "gasPrice": self.gas_provider.gas_price()
            })
        signed_tx = self.account.sign_transaction(tx)
        txn_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        txn_receipt = self.web3.eth.wait_for_transaction_receipt(txn_hash)
        return txn_receipt

    def initialize(self,
                   factory_deps: List[bytes],
                   l2_token_factory: HexStr):
        tx = self.contract.functions.initialize(factory_deps,
                                                l2_token_factory).build_transaction(
            {
                "chainId": self.web3.eth.chain_id,
                "from": self.account.address,
                "nonce": self._get_nonce(),
                "gas": self.gas_provider.gas_limit(),
                "gasPrice": self.gas_provider.gas_price()
            })
        signed_tx = self.account.sign_transaction(tx)
        txn_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        txn_receipt = self.web3.eth.wait_for_transaction_receipt(txn_hash)
        return txn_receipt

    def is_withdraw_finalized(self, a: int, b: int) -> bool:
        return self.contract.functions.isWithdrawalFinalized(a, b).call()

    def l2_bridge(self):
        return self.contract.functions.l2Bridge().call()

    def l2_proxy_token_byte_code_hash(self):
        return self.contract.functions.l2ProxyTokenBytecodeHash().call()

    def l2_token_address(self, l1_token: HexStr):
        return self.contract.functions.l2TokenAddress(l1_token).call()

    def l2_token_factory(self) -> HexStr:
        return self.contract.functions.l2TokenFactory().call()

    @property
    def address(self):
        return self.addr
