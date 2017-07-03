class EanUtility:
    def __init__(self):
        pass

    @staticmethod
    def ean_verify(ean_text):
        is_valid = False
        try:
            ean_numbers = [int(i) for i in ean_text]
            if len(ean_numbers) == 13:
                ean_code = ean_numbers[:12]
                ean_checksum = ean_numbers[12]
                sum_ = lambda x, y: int(x) + int(y)
                evensum = reduce(sum_, ean_code[::2])
                oddsum = reduce(sum_, ean_code[1::2])
                checksum = (10 - ((evensum + oddsum * 3) % 10)) % 10
                if ean_checksum == checksum:
                    is_valid = True
        except Exception as exception:
                is_valid = False
        finally:
            return is_valid

    @staticmethod
    def ean_get_protocollo(ean_text):
        is_valid = True
        protocollo_anno = 0
        protocollo_numero = 0
        try:
            if len(ean_text) == 13:
                protocollo_anno = ean_text[:4]
                protocollo_numero = ean_text[5:12]
            else:
                is_valid = False
        except Exception as exception:
            is_valid = False
        finally:
            return is_valid, protocollo_anno, protocollo_numero





