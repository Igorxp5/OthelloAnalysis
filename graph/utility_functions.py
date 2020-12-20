import numpy as np

class UtilityFunction:

    def __init__(self):
        self.a = 0

    def utilityFunction(self, val):
        if self.a == 0:
            return val
        else:
            return (1-np.exp(-(self.a/10) * val))/ (self.a/10)
    
    def normalize(self, val):
        return val
    
    def bestLottery(self, loterries):
        lotUtilityValues = []
        for i, lot in enumerate(loterries):
            lotValues, lotProbs = zip(*lot)
            lotValues = np.array(lotValues)
            lotProbs = np.array(lotProbs)
            
            lotUtility = self.utilityFunction(self.normalize(lotValues))
            finalValue = np.sum((lotUtility * lotProbs))
            lotUtilityValues.append( (i, finalValue) )
        return max(lotUtilityValues, key=lambda k : k[1])