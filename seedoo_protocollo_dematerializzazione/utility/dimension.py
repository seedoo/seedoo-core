class DimensionUtility:
    def __init__(self):
        pass

    @staticmethod
    def mm_to_in(value=0):
        return value * 0.0393701

    @staticmethod
    def in_to_mm(value=0):
        return value / 0.0393701

    @staticmethod
    def mm_to_pt(value=0):
        return DimensionUtility.mm_to_in(value) * 72

    @staticmethod
    def pt_to_mm(value=0):
        return DimensionUtility.in_to_mm(value / 72)

    @staticmethod
    def xymm_to_pt(value=(0, 0)):
        return (
            DimensionUtility.mm_to_pt(value[0]),
            DimensionUtility.mm_to_pt(value[1]),
        )
