# -*- coding: utf-8 -*-
# type: ignore

from enum import Enum
from grpc import insecure_channel

try:
    from protos import wallet_pb2_grpc, network_pb2, wallet_pb2, base_node_pb2, types_pb2, block_pb2
except:
    print("You forgot to generate protos, run protos.sh or protos.bat")
    exit()
from time import sleep
from datetime import datetime, timedelta


class Elapsed:
    def __init__(self):
        self.start = datetime.now()

    def elapsed(self):
        return datetime.now() - self.start


class Wallet:
    def __init__(self):
        self.address = "127.0.0.1:18153"
        self.channel = insecure_channel(self.address)
        self.stub = wallet_pb2_grpc.WalletStub(self.channel)
        # Get the public key of this wallet
        request = network_pb2.GetIdentityRequest()
        result = self.stub.Identify(request)
        # The last byte is for igor network
        self.public_key = result.public_key + b"\xfb"

    def coin_split(self, amount_per_split, split_count, fee_per_gram=5, message="", lock_height=0):
        request = wallet_pb2.CoinSplitRequest(
            amount_per_split=amount_per_split, split_count=split_count, fee_per_gram=fee_per_gram, message=message, lock_height=lock_height
        )
        result = self.stub.CoinSplit(request)
        return result

    def send_tari(self, address, amount, fee_per_gram=5, message="", payment_type=wallet_pb2.PaymentRecipient.STANDARD_MIMBLEWIMBLE):
        print(address)
        recipient = wallet_pb2.PaymentRecipient(
            address=address, amount=amount, fee_per_gram=fee_per_gram, message=message, payment_type=payment_type
        )
        request = wallet_pb2.TransferRequest(recipients=[recipient])
        result = self.stub.Transfer(request)
        return result

    def send_to_self(self, amount, fee_per_gram=5, message=""):
        return self.send_tari(self.public_key.hex(), amount, fee_per_gram, message)

    def big_coin_split(self, amount_per_split, split_count):
        max_outputs_per_tx = 499  # it's 500, but we reserve one for the change output
        while split_count > 0:
            self.coin_split(amount_per_split, min(split_count, max_outputs_per_tx))
            split_count -= min(split_count, max_outputs_per_tx)

    def make_it_rain(
        self, address, amount, transactions_per_second, duration, increase_amount=0, one_sided=False, stealth=False, message=""
    ):
        time = Elapsed()
        transactions_count = duration * transactions_per_second
        time_per_transaction = timedelta(seconds=1 / transactions_per_second)
        target_time = timedelta()
        for i in range(transactions_count):
            if time.elapsed() < target_time:
                sleep((target_time - time.elapsed()).microseconds / 1000000)
            target_time += time_per_transaction
            print(i, time.elapsed())
            self.send_tari(
                address,
                amount,
                message=message,
                payment_type=one_sided
                and (stealth and wallet_pb2.PaymentRecipient.ONE_SIDED_TO_STEALTH_ADDRESS or wallet_pb2.PaymentRecipient.ONE_SIDED)
                or wallet_pb2.PaymentRecipient.STANDARD_MIMBLEWIMBLE,
            )
            amount += increase_amount

    def get_balance(self):
        request = wallet_pb2.GetBalanceRequest()
        return self.stub.GetBalance(request)


wallet = Wallet()
# wallet.big_coin_split(10000, 5000)
# wallet.make_it_rain(wallet.public_key.hex(), 100, 3, 10, 1)
