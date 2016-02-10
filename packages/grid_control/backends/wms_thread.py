#-#  Copyright 2012-2016 Karlsruhe Institute of Technology
#-#
#-#  Licensed under the Apache License, Version 2.0 (the "License");
#-#  you may not use this file except in compliance with the License.
#-#  You may obtain a copy of the License at
#-#
#-#      http://www.apache.org/licenses/LICENSE-2.0
#-#
#-#  Unless required by applicable law or agreed to in writing, software
#-#  distributed under the License is distributed on an "AS IS" BASIS,
#-#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#-#  See the License for the specific language governing permissions and
#-#  limitations under the License.

from grid_control import utils
from grid_control.backends.wms_multi import MultiWMS
from python_compat import ifilter, imap

class ThreadedMultiWMS(MultiWMS):
	def _forwardCall(self, args, assignFun, callFun):
		argMap = self._getMapID2Backend(args, assignFun)
		makeGenerator = lambda wmsPrefix: (wmsPrefix, callFun(self._wmsMap[wmsPrefix], argMap[wmsPrefix]))
		activeWMS = ifilter(lambda wmsPrefix: wmsPrefix in argMap, self._wmsMap)
		for result in utils.getThreadedGenerator(imap(makeGenerator, activeWMS)):
			yield result
