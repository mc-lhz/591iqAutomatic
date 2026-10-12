import sys, json
sys.path.insert(0,"tools")
from IqClient import IQClient
c=IQClient("f47b1264c34a4164b40964548ddc80ce"); c.login()
L=c.activityLabels(5)
for x in L:
    print(x["labelId"], "|", x["labelName"], "|", x["dimensionName"])
