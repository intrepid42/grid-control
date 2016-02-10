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

import random
from grid_control.config import TaggedConfigView
from grid_control.gc_plugin import NamedPlugin
from grid_control.parameters.config_param import ParameterConfig
from grid_control.parameters.padapter import ParameterAdapter
from grid_control.parameters.psource_base import ParameterSource
from grid_control.parameters.psource_data import DataParameterSource
from python_compat import ifilter, imap, irange, lmap

class ParameterFactory(NamedPlugin):
	configSections = NamedPlugin.configSections + ['parameters']
	tagName = 'parameters'

	def __init__(self, config, name):
		NamedPlugin.__init__(self, config, name)
		self.adapter = config.get('parameter adapter', 'TrackedParameterAdapter')
		self.paramConfig = ParameterConfig(config.changeView(setSections = ['parameters']), self.adapter != 'TrackedParameterAdapter')


	def _getRawSource(self, parent):
		return parent


	def getSource(self, config):
		source = self._getRawSource(ParameterSource.getInstance('RNGParameterSource'))
		if DataParameterSource.datasetsAvailable and not DataParameterSource.datasetsUsed:
			source = ParameterSource.getInstance('CrossParameterSource', DataParameterSource.create(), source)
		return ParameterAdapter.getInstance(self.adapter, config, source)


class BasicParameterFactory(ParameterFactory):
	def __init__(self, config, name):
		(self.constSources, self.lookupSources) = ([], [])
		ParameterFactory.__init__(self, config, name)

		# Get constants from [constants <tags...>]
		configConstants = config.changeView(viewClass = TaggedConfigView,
			setClasses = None, setSections = ['constants'], addTags = [self])
		for cName in ifilter(lambda o: not o.endswith(' lookup'), configConstants.getOptions()):
			self._addConstantPSource(configConstants, cName, cName.upper())
		# Get constants from [<Module>] constants
		for cName in imap(str.strip, config.getList('constants', [])):
			self._addConstantPSource(config, cName, cName)
		# Random number variables
		configJobs = config.changeView(addSections = ['jobs'])
		nseeds = configJobs.getInt('nseeds', 10)
		newSeeds = lmap(lambda x: str(random.randint(0, 10000000)), irange(nseeds))
		for (idx, seed) in enumerate(configJobs.getList('seeds', newSeeds, persistent = True)):
			ps = ParameterSource.getInstance('CounterParameterSource', 'SEED_%d' % idx, int(seed))
			self.constSources.append(ps)
		self.repeat = config.getInt('repeat', 1, onChange = None) # ALL config.x -> paramconfig.x !


	def _addConstantPSource(self, config, cName, varName):
		lookupVar = config.get('%s lookup' % cName, '')
		if lookupVar:
			ps = ParameterSource.getInstance('LookupParameterSource', varName, config.getDict(cName, {}), lookupVar)
			self.lookupSources.append(ps)
		else:
			ps = ParameterSource.getInstance('ConstParameterSource', varName, config.get(cName).strip())
			self.constSources.append(ps)


	def _getRawSource(self, parent):
		source_list = self.constSources + [parent, ParameterSource.getInstance('RequirementParameterSource')]
		source = ParameterSource.getInstance('ZipLongParameterSource', *source_list)
		if self.repeat > 1:
			source = ParameterSource.getInstance('RepeatParameterSource', source, self.repeat)
		return ParameterFactory._getRawSource(self, source)
